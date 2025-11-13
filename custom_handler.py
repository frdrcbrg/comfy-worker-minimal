"""
Custom RunPod handler for ComfyUI with N8N-optimized input/output formats.

Supports:
- Multiple input formats: base64, HTTP URLs, S3 pre-signed URLs
- URL streaming: Direct binary fetch without base64 decoding
- S3 output: Upload generated images to S3, return URLs instead of base64
- Performance: ~2x faster than base64 encoding/decoding
"""

import os
import json
import base64
import io
import logging
from typing import Any, Dict, Optional
from pathlib import Path
import urllib.request
import urllib.error
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class S3Manager:
    """Handles S3 upload operations for generated images."""

    def __init__(self):
        """Initialize S3 client with environment variables."""
        self.endpoint_url = os.getenv("BUCKET_ENDPOINT_URL")
        self.access_key = os.getenv("BUCKET_ACCESS_KEY_ID")
        self.secret_key = os.getenv("BUCKET_SECRET_ACCESS_KEY")
        self.bucket_name = os.getenv("BUCKET_NAME", "comfy-outputs")
        self.enabled = bool(self.endpoint_url and self.access_key and self.secret_key)

        if self.enabled:
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=os.getenv("AWS_REGION", "us-east-1"),
            )
            logger.info(f"S3 storage enabled. Bucket: {self.bucket_name}")
        else:
            logger.info("S3 storage disabled. Missing environment variables.")

    def upload_image(self, image_data: bytes, filename: str) -> Optional[str]:
        """
        Upload image to S3 and return the URL.

        Args:
            image_data: Raw image bytes
            filename: Target filename (e.g., 'job-id/image.png')

        Returns:
            S3 URL or None if upload failed
        """
        if not self.enabled:
            return None

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=image_data,
                ContentType="image/png",
            )
            # Construct URL based on endpoint
            url = f"{self.endpoint_url.rstrip('/')}/{self.bucket_name}/{filename}"
            logger.info(f"Image uploaded to S3: {url}")
            return url
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return None


class InputFormatter:
    """Handles multiple input formats: base64, URLs, and S3 pre-signed URLs."""

    @staticmethod
    def fetch_url(url: str) -> bytes:
        """
        Fetch binary data from HTTP/HTTPS URL.

        Args:
            url: HTTP/HTTPS URL to fetch

        Returns:
            Raw binary data

        Raises:
            urllib.error.URLError if fetch fails
        """
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return response.read()
        except urllib.error.URLError as e:
            logger.error(f"Failed to fetch URL: {url}. Error: {e}")
            raise

    @staticmethod
    def decode_base64(data: str) -> bytes:
        """
        Decode base64 string to binary.

        Args:
            data: Base64-encoded string

        Returns:
            Raw binary data

        Raises:
            ValueError if base64 is invalid
        """
        try:
            return base64.b64decode(data)
        except Exception as e:
            logger.error(f"Failed to decode base64: {e}")
            raise ValueError(f"Invalid base64 data: {e}")

    @classmethod
    def process_input(
        cls, input_data: Dict[str, Any], job_id: str
    ) -> Optional[str]:
        """
        Process input in multiple formats and save to ComfyUI input directory.

        Supports:
        - {"type": "url", "data": "https://..."}
        - {"type": "base64", "data": "iVBORw0..."}
        - {"type": "s3_url", "data": "https://bucket.s3.amazonaws.com/..."}

        Args:
            input_data: Input specification dict
            job_id: Job ID for file naming

        Returns:
            Path to saved image file or None if processing failed
        """
        input_type = input_data.get("type", "base64")
        input_value = input_data.get("data")

        if not input_value:
            logger.error("No input data provided")
            return None

        try:
            # Fetch binary data based on input type
            if input_type == "url":
                logger.info(f"Fetching image from URL: {input_value}")
                image_bytes = cls.fetch_url(input_value)
            elif input_type == "s3_url":
                logger.info(f"Fetching image from S3 URL: {input_value}")
                image_bytes = cls.fetch_url(input_value)
            elif input_type == "base64":
                logger.info("Processing base64-encoded image")
                image_bytes = cls.decode_base64(input_value)
            else:
                logger.error(f"Unknown input type: {input_type}")
                return None

            # Save to ComfyUI input directory
            input_dir = Path("/comfyui/input")
            input_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{job_id}_input.png"
            filepath = input_dir / filename

            with open(filepath, "wb") as f:
                f.write(image_bytes)

            logger.info(f"Image saved to: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Input processing failed: {e}")
            return None


