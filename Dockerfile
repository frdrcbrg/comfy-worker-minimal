# Simple ComfyUI Worker Dockerfile
# Using CUDA 12.8.1 for RTX 5090 (Blackwell) support
FROM runpod/worker-comfyui:5.4.1-base-cuda12.8.1

# Install S3 dependencies for output optimization
RUN pip install --no-cache-dir boto3

# Copy custom handler for N8N optimization
COPY custom_handler.py /

# Set custom handler as entry point
ENV RUNPOD_DEBUG=false

# Install custom nodes (optional - uncomment and add your desired nodes)
# RUN comfy-node-install comfyui-kjnodes comfyui-ic-light

# Download models (optional - uncomment and configure for your needs)
# RUN comfy model download --url https://your-model-url.safetensors \
#     --relative-path models/checkpoints \
#     --filename your-model.safetensors

# Copy static input files (optional - create an input/ folder if needed)
# COPY input/ /comfyui/input/
