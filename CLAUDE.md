# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a minimal Docker-based template for creating custom ComfyUI workers that run on RunPod. The project intentionally contains minimal files and is designed to be extended with custom nodes, models, and configurations.

## Architecture

**Base Image**: The Dockerfile extends `runpod/worker-comfyui:5.5.0-sdxl`, which provides:
- A clean ComfyUI installation
- The `comfy-cli` tooling (including `comfy-node-install` and `comfy model download`)
- Python runtime with GPU support
- RunPod worker SDK integration

**Customization Pattern**: All customizations are made by modifying the Dockerfile:
1. **Custom Nodes**: Installed using `comfy-node-install` command with node names or URLs
2. **Models**: Downloaded using `comfy model download` with `--url`, `--relative-path`, and `--filename` parameters
3. **Static Files**: Copied into the container using `COPY input/ /comfyui/input/`

## Common Commands

### Building the Docker Image
```bash
docker build -t comfy-worker-minimal .
```

### Testing Locally
```bash
docker run --gpus all -p 8188:8188 comfy-worker-minimal
```

### Pushing to Registry
```bash
docker tag comfy-worker-minimal your-registry/comfy-worker-minimal:version
docker push your-registry/comfy-worker-minimal:version
```

## Key Conventions

**Model Paths**: When downloading models, use correct `--relative-path` values that match ComfyUI's directory structure:
- `models/checkpoints` - For checkpoint models
- `models/loras` - For LoRA models
- `models/vae` - For VAE models
- `models/clip` - For CLIP models

**Custom Node Installation**: Use the `comfy-node-install` command (not standard `comfy-cli`) as it provides better error reporting. Find node names at the Comfy Registry.

**Version Tags**: The base image uses specific tags like `-sdxl` which includes SDXL models pre-packaged, or `-base` for clean installs. Update version number (e.g., `5.5.0`) as needed from the runpod/worker-comfyui releases.
