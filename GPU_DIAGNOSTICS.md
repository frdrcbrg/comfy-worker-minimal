# GPU Diagnostics and Troubleshooting

## Confirming GPU Usage

Based on your output, **the GPU IS being used**. Here are the key indicators:

### GPU Detection Signs ✓
```
VAE load device: cuda:0
CLIP/text encoder model load device: cuda:0
dtype: torch.bfloat16
```

These lines confirm:
- **cuda:0** = GPU #0 is active
- **torch.bfloat16** = GPU optimized precision
- Models are loading to GPU memory

### Normal Warnings (Not Errors)

These warnings are **safe to ignore**:
```
Model doesn't have a device attribute.
```
This is a compatibility message from ComfyUI's memory management - it doesn't prevent GPU usage.

```
clip missing: ['clip_l.logit_scale', 'clip_l.transformer.text_projection.weight']
clip unexpected ['clip_l.transformer.text_model.embeddings.position_ids']
```
These are model format mismatches that ComfyUI handles automatically.

## Verifying GPU Performance

### Method 1: Check NVIDIA-SMI Output

SSH into your RunPod and run:
```bash
nvidia-smi
```

Expected output:
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 555.XX.XX    Driver Version: 555.XX.XX       CUDA Version: 12.8 |
+-----------------------------------------------------------------------------+
| GPU  Name       Persistence-M | Bus-Id  Disp.A | Volatile Uncorr. ECC     |
| 0    RTX 5090       Off        | 00:1F.0  Off   |                  Disabled |
+-----------------------------------------------------------------------------+
```

Look for your GPU appearing and memory being used during workflow execution.

### Method 2: Monitor GPU During Execution

While running a workflow, check GPU usage:
```bash
watch -n 1 nvidia-smi
```

You should see:
- **Mem Usage** increasing during model load
- **GPU-Util** high (80-100%) during inference
- Process names: `python`, `torch`, or `comfyui`

### Method 3: Check Process GPU Usage

```bash
nvidia-smi pmon
```

Shows real-time GPU memory and utilization by process.

## Performance Optimization

### Current Setup
- Base image: CUDA 12.8.1 for RTX 5090 (optimal)
- Offload device: CPU (trades speed for VRAM)
- Precision: torch.bfloat16 (GPU optimized)

### Optimization Steps

#### 1. Check VRAM Usage
If models fit entirely on GPU (RTX 5090 has 32GB):
```bash
# In ComfyUI settings, disable offloading
# This keeps all models on VRAM for ~2x speed increase
```

#### 2. Monitor Execution Time
- First run: Slower (model loading, compilation)
- Subsequent runs: Should be significantly faster

Typical latency:
- Model loading: 10-30 seconds
- SDXL generation: 20-40 seconds per image (varies by steps)
- VAE decode: 2-5 seconds

#### 3. Batch Size Impact
Processing multiple images in one workflow:
- Batch size 1: Fastest per image
- Batch size 4+: Better amortized cost per image

### Memory Management

#### Signs of Out-of-Memory (OOM):
```
RuntimeError: CUDA out of memory
CUDA error: out of memory
```

#### Solutions:
1. **Reduce batch size** - Lower from 4 to 1
2. **Enable offloading** - Already configured, trades speed for VRAM
3. **Lower precision** - Keep bfloat16 (already optimal)
4. **Use smaller models** - Instead of SDXL, use SD1.5

## Workflow Execution Checklist

### Pre-Execution
- [ ] Models downloaded to image
- [ ] GPU has free VRAM (check: `nvidia-smi`)
- [ ] Temperature normal (~40-60°C idle)

### During Execution
- [ ] GPU util > 70% (should see active work)
- [ ] Memory increasing during model load
- [ ] No CUDA errors in logs

### Post-Execution
- [ ] Output generated successfully
- [ ] Check S3 upload (if configured)
- [ ] Review execution time

## Common Issues and Fixes

### Issue: "Model doesn't have a device attribute"
**Status**: Not an error, just a warning
**Action**: None needed, GPU is still being used

### Issue: GPU shows 0% utilization
**Causes**:
- Model still loading (wait 30-60 seconds)
- Workflow stuck on CPU operation
- GPU not properly initialized

**Fix**:
```bash
# Check GPU initialization
python -c "import torch; print(torch.cuda.is_available())"
# Should print: True
```

### Issue: Slow execution (but GPU is working)
**Likely causes**:
- CPU offloading enabled (design choice for VRAM)
- Models not in VRAM (first run)
- High CPU load from other processes

**Fix**:
- Run second iteration (models cached)
- Monitor with `nvidia-smi`
- Check if workflow can use smaller models

### Issue: CUDA out of memory
**Fix**:
- Reduce batch size
- Use lighter models
- Enable aggressive offloading

## RunPod Specific

### Instance Type Impact
- **RTX 5090**: 32GB VRAM, fastest
- **RTX 4090**: 24GB VRAM, slightly slower
- **A100**: Different but similar performance

### Network Volumes Impact
- Model loading from network volume: 1-5 seconds extra
- Output to S3: Network speed dependent
- Local temp storage: Fastest

## Advanced Diagnostics

### Enable ComfyUI Debug Logging
Add to RunPod environment:
```bash
DEBUG=1
COMFYUI_DEBUG=1
```

### Check CUDA Version Compatibility
```bash
python -c "import torch; print(torch.version.cuda)"
# Should be: 12.8
```

### Verify PyTorch GPU Installation
```bash
python -c "import torch; print(torch.cuda.get_device_name(0))"
# Should show your GPU name
```

## Performance Baseline

Typical performance on RTX 5090:
- **SDXL (50 steps)**: 25-35 seconds
- **SD1.5 (50 steps)**: 8-15 seconds
- **Model loading**: 10-30 seconds (first time)
- **Model loading (cached)**: 2-5 seconds

If you're significantly slower, check:
1. GPU utilization (nvidia-smi)
2. CPU usage (might be bottleneck)
3. Network volume latency (if using)
4. S3 upload time (if writing output)

## Summary

**Your GPU is working correctly.** The warnings you're seeing are normal ComfyUI behavior and don't indicate GPU problems. The `cuda:0` and `bfloat16` references prove GPU acceleration is active.

For production use:
1. Monitor GPU with `nvidia-smi` during first execution
2. Subsequent executions will be faster (cached models)
3. Adjust batch size based on your GPU VRAM
4. Use S3 for output (recommended, faster than base64)
