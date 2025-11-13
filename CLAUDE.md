# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a minimal Docker-based template for creating custom ComfyUI workers that run on RunPod or any containerized GPU environment. The project intentionally contains minimal files and is designed to be extended with custom nodes, models, and configurations.

## Architecture

**Base Image**: The Dockerfile extends `runpod/worker-comfyui:5.4.1-base-cuda12.8.1`, which provides:
- A clean ComfyUI installation (no pre-packaged models)
- CUDA 12.8.1 for RTX 5090 (Blackwell) and latest GPU support
- The `comfy-cli` tooling (including `comfy-node-install` and `comfy model download`)
- Python runtime with GPU support
- RunPod worker SDK integration

**Customization Pattern**: All customizations are made by modifying the Dockerfile:
1. **Custom Nodes**: Installed using `comfy-node-install` command with node names or URLs
2. **Models**: Downloaded using `comfy model download` with `--url`, `--relative-path`, and `--filename` parameters
3. **Static Files**: Copied into the container using `COPY input/ /comfyui/input/`

## Common Commands

### Building and Testing Locally
```bash
# Build the image
docker build -t comfy-worker-minimal .

# Run locally (requires GPU)
docker run --gpus all -p 8188:8188 comfy-worker-minimal
```

### Using Pre-built Images
```bash
# Pull specific version (recommended for production)
docker pull ghcr.io/frdrcbrg/comfy-worker-minimal:1.1.0

# Pull flexible versions
docker pull ghcr.io/frdrcbrg/comfy-worker-minimal:1.1  # Latest patch
docker pull ghcr.io/frdrcbrg/comfy-worker-minimal:1    # Latest minor

# Pull latest development
docker pull ghcr.io/frdrcbrg/comfy-worker-minimal:main
```

### Release Management
```bash
# Create a new release using GitHub CLI (recommended)
gh release create v1.2.0 --title "v1.2.0 - Feature Description" --notes "Release notes here"

# Or create manually with git tags
git tag -a v1.2.0 -m "Release v1.2.0: Description"
git push origin v1.2.0
```

## CI/CD Workflow

**GitHub Actions** (`.github/workflows/docker-build.yml`):
- **Triggers**: Push to `main`, version tags (`v*`), pull requests
- **Outputs**: Multi-tagged Docker images published to `ghcr.io/frdrcbrg/comfy-worker-minimal`
- **Tag Strategy**:
  - Git tag `v1.2.3` → Creates Docker tags: `1.2.3`, `1.2`, `1`, `sha-abc123`
  - Push to `main` → Creates Docker tag: `main`
  - Note: The `v` prefix is stripped from semantic version tags
- **Optimizations**: Uses GitHub Actions cache for Docker layer caching

## Versioning Strategy

This project uses **Semantic Versioning** (SemVer):
- **MAJOR** (v2.0.0): Breaking changes (e.g., upgrade base image to new major version)
- **MINOR** (v1.1.0): New features, backward compatible (e.g., add pre-installed custom nodes)
- **PATCH** (v1.0.1): Bug fixes and documentation updates

## Key Conventions

**Model Paths**: When downloading models in Dockerfile, use correct `--relative-path` values:
- `models/checkpoints` - Checkpoint models
- `models/loras` - LoRA models
- `models/vae` - VAE models
- `models/clip` - CLIP models
- `models/controlnet` - ControlNet models

**Custom Node Installation**: Use `comfy-node-install` (not standard `comfy-cli`) for better error reporting. Find node names at [Comfy Registry](https://registry.comfy.org/).

**Base Image Variants**:
- `-base-cuda12.8.1` suffix: Clean install with CUDA 12.8.1 (current choice, supports RTX 5090)
- `-base` suffix: Clean install without models
- `-sdxl` suffix: Includes SDXL models pre-packaged
- Update base image version from [runpod/worker-comfyui releases](https://github.com/runpod-workers/worker-comfyui/releases) or [Docker Hub tags](https://hub.docker.com/r/runpod/worker-comfyui/tags)

## Storage Configuration

**S3 Storage for Output Images**: Configure S3 to automatically upload generated images instead of returning base64-encoded strings. Set these environment variables in your RunPod template:
```bash
BUCKET_ENDPOINT_URL=https://your-bucket-name.s3.us-east-1.amazonaws.com
BUCKET_ACCESS_KEY_ID=AKIA...
BUCKET_SECRET_ACCESS_KEY=your-secret-key
```

This changes output format from `{"type": "base64", "data": "..."}` to `{"type": "s3_url", "data": "https://..."}`.

Works with S3-compatible providers: AWS S3, Cloudflare R2, DigitalOcean Spaces, Backblaze B2, MinIO.

**Network Volumes for Model Storage**: Use Network Volumes for persistent model storage shared across workers, not for outputs. Mounts at `/runpod-volume` (serverless) or `/workspace` (pods). Configure in RunPod template under "Advanced > Select Network Volume".

## N8N Optimization - Custom Handler

The `custom_handler.py` provides optimized input/output handling for N8N workflows, eliminating base64 encoding/decoding overhead and achieving ~2x performance improvement.

### Features

- **Input Flexibility**: Accept base64, HTTP URLs, S3 pre-signed URLs
- **URL Streaming**: Fetch images directly without base64 decoding step
- **S3 Output**: Upload generated images to S3, return URLs instead of base64
- **Performance**: Eliminate redundant encoding/decoding operations

### Input Formats

The handler accepts input in multiple formats:

```json
{
  "input": {
    "type": "url",
    "data": "https://example.com/image.png"
  },
  "workflow": { ... }
}
```

**Supported Types**:
- `url`: HTTP/HTTPS URL (N8N sends image URL → handler fetches binary)
- `base64`: Base64-encoded image data
- `s3_url`: S3 pre-signed URL (works with any S3-compatible storage)

### Output Formats

**With S3 configured** (environment variables set):
```json
{
  "type": "s3_url",
  "data": "https://your-bucket.s3.amazonaws.com/job-id/image.png"
}
```

**Without S3** (fallback to base64):
```json
{
  "type": "base64",
  "data": "iVBORw0KGgoAAAANS..."
}
```

### Environment Variables

Add to RunPod template for S3 optimization:
```bash
BUCKET_ENDPOINT_URL=https://your-bucket-name.s3.us-east-1.amazonaws.com
BUCKET_ACCESS_KEY_ID=AKIA...
BUCKET_SECRET_ACCESS_KEY=your-secret-key
BUCKET_NAME=comfy-outputs  # Optional, defaults to 'comfy-outputs'
AWS_REGION=us-east-1       # Optional, defaults to 'us-east-1'
```

### Performance Comparison

**Base64 Workflow** (current default):
1. N8N converts image to base64 (~2MB image = ~2.7MB base64)
2. Send 2.7MB JSON payload over network
3. Handler decodes base64 → binary (CPU cost)
4. ComfyUI generates output
5. Encode output to base64
6. Send 2.7MB JSON response

**URL-based Workflow** (optimized):
1. N8N uploads image to temporary URL/S3 (~2MB)
2. Send 200 bytes JSON with URL
3. Handler fetches binary via HTTP (parallel to ComfyUI processing)
4. ComfyUI generates output
5. Handler uploads to S3 (~2MB)
6. Send 200 bytes JSON response with S3 URL

**Result**: ~2x faster, 90% smaller JSON payloads

### Integration with N8N

See the N8N integration guide in this repository for complete workflow examples.
