# ComfyUI Worker Minimal

A minimal Docker-based template for creating custom ComfyUI workers that run on RunPod or any containerized GPU environment.

## Features

- 🚀 Based on `runpod/worker-comfyui:5.5.0-sdxl` with SDXL models pre-installed
- 🔧 Easy customization via simple Dockerfile modifications
- 📦 Pre-built images available on GitHub Container Registry
- ⚡ GitHub Actions CI/CD for automatic builds
- 🎯 Minimal and focused - only what you need

## Quick Start

### Using Pre-built Images

Pull and run the latest pre-built image:

```bash
docker pull ghcr.io/frdrcbrg/comfy-worker-minimal:main
docker run --gpus all -p 8188:8188 ghcr.io/frdrcbrg/comfy-worker-minimal:main
```

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

1. Build and push your customized image to a registry (Docker Hub, GHCR, etc.)
2. Create a new RunPod template using your image
3. Deploy as a serverless endpoint or GPU pod

### Version Tags

Images are automatically tagged on GitHub Container Registry:
- `main` - Latest build from main branch
- `v1.0.0` - Semantic version tags
- `sha-abc123` - Commit-specific tags

Create a version release:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Requirements

- Docker with GPU support (NVIDIA)
- CUDA-compatible GPU for local testing
- GitHub account for using pre-built images

## Documentation

- [`CLAUDE.md`](CLAUDE.md) - Developer documentation for working with this codebase
- [RunPod Worker ComfyUI Docs](https://github.com/runpod-workers/worker-comfyui) - Upstream project documentation

## License

This is a template repository. Customize and use it however you need.
