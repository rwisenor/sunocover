#!/bin/bash

echo ""
echo "============================================"
echo "  Suno Song Processor - By PresidentPikachu"
echo "============================================"
echo ""

# Check Python version and use 3.10 if system Python > 3.10
echo "[1/7] Checking Python..."
command -v python3 &> /dev/null || (echo "ERROR: Python not found" && exit 1)

PYTHON_CMD="python3"
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$MINOR_VERSION" -gt 10 ]; then
    echo "System Python is 3.$MINOR_VERSION (too new). Using embedded Python 3.10..."
    if [ ! -f "python310/bin/python3" ]; then
        echo "Downloading Python 3.10.11 standalone..."

        # Download python-build-standalone
        if [[ "$OSTYPE" == "darwin"* ]]; then
            if [[ $(uname -m) == "arm64" ]]; then
                PYTHON_URL="https://github.com/indygreg/python-build-standalone/releases/download/20230507/cpython-3.10.11+20230507-aarch64-apple-darwin-install_only.tar.gz"
            else
                PYTHON_URL="https://github.com/indygreg/python-build-standalone/releases/download/20230507/cpython-3.10.11+20230507-x86_64-apple-darwin-install_only.tar.gz"
            fi
        else
            PYTHON_URL="https://github.com/indygreg/python-build-standalone/releases/download/20230507/cpython-3.10.11+20230507-x86_64-unknown-linux-gnu-install_only.tar.gz"
        fi

        curl -L "$PYTHON_URL" -o python310.tar.gz
        mkdir -p python310
        tar -xzf python310.tar.gz -C python310 --strip-components=1
        rm python310.tar.gz
        echo "Embedded Python 3.10.11 installed"
    fi
    PYTHON_CMD="python310/bin/python3"
    echo "Using embedded Python 3.10.11"
else
    echo "Using system Python $PYTHON_VERSION"
fi

# Detect GPU
echo ""
echo "[2/7] Detecting GPU..."
HAS_CUDA=0
HAS_MPS=0
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected"
    HAS_CUDA=1
elif [[ "$OSTYPE" == "darwin"* ]] && [[ $(uname -m) == "arm64" ]]; then
    echo "Apple Silicon detected"
    HAS_MPS=1
else
    echo "No GPU - CPU only"
fi

echo ""
echo "[3/11] Creating directories..."
for dir in MyDownloadedModels temp_outputs media_cache unpacked_models separation_outputs; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir" && echo "Created $dir"
    fi
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

# Create virtual environment or use standalone Python
echo ""
echo "[5/7] Setting up Python environment..."
if [ "$MINOR_VERSION" -gt 10 ]; then
    echo "Using standalone Python 3.10 directly (no venv needed)"
    export PATH="$(pwd)/python310/bin:$PATH"
    python3 -m pip install pip==24.0 --quiet
else
    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
        echo "Virtual environment created"
    else
        echo "Virtual environment already exists"
    fi
    source venv/bin/activate
    python -m pip install pip==24.0 --quiet
fi

# CRITICAL: Install PyTorch FIRST and LOCK IT
echo ""
echo "[6/7] Installing packages..."
echo ""
echo "Installing PyTorch..."
if [ $HAS_CUDA -eq 1 ]; then
    pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 --index-url https://download.pytorch.org/whl/cu118
    pip install onnxruntime-gpu==1.22.0
elif [ $HAS_MPS -eq 1 ]; then
    pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
    pip install onnxruntime==1.22.0
else
    pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
    pip install onnxruntime==1.22.0
fi

# Install core dependencies from requirements.txt (This replaces all redundant installations)
echo ""
echo "Installing core and minimal dependencies..."
pip install -r requirements.txt --upgrade

# Fairseq minimal deps ONLY (The fairseq line below is missing dependencies in the batch file)
echo ""
echo "Installing Fairseq and its minimal dependencies (hydra-core, omegaconf, etc.)..."
pip install sacrebleu regex tqdm bitarray
pip install --no-deps fairseq==0.12.2
pip install hydra-core==1.0.7 omegaconf==2.0.6

# Gradio and essential deps ONLY (This uses the versions from the original install and adds missing ones)
echo ""
echo "Installing Gradio UI and core dependencies..."
pip install gradio==5.42.0

# Audio separator minimal deps (only what wasn't in requirements.txt or was manually installed)
echo ""
echo "Installing additional audio separation components..."
pip install --no-deps audio-separator==0.36.1 numpy==1.26.4 torchcrepe
pip install onnx imageio-ffmpeg

# Download models
echo ""
echo "[7/7] Downloading models..."
[ ! -f "MyDownloadedModels/hack.zip" ] && curl -L "https://storage.googleapis.com/eighth-block-311611.appspot.com/hack.zip" -o "MyDownloadedModels/hack.zip"
[ ! -f "MyDownloadedModels/guitar.zip" ] && curl -L "https://storage.googleapis.com/eighth-block-311611.appspot.com/guitar.zip" -o "MyDownloadedModels/guitar.zip"
[ ! -f "RVC-v2-UI/rvc_models/hubert_base.pt" ] && curl -L "https://storage.googleapis.com/eighth-block-311611.appspot.com/hubert_base.pt" -o "RVC-v2-UI/rvc_models/hubert_base.pt"
[ ! -f "RVC-v2-UI/rvc_models/rmvpe.pt" ] && curl -L "https://storage.googleapis.com/eighth-block-311611.appspot.com/rmvpe.pt" -o "RVC-v2-UI/rvc_models/rmvpe.pt"

# Create configs
if [ ! -f "local_models.json" ]; then
    cat > local_models.json << 'EOF'
{
  "האק": {"path": "MyDownloadedModels/hack.zip", "pitch": 0},
  "גיטרה": {"path": "MyDownloadedModels/guitar.zip", "pitch": 0}
}
EOF
fi
[ ! -f "youtube_audio_cache.json" ] && echo "{}" > youtube_audio_cache.json

# Create start script
if [ "$MINOR_VERSION" -gt 10 ]; then
    cat > start.sh << 'EOF'
#!/bin/bash
export PATH="$(pwd)/python310/bin:$PATH"
python3 app.py &
sleep 3
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:7860
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:7860
fi
wait
EOF
else
    cat > start.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python app.py &
sleep 3
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:7860
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:7860
fi
wait
EOF
fi
chmod +x start.sh

# Verify
echo ""
echo "================================================================"
echo "Verifying installation..."
echo "================================================================"
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
if [ $HAS_CUDA -eq 1 ]; then
    python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
fi
python -c "import librosa; print(f'Librosa: {librosa.__version__}')"
python -c "import gradio; print(f'Gradio: {gradio.__version__}')"
python -c "import fairseq; print('Fairseq: OK')"
python -c "from audio_separator.separator import Separator; print('Audio Separator: OK')"
echo "================================================================"
echo ""
echo "DONE."
echo "Run './start.sh' to launch."
echo ""
