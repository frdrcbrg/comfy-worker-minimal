# Simple ComfyUI Worker Dockerfile
# Using CUDA 12.8.1 for RTX 5090 (Blackwell) support
FROM runpod/worker-comfyui:5.4.1-base-cuda12.8.1

# Install S3 dependencies for output optimization
RUN pip install --no-cache-dir boto3

# Copy custom handler for N8N optimization
COPY custom_handler.py /

# Set custom handler as entry point
ENV RUNPOD_DEBUG=false

# Install custom nodes
RUN comfy-node-install \
    "https://github.com/ltdrdata/ComfyUI-Impact-Pack" \
    "https://github.com/rgthree/rgthree-comfy" \
    "https://github.com/cubiq/ComfyUI_essentials" \
    "https://github.com/chrisgoringe/cg-use-everywhere" \
    "https://github.com/ssitu/ComfyUI_UltimateSDUpscale" && \
    pip cache purge && \
    apt-get clean && \
    rm -rf /tmp/* /var/tmp/* /var/cache/apt/*

# Download models (optional - uncomment and configure for your needs)
# RUN comfy model download --url https://your-model-url.safetensors \
#     --relative-path models/checkpoints \
#     --filename your-model.safetensors

# Copy static input files (optional - create an input/ folder if needed)
# COPY input/ /comfyui/input/
