@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ================================================================
echo   RVC Song Processor - Setup
echo ================================================================
echo.

echo [1/11] Checking Python...
python --version >nul 2>&1 || (echo Python not found & pause & exit /b 1)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo Found Python %%i

echo.
echo [2/11] Detecting GPU...
set HAS_CUDA=0
nvidia-smi >nul 2>&1 && (echo NVIDIA GPU detected & set HAS_CUDA=1) || echo No GPU

echo.
echo [3/11] Creating directories...
for %%d in (MyDownloadedModels temp_outputs media_cache unpacked_models separation_outputs) do if not exist "%%d" (mkdir "%%d" & echo Created %%d)

echo.
echo [4/11] Cloning RVC-v2-UI...
if not exist "RVC-v2-UI\src" (
    git clone https://github.com/PseudoRAM/RVC-v2-UI.git 2>nul || (
        curl -L "https://github.com/PseudoRAM/RVC-v2-UI/archive/main.zip" -o rvc.zip
        tar -xf rvc.zip && move RVC-v2-UI-main RVC-v2-UI >nul && del rvc.zip
    )
    echo Cloned
) else (
    echo Exists
)
if not exist "RVC-v2-UI\rvc_models" mkdir RVC-v2-UI\rvc_models

echo.
echo [5/11] Creating venv...
if not exist "venv" (python -m venv venv & echo Created) else echo Exists

call venv\Scripts\activate.bat
python -m pip install pip==24.0 --quiet
echo pip 24.0 ready

echo.
echo [6/11] Installing PyTorch 2.0.1+cu118...
if !HAS_CUDA!==1 (
    pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 --index-url https://download.pytorch.org/whl/cu118
) else (
    pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
)

echo.
echo [7/11] Installing onnxruntime...
if !HAS_CUDA!==1 (pip install onnxruntime-gpu==1.22.0) else (pip install onnxruntime)

echo.
echo [8/11] Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo Installing audio-separator...
pip install --no-deps audio-separator==0.36.1

echo.
echo Fixing library versions for RVC compatibility...
pip install --force-reinstall -r requirements-final.txt

echo.
echo [9/11] Downloading models...
if not exist "MyDownloadedModels\hack.zip" curl -L "https://storage.googleapis.com/eighth-block-311611.appspot.com/hack.zip" -o "MyDownloadedModels\hack.zip"
if not exist "MyDownloadedModels\guitar.zip" curl -L "https://storage.googleapis.com/eighth-block-311611.appspot.com/guitar.zip" -o "MyDownloadedModels\guitar.zip"
if not exist "RVC-v2-UI\rvc_models\hubert_base.pt" curl -L "https://storage.googleapis.com/eighth-block-311611.appspot.com/hubert_base.pt" -o "RVC-v2-UI\rvc_models\hubert_base.pt"
if not exist "RVC-v2-UI\rvc_models\rmvpe.pt" curl -L "https://storage.googleapis.com/eighth-block-311611.appspot.com/rmvpe.pt" -o "RVC-v2-UI\rvc_models\rmvpe.pt"

echo.
echo [10/11] Creating config...
if not exist "local_models.json" (
    (echo {& echo   "האק": {"path": "MyDownloadedModels/hack.zip", "pitch": 0},& echo   "גיטרה": {"path": "MyDownloadedModels/guitar.zip", "pitch": 0}& echo }) > local_models.json
)
if not exist "youtube_audio_cache.json" echo {} > youtube_audio_cache.json

echo.
echo [11/11] Creating start.bat...
(
echo @echo off
echo call venv\Scripts\activate.bat
echo start http://localhost:7860
echo python standalone_song_processor.py
echo pause
) > start.bat

echo.
echo ================================================================
python -c "import torch; print('torch:', torch.__version__)"
python -c "import numpy; print('numpy:', numpy.__version__)"
python -c "import gradio; print('gradio:', gradio.__version__)"
if !HAS_CUDA!==1 python -c "import torch; print('CUDA:', torch.cuda.is_available())"
echo ================================================================
echo.
echo Done. Run start.bat
pause
