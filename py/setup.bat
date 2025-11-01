@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ============================================
echo   Suno Song Processor - By PresidentPikachu
echo ============================================
echo.
:: Check Python version and use 3.10 if system Python > 3.10
echo [1/7] Checking Python...
set PYTHON_CMD=python
python --version >nul 2>&1 || (echo ERROR: Python not found & pause & exit /b 1)

for /f "tokens=2 delims=." %%a in ('python --version 2^>^&1') do (
    for /f "tokens=1" %%b in ("%%a") do set MINOR=%%b
)

if %MINOR% GTR 10 (
    echo System Python is 3.%MINOR% ^(too new^). Using embedded Python 3.10...
    echo Downloading Python 3.10.11 embedded...
    curl -L "https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip" -o python310.zip
    mkdir python310
    tar -xf python310.zip -C python310
    del python310.zip

    echo Enabling pip in embedded Python...
    del python310\python310._pth
    curl -L "https://bootstrap.pypa.io/get-pip.py" -o python310\get-pip.py
    python310\python.exe python310\get-pip.py
    set PYTHON_CMD=python310\python.exe
    echo Using embedded Python 3.10.11
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo Using system Python %%i
)

:: Detect GPU
echo.
echo [2/7] Detecting GPU...
set HAS_CUDA=0
nvidia-smi >nul 2>&1 && (
    echo NVIDIA GPU detected
    set HAS_CUDA=1
) || echo No GPU - CPU only

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


:: Create virtual environment or use embedded Python
echo.
echo [5/7] Setting up Python environment...
if %MINOR% GTR 10 (
    echo Using embedded Python 3.10 directly ^(no venv needed^)
    set "PATH=%CD%\python310;%CD%\python310\Scripts;%PATH%"
    python -m pip install pip==24.0 --quiet
) else (
    if not exist "venv" (
        %PYTHON_CMD% -m venv venv
        echo Virtual environment created
    ) else (
        echo Virtual environment already exists
    )
    call venv\Scripts\activate.bat
    python -m pip install pip==24.0 --quiet
)

:: CRITICAL: Install PyTorch FIRST and LOCK IT
echo.
echo [6/7] Installing packages...
echo.
echo Installing PyTorch...
if !HAS_CUDA!==1 (
    pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 --index-url https://download.pytorch.org/whl/cu118
    pip install onnxruntime-gpu==1.22.0
) else (
    pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
    pip install onnxruntime==1.22.0
)

:: Install core dependencies from requirements.txt (This replaces all redundant installations)
echo.
echo Installing core and minimal dependencies...
pip install -r requirements.txt --upgrade

:: Fairseq minimal deps ONLY (The fairseq line below is missing dependencies in the batch file)
echo.
echo Installing Fairseq and its minimal dependencies (hydra-core, omegaconf, etc.)...
pip install sacrebleu regex tqdm bitarray
pip install --no-deps fairseq==0.12.2
pip install hydra-core==1.0.7 omegaconf==2.0.6


:: Gradio and essential deps ONLY (This uses the versions from the original install and adds missing ones)
echo.
echo Installing Gradio UI and core dependencies...
pip install gradio==5.42.0 

:: Audio separator minimal deps (only what wasn't in requirements.txt or was manually installed)
echo.
echo Installing additional audio separation components...
pip install --no-deps audio-separator==0.36.1 numpy==1.26.4 torchcrepe
pip install onnx imageio-ffmpeg

:: Download models
echo.
echo [7/7] Downloading models...
if not exist "MyDownloadedModels\hack.zip" (
    curl -L "https://storage.googleapis.com/eighth-block-311611.appspot.com/hack.zip" -o "MyDownloadedModels\hack.zip"
)
if not exist "MyDownloadedModels\guitar.zip" (
    curl -L "https://storage.googleapis.com/eighth-block-311611.appspot.com/guitar.zip" -o "MyDownloadedModels\guitar.zip"
)
if not exist "RVC-v2-UI\rvc_models\hubert_base.pt" (
    curl -L "https://storage.googleapis.com/eighth-block-311611.appspot.com/hubert_base.pt" -o "RVC-v2-UI\rvc_models\hubert_base.pt"
)
if not exist "RVC-v2-UI\rvc_models\rmvpe.pt" (
    curl -L "https://storage.googleapis.com/eighth-block-311611.appspot.com/rmvpe.pt" -o "RVC-v2-UI\rvc_models\rmvpe.pt"
)

:: Create configs
if not exist "local_models.json" (
    (
        echo {
        echo   "האק": {"path": "MyDownloadedModels/hack.zip", "pitch": 0},
        echo   "גיטרה": {"path": "MyDownloadedModels/guitar.zip", "pitch": 0}
        echo }
    ) > local_models.json
)
if not exist "youtube_audio_cache.json" echo {} > youtube_audio_cache.json

:: Create start script
if %MINOR% GTR 10 (
    (
        echo @echo off
        echo set "PATH=%%CD%%\python310;%%CD%%\python310\Scripts;%%PATH%%"
        echo start /B python app.py
        echo timeout /t 3 /nobreak ^>nul
        echo start http://localhost:7860
        echo pause
    ) > start.bat
) else (
    (
        echo @echo off
        echo call venv\Scripts\activate.bat
        echo start /B python app.py
        echo timeout /t 3 /nobreak ^>nul
        echo start http://localhost:7860
        echo pause
    ) > start.bat
)

:: Verify
echo.
echo ================================================================
echo Verifying installation...
echo ================================================================
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
if !HAS_CUDA!==1 (
    python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
)
python -c "import librosa; print(f'Librosa: {librosa.__version__}')"
python -c "import gradio; print(f'Gradio: {gradio.__version__}')"
python -c "import fairseq; print('Fairseq: OK')"
python -c "from audio_separator.separator import Separator; print('Audio Separator: OK')"
echo ================================================================
echo.
echo DONE.
echo Run 'start.bat' to launch.
echo.
pause