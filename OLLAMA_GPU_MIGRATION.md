# Ollama GPU Migration - Quick Reference

## Overview
The Trainium Job Center has been updated to use host-based Ollama instead of Docker container Ollama to enable GPU acceleration for inference.

## What Changed

### Before (Container-based)
- Ollama ran inside Docker container (`trainium_ollama`)
- No GPU access available
- Environment: `OLLAMA_HOST=http://ollama:11434`
- Automatic model pulling in container

### After (Host-based)  
- Ollama runs directly on host machine
- **GPU acceleration available** 🚀
- Environment: `OLLAMA_HOST=http://host.docker.internal:11434`
- Manual setup required on host

## Developer Migration Steps

### 1. Install Ollama on Host
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Pull Required Model
```bash
ollama pull gemma3:1b
```

### 3. Start Ollama Service
```bash
ollama serve  # Runs on localhost:11434
```

### 4. Verify Setup
```bash
cd python-service
python gpu_setup_check.py  # Comprehensive setup verification
```

### 5. Start Application
```bash
docker-compose up --build
```

## Verification Commands

### Check Ollama Status
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# List available models
ollama list

# Test inference
ollama run gemma3:1b "Hello, how are you?"
```

### Check GPU Availability
```bash
# Check for NVIDIA GPU
nvidia-smi

# Check Ollama can see GPU
ollama run gemma3:1b "Test GPU" --verbose
```

### Check Application Health
```bash
# Check health endpoint
curl http://localhost:8000/health

# Check LLM provider status
curl http://localhost:8000/health/detailed
```

## Troubleshooting

### Common Issues

**"Connection refused"**
- Ensure `ollama serve` is running
- Check if port 11434 is available

**"Model not found"**  
- Run `ollama pull gemma3:1b`
- Verify with `ollama list`

**"No GPU acceleration"**
- Install NVIDIA drivers
- Restart Ollama after driver installation
- Check `nvidia-smi` works

**Docker can't reach host**
- Verify `host.docker.internal` resolves
- On Linux, may need `--add-host=host.docker.internal:host-gateway`

## Configuration Files Changed

- `docker-compose.yml` - Removed ollama service, updated OLLAMA_HOST
- `.env.example` - Updated OLLAMA_HOST default
- `python-service/app/core/config.py` - Updated default host URL
- `README.md` - Added setup instructions
- `LLM_MIGRATION.md` - Updated with host-based guide

## Benefits Achieved

✅ **GPU Acceleration** - Direct access to host GPU  
✅ **Better Performance** - No container overhead for inference  
✅ **Simplified Architecture** - One less container to manage  
✅ **Developer Control** - Direct control over Ollama configuration  

## Fallback Behavior

If Ollama is not available, the system automatically falls back to:
1. OpenAI (if `OPENAI_API_KEY` is set)
2. Gemini (if `GEMINI_API_KEY` is set) 
3. Rule-based processing (if no LLM providers available)

This ensures the application remains functional even without Ollama.