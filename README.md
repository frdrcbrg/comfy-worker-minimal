# ComfyUI Worker Minimal

A minimal Docker-based template for creating custom ComfyUI workers that run on RunPod or any containerized GPU environment.

## Features

- 🚀 Based on `runpod/worker-comfyui:5.4.1-base-cuda12.8.1` with CUDA 12.8.1 for RTX 5090 support
- 🔧 Easy customization via simple Dockerfile modifications
- 📦 Pre-built images available on GitHub Container Registry
- ⚡ GitHub Actions CI/CD for automatic builds
- 🎯 Minimal and focused - only what you need

## Quick Start

### Using Pre-built Images

Pull and run a stable versioned image (recommended for production):

```bash
# Use a specific version (recommended for production)
docker pull ghcr.io/frdrcbrg/comfy-worker-minimal:1.2.0
docker run --gpus all -p 8188:8188 ghcr.io/frdrcbrg/comfy-worker-minimal:1.2.0

# Or use flexible versioning
docker pull ghcr.io/frdrcbrg/comfy-worker-minimal:1.2
docker run --gpus all -p 8188:8188 ghcr.io/frdrcbrg/comfy-worker-minimal:1.2

# Or use latest from main branch (for development)
docker pull ghcr.io/frdrcbrg/comfy-worker-minimal:main
docker run --gpus all -p 8188:8188 ghcr.io/frdrcbrg/comfy-worker-minimal:main
```

**Available Image Tags:**
- `1.2.0` - Latest stable version with CUDA 12.8.1 and RTX 5090 support
- `1.2` - Latest v1.2.x patch
- `1` - Latest v1.x minor version
- `main` - Latest development build
- `sha-*` - Specific commit builds

### Building Locally

Clone and build your own version:

```bash
git clone https://github.com/frdrcbrg/comfy-worker-minimal.git
cd comfy-worker-minimal
docker build -t my-comfy-worker .
docker run --gpus all -p 8188:8188 my-comfy-worker
```

## Customization

All customizations are made by editing the `Dockerfile`. Uncomment and modify the sections you need:

### 1. Install Custom Nodes

```dockerfile
RUN comfy-node-install comfyui-kjnodes comfyui-ic-light
```

Find available nodes at the [Comfy Registry](https://registry.comfy.org/).

### 2. Download Models

```dockerfile
RUN comfy model download --url https://huggingface.co/model.safetensors \
    --relative-path models/checkpoints \
    --filename my-model.safetensors
```

**Common model paths**:
- `models/checkpoints` - Checkpoint models
- `models/loras` - LoRA models
- `models/vae` - VAE models
- `models/clip` - CLIP models

### 3. Add Static Input Files

Create an `input/` directory and copy files:

```dockerfile
COPY input/ /comfyui/input/
```

## Deployment

### Deploy to RunPod

**Option 1: Use Pre-built Image**
1. Go to [RunPod Templates](https://www.runpod.io/console/templates)
2. Create a new template
3. Use image: `ghcr.io/frdrcbrg/comfy-worker-minimal:1.2`
4. Deploy as a serverless endpoint or GPU pod

**Option 2: Use Customized Image**
1. Fork this repository and customize the Dockerfile
2. Your GitHub Actions will automatically build and publish to GHCR
3. Use your custom image: `ghcr.io/your-username/comfy-worker-minimal:1.2`
4. Create a RunPod template with your image

**Environment Variables** (optional):
```
COMFYUI_PORT=8188
```

## Storage Configuration

### S3 Storage for Generated Images

By default, ComfyUI workers return generated images as base64-encoded strings. For production use, configure S3 storage to automatically upload images to your bucket.

#### Configure S3 Environment Variables

Add these environment variables to your RunPod template:

```bash
BUCKET_ENDPOINT_URL=https://your-bucket-name.s3.us-east-1.amazonaws.com
BUCKET_ACCESS_KEY_ID=AKIA...
BUCKET_SECRET_ACCESS_KEY=your-secret-key
```

#### AWS Setup Requirements

1. **Create an S3 Bucket**
   - Choose your preferred AWS region
   - Enable appropriate access settings

2. **Create IAM User**
   - Create an IAM user with programmatic access
   - Attach a policy with `s3:PutObject` permission:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": ["s3:PutObject", "s3:PutObjectAcl"],
         "Resource": "arn:aws:s3:::your-bucket-name/*"
       }
     ]
   }
   ```

3. **Get Credentials**
   - Copy the Access Key ID and Secret Access Key
   - Use these for the environment variables above

#### Output Format Changes

**Without S3 (default):**
```json
{
  "type": "base64",
  "data": "iVBORw0KGgoAAAANS..."
}
```

**With S3 configured:**
```json
{
  "type": "s3_url",
  "data": "https://your-bucket.s3.amazonaws.com/job-id/image.png"
}
```

#### S3-Compatible Storage

This works with any S3-compatible storage provider:
- **AWS S3** - Standard option
- **Cloudflare R2** - No egress fees
- **DigitalOcean Spaces** - Simple pricing
- **Backblaze B2** - Cost-effective
- **MinIO** - Self-hosted option

Just use the appropriate endpoint URL for your provider.

### Network Volumes

Network Volumes are recommended for **storing models**, not outputs:

- **Serverless**: Mounts at `/runpod-volume`
- **Pods**: Mounts at `/workspace`
- **Use case**: Persistent model storage shared across workers
- **Setup**: Attach in RunPod template under "Advanced > Select Network Volume"

For organizing models in a Network Volume:
```
/models/checkpoints/  - Checkpoint models
/models/loras/        - LoRA models
/models/vae/          - VAE models
/models/clip/         - CLIP models
/models/controlnet/   - ControlNet models
```

### Versioning

This project uses [Semantic Versioning](https://semver.org/):
- **MAJOR** (v2.0.0): Breaking changes (e.g., base image upgrade)
- **MINOR** (v1.1.0): New features, backward compatible (e.g., new custom nodes)
- **PATCH** (v1.0.1): Bug fixes and documentation updates

Create a new release:

```bash
# Using GitHub CLI (recommended)
gh release create v1.3.0 --title "v1.3.0 - Feature Update" --notes "Description of changes"

# Or manually with git tags
git tag -a v1.3.0 -m "Release v1.3.0"
git push origin v1.3.0
```

GitHub Actions will automatically build and publish the Docker images with appropriate tags.

## Requirements

- Docker with GPU support (NVIDIA)
- CUDA-compatible GPU for local testing
- GitHub account for using pre-built images

## Documentation

- [`CLAUDE.md`](CLAUDE.md) - Developer documentation for working with this codebase
- [RunPod Worker ComfyUI Docs](https://github.com/runpod-workers/worker-comfyui) - Upstream project documentation

## License

This is a template repository. Customize and use it however you need.
