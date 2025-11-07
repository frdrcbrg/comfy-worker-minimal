# Simple ComfyUI Worker Dockerfile
# Using CUDA 12.8.1 for RTX 5090 (Blackwell) support
FROM runpod/worker-comfyui:5.4.1-base-cuda12.8.1

# Install custom nodes (optional - uncomment and add your desired nodes)
# RUN comfy-node-install comfyui-kjnodes comfyui-ic-light

# Download models (optional - uncomment and configure for your needs)
# RUN comfy model download --url https://your-model-url.safetensors \
#     --relative-path models/checkpoints \
#     --filename your-model.safetensors

# Copy static input files (optional - create an input/ folder if needed)
# COPY input/ /comfyui/input/

# Clean up to reduce image size
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    pip cache purge 2>/dev/null || true
