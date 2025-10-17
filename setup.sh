#!/bin/bash

echo ""
echo "================================================================"
echo "  RVC Song Processor - Setup"
echo "================================================================"
echo ""

echo "[1/11] Checking Python..."
command -v python3 &> /dev/null || (echo "Python not found" && exit 1)
echo "Found Python $(python3 --version | awk '{print $2}')"

echo ""
echo "[2/11] Detecting GPU..."
HAS_CUDA=0
HAS_MPS=0
command -v nvidia-smi &> /dev/null && (echo "NVIDIA GPU detected" && HAS_CUDA=1)
[[ "$OSTYPE" == "darwin"* ]] && [[ $(uname -m) == "arm64" ]] && (echo "Apple Silicon" && HAS_MPS=1)
[ $HAS_CUDA -eq 0 ] && [ $HAS_MPS -eq 0 ] && echo "No GPU"

echo ""
echo "[3/11] Creating directories..."
for dir in MyDownloadedModels temp_outputs media_cache unpacked_models separation_outputs; do
    mkdir -p "$dir" && echo "Created $dir"
done

echo ""
echo "[4/11] Cloning RVC-v2-UI..."
if [ ! -d "RVC-v2-UI/src" ]; then
    git clone https://github.com/PseudoRAM/RVC-v2-UI.git 2>/dev/null || (
        curl -L "https://github.com/PseudoRAM/RVC-v2-UI/archive/main.zip" -o rvc.zip
        unzip -q rvc.zip && mv RVC-v2-UI-main RVC-v2-UI && rm rvc.zip
    )
    echo "Cloned"
else
    echo "Exists"
fi
mkdir -p RVC-v2-UI/rvc_models

echo ""
echo "[5/11] Creating venv..."
[ ! -d "venv" ] && (python3 -m venv venv && echo "Created") || echo "Exists"

source venv/bin/activate
python -m pip install pip==24.0 --quiet
echo "pip 24.0 ready"

echo ""
echo "[6/11] Installing PyTorch 2.0.1..."
if [ $HAS_CUDA -eq 1 ]; then
    pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 --index-url https://download.pytorch.org/whl/cu118
elif [ $HAS_MPS -eq 1 ]; then
    pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
else
    pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
fi

echo ""
echo "[7/11] Installing onnxruntime..."
[ $HAS_CUDA -eq 1 ] && pip install onnxruntime-gpu==1.22.0 || pip install onnxruntime

echo ""
echo "[6/10] Installing dependencies from requirements.txt..."
pip install -r requirements.txt
pip install --no-deps audio-separator==0.36.1

echo ""
echo "[7/10] Fixing library versions for RVC compatibility..."
pip install --force-reinstall -r requirements-final.txt

echo ""
echo "[9/11] Downloading models..."
[ ! -f "MyDownloadedModels/hack.zip" ] && curl -L "https://storage.googleapis.com/eighth-block-311611.appspot.com/hack.zip" -o "MyDownloadedModels/hack.zip"
[ ! -f "MyDownloadedModels/guitar.zip" ] && curl -L "https://storage.googleapis.com/eighth-block-311611.appspot.com/guitar.zip" -o "MyDownloadedModels/guitar.zip"
[ ! -f "RVC-v2-UI/rvc_models/hubert_base.pt" ] && curl -L "https://storage.googleapis.com/eighth-block-311611.appspot.com/hubert_base.pt" -o "RVC-v2-UI/rvc_models/hubert_base.pt"
[ ! -f "RVC-v2-UI/rvc_models/rmvpe.pt" ] && curl -L "https://storage.googleapis.com/eighth-block-311611.appspot.com/rmvpe.pt" -o "RVC-v2-UI/rvc_models/rmvpe.pt"

echo ""
echo "[10/11] Creating config..."
if [ ! -f "local_models.json" ]; then
    cat > local_models.json << 'EOF'
{
  "האק": {"path": "MyDownloadedModels/hack.zip", "pitch": 0},
  "גיטרה": {"path": "MyDownloadedModels/guitar.zip", "pitch": 0}
}
EOF
fi
[ ! -f "youtube_audio_cache.json" ] && echo "{}" > youtube_audio_cache.json

echo ""
echo "[11/11] Creating start.sh..."
cat > start.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
[[ "$OSTYPE" == "darwin"* ]] && open http://localhost:7860 || (command -v xdg-open &> /dev/null && xdg-open http://localhost:7860)
python standalone_song_processor.py
EOF
chmod +x start.sh

echo ""
echo "================================================================"
python -c "import torch; print('torch:', torch.__version__)"
python -c "import numpy; print('numpy:', numpy.__version__)"
python -c "import gradio; print('gradio:', gradio.__version__)"
[ $HAS_CUDA -eq 1 ] && python -c "import torch; print('CUDA:', torch.cuda.is_available())"
echo "================================================================"
echo ""
echo "Done. Run: ./start.sh"
