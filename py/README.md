# Legacy Suno Song Processor

The files in this directory contain the original Python-based desktop utility for
pre-processing audio before uploading to Suno. The setup instructions remain unchanged from
previous releases:

![Screenshot](../screenshot.png)

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows you can run `setup.bat`; on macOS/Linux run `chmod +x setup.sh && ./setup.sh`.

## Run

```bash
python app.py
```

The application provides the same user interface and processing pipeline described in the
original README.