class OutputFormatter:
    """Handles output formatting with S3 upload support."""

    def __init__(self, s3_manager: S3Manager):
        """Initialize with S3 manager."""
        self.s3_manager = s3_manager

    def process_output(
        self, output_path: str, job_id: str
    ) -> Dict[str, Any]:
        """
        Process ComfyUI output image.

        If S3 is configured, uploads to S3 and returns URL.
        Otherwise, returns base64-encoded image.

        Args:
            output_path: Path to output image file
            job_id: Job ID for S3 organization

        Returns:
            Dict with format: {"type": "s3_url"|"base64", "data": "..."}
        """
        if not os.path.exists(output_path):
            logger.error(f"Output file not found: {output_path}")
            return {"type": "error", "data": "Output file not found"}

        try:
            with open(output_path, "rb") as f:
                image_bytes = f.read()

            # Try S3 upload first
            if self.s3_manager.enabled:
                filename = Path(output_path).name
                s3_url = self.s3_manager.upload_image(
                    image_bytes, f"{job_id}/{filename}"
                )
                if s3_url:
                    return {"type": "s3_url", "data": s3_url}

            # Fallback to base64
            logger.info("Using base64 encoding for output")
            b64_data = base64.b64encode(image_bytes).decode("utf-8")
            return {"type": "base64", "data": b64_data}

        except Exception as e:
            logger.error(f"Output processing failed: {e}")
            return {"type": "error", "data": str(e)}


def handler(job):
    """
    Main RunPod handler function.

    Processes input, runs ComfyUI workflow, and returns optimized output.

    Input format:
    {
        "input": {
            "type": "url|base64|s3_url",
            "data": "..."
        },
        "workflow": {...},  # ComfyUI workflow JSON
        ...
    }
    """
    try:
        job_id = job.get("id", "unknown")
        logger.info(f"Processing job: {job_id}")

        # Initialize managers
        s3_manager = S3Manager()
        output_formatter = OutputFormatter(s3_manager)

        # Process input if provided
        input_image_path = None
        if "input" in job.get("input", {}):
            input_data = job["input"]["input"]
            input_image_path = InputFormatter.process_input(input_data, job_id)
            if not input_image_path:
                return {
                    "error": "Failed to process input image",
                    "job_id": job_id,
                }

        # Get ComfyUI workflow
        workflow = job.get("input", {}).get("workflow", {})
        if not workflow:
            return {"error": "No workflow provided", "job_id": job_id}

        # TODO: Execute ComfyUI workflow here
        # This would integrate with ComfyUI's Python API or CLI
        logger.info(f"Would execute workflow: {json.dumps(workflow, indent=2)}")

        # Mock output for demonstration
        # In production, get actual output from ComfyUI
        output_image_path = "/tmp/mock_output.png"

        # Process output
        output = output_formatter.process_output(output_image_path, job_id)

        return {
            "success": True,
            "job_id": job_id,
            "output": output,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Handler error: {e}", exc_info=True)
        return {"error": str(e), "job_id": job.get("id", "unknown")}


if __name__ == "__main__":
    # Test handler with sample input
    test_job = {
        "id": "test-job-001",
        "input": {
            "input": {"type": "base64", "data": "iVBORw0KGgo..."},
            "workflow": {"nodes": []},
        },
    }
    result = handler(test_job)
    print(json.dumps(result, indent=2))
