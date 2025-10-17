#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
standalone_song_processor.py
אפליקציה עצמאית לעיבוד שירים עם RVC

משתמש בדיוק באותן מתודות כמו האפליקציה המקורית
"""

import gradio as gr
import os
import sys
import subprocess
import uuid
import shutil
import json
import zipfile
import hashlib
import base64
from pathlib import Path
import threading
import time

# ====== הגדרות תיקיות ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "temp_outputs")
UNPACKED_MODELS_DIR = os.path.join(BASE_DIR, "unpacked_models")
SEPARATION_OUTPUT_DIR = os.path.join(BASE_DIR, "separation_outputs")
LOCAL_MODELS_PATH = os.path.join(BASE_DIR, "MyDownloadedModels")
MEDIA_CACHE_DIR = os.path.join(BASE_DIR, "media_cache")
YOUTUBE_AUDIO_CACHE_PATH = os.path.join(BASE_DIR, "youtube_audio_cache.json")

# יצירת כל התיקיות הנדרשות
for dir_path in [OUTPUT_DIR, UNPACKED_MODELS_DIR, SEPARATION_OUTPUT_DIR,
                  LOCAL_MODELS_PATH, MEDIA_CACHE_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# ====== טעינת מודלים מקומיים ======
local_models = {}
youtube_audio_cache = {}

def load_local_models_config():
    """טוען את קובץ ההגדרות של המודלים המקומיים"""
    global local_models
    try:
        with open('local_models.json', 'r', encoding='utf-8') as f:
            local_models = json.load(f)
        print(f"Loaded {len(local_models)} models")

        # בדיקה שהמודלים הנדרשים קיימים
        required_models = ['האק', 'גיטרה']
        missing = [m for m in required_models if m not in local_models]
        if missing:
            print(f"⚠️ Missing models: {', '.join(missing)}")
            return False
        return True
    except FileNotFoundError:
        print("⚠️ local_models.json not found")
        local_models = {}
        return False
    except Exception as e:
        print(f"ERROR loading models: {e}")
        return False

def load_youtube_cache():
    """טוען את קאש היוטיוב מהדיסק"""
    global youtube_audio_cache
    try:
        if os.path.exists(YOUTUBE_AUDIO_CACHE_PATH):
            with open(YOUTUBE_AUDIO_CACHE_PATH, 'r', encoding='utf-8') as f:
                youtube_audio_cache = json.load(f)
            print(f"Loaded {len(youtube_audio_cache)} cached files")
    except Exception as e:
        print(f"⚠️ Cannot load cache: {e}")
        youtube_audio_cache = {}

def save_youtube_cache():
    """שומר את קאש היוטיוב לדיסק"""
    try:
        with open(YOUTUBE_AUDIO_CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(youtube_audio_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Cannot save cache: {e}")

def prepare_model_files(model_name):
    """מכין את קבצי המודל (חילוץ מ-ZIP אם צריך)"""
    global local_models

    if model_name not in local_models:
        raise Exception(f"מודל '{model_name}' not found. וודא שהמודל קיים ב-local_models.json")

    model_config = local_models[model_name]
    zip_path = model_config['path']
    pitch = model_config.get('pitch', 0)
    target_dir = os.path.join(UNPACKED_MODELS_DIR, model_name)

    if not os.path.exists(target_dir):
        print(f"📦 Extracting model '{model_name}'...")
        os.makedirs(target_dir)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)

    pth_file = next((os.path.join(target_dir, f) for f in os.listdir(target_dir)
                     if f.endswith(".pth")), None)
    if not pth_file:
        raise Exception(f"not found קובץ .pth למודל '{model_name}'")

    return pth_file, pitch

# ====== פונקציות עיבוד - מתאימות לקוד המקורי ======

def download_youtube_audio(url, progress_callback=None):
    """
    מוריד אודיו מיוטיוב - בדיוק כמו בקוד המקורי
    משתמש במערכת קאש זהה
    """
    global youtube_audio_cache

    try:
        # בדיקת קאש - כמו בקוד המקורי
        unique_id = base64.b64encode(url.encode()).decode().replace('/', '').replace('+', '').replace('=', '')
        cached_path = os.path.join(MEDIA_CACHE_DIR, f"{unique_id}.mp3")

        # קאש HIT מהזיכרון
        if url in youtube_audio_cache and os.path.exists(youtube_audio_cache[url]):
            print(f"✅ [YouTube Audio Cache] HIT: Found existing audio file for {url}")
            if progress_callback:
                progress_callback(1.0, "Found in cache!")
            return youtube_audio_cache[url]

        # קאש HIT מהדיסק
        if os.path.exists(cached_path):
            print(f"✅ [YouTube Audio Cache] HIT: Found existing audio file on disk")
            youtube_audio_cache[url] = cached_path
            save_youtube_cache()
            if progress_callback:
                progress_callback(1.0, "Found in cache!")
            return cached_path

        print(f"[YouTube Cache] MISS: No valid cached file found for {url}. Starting download...")

        if progress_callback:
            progress_callback(0.1, "Downloading from YouTube...")

        # בדיקה אם יש cookies.txt (כמו בקוד המקורי)
        cookies_path = os.path.join(BASE_DIR, 'cookies.txt')

        # פקודת yt-dlp - בדיוק כמו בקוד המקורי
        cmd = [
            'yt-dlp',
            url,
            '-f', 'bestaudio/best',
            '-x',  # חילוץ אודיו
            '--audio-format', 'mp3',
            '-o', cached_path
        ]

        if os.path.exists(cookies_path):
            cmd.extend(['--cookies', cookies_path])


        # הרצת yt-dlp עם הצגת התקדמות
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            universal_newlines=True,
            bufsize=1
        )

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                # חיפוש אחוז התקדמות
                if 'download' in line.lower() and '%' in line:
                    try:
                        # ניסיון לחלץ אחוז
                        percent_str = None
                        parts = line.split()
                        for part in parts:
                            if '%' in part:
                                percent_str = part.replace('%', '')
                                break

                        if percent_str:
                            percent = float(percent_str)
                            if progress_callback:
                                progress_callback(percent / 100, f"Downloading... {percent:.1f}%")
                    except:
                        pass
                print(f"[yt-dlp] {line}")

        return_code = process.wait()

        if return_code != 0:
            raise Exception(f"Download failed with code {return_code}")

        if not os.path.exists(cached_path):
            raise Exception("Downloaded file not found")

        # שמירה בקאש
        youtube_audio_cache[url] = cached_path
        save_youtube_cache()

        if progress_callback:
            progress_callback(1.0, "Download complete")

        return cached_path

    except Exception as e:
        raise

def run_separation(input_path, model_filename='UVR_MDXNET_KARA_2.onnx',
                   vocals_keyword='vocals', instrumental_keyword='instrumental',
                   progress_callback=None):
    """מפריד vocals מ-instrumental - כמו בקוד המקורי"""
    try:
        if progress_callback:
            progress_callback(0.0, f"Separating audio with {model_filename}...")

        output_dir = os.path.join(SEPARATION_OUTPUT_DIR, str(uuid.uuid4()))
        os.makedirs(output_dir)

        command = [
            sys.executable, "your_separation_script.py",
            "--input_path", input_path,
            "--output_dir", output_dir,
            "--model_filename", model_filename,
            "--vocals_keyword", vocals_keyword,
            "--instrumental_keyword", instrumental_keyword
        ]


        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            universal_newlines=True,
            bufsize=1
        )

        output_lines = []
        paths_result = None
        last_percent = 0

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                if '%' in line:
                    print(f"\r[Separation] {line}", end='')
                    try:
                        percent_str = line.split('%')[0].split()[-1]
                        percent = float(percent_str)
                        if abs(percent - last_percent) >= 5:  # עדכון כל 5%
                            last_percent = percent
                            if progress_callback:
                                progress_callback(percent / 100, f"Separating... {percent:.0f}%")
                    except:
                        pass
                else:
                    print(f"[Separation] {line}")
                output_lines.append(line)

                try:
                    paths = json.loads(line)
                    # Fix paths like gpu_server.py
                    corrected_paths = {}
                    for key, path in paths.items():
                        if not os.path.isabs(path):
                            corrected_paths[key] = os.path.join(output_dir, os.path.basename(path))
                        else:
                            corrected_paths[key] = path
                    paths_result = corrected_paths
                except json.JSONDecodeError:
                    continue

        return_code = process.wait()
        print()

        if return_code != 0:
            raise Exception(f"Separation failed with code {return_code}")

        if paths_result is None:
            raise Exception("No result from separation script")

        if progress_callback:
            progress_callback(1.0, "Separation complete")

        return paths_result

    except Exception as e:
        raise

def run_rvc_conversion(input_path, model_pth_path, pitch, progress_callback=None):
    """מריץ המרת קול עם RVC - כמו בקוד המקורי"""
    try:
        if progress_callback:
            progress_callback(0.0, "Voice conversion...")

        output_path = os.path.join(OUTPUT_DIR, f"{uuid.uuid4()}.wav")
        command = [
            sys.executable, "your_rvc_script_new.py",
            "--input_path", input_path,
            "--model_path", model_pth_path,
            "--output_path", output_path,
            "--pitch", str(pitch)
        ]


        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            universal_newlines=True,
            bufsize=1
        )

        output_lines = []
        last_percent = 0

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                if '%' in line:
                    print(f"\r[RVC] {line}", end='')
                    try:
                        percent_str = line.split('%')[0].split()[-1]
                        percent = float(percent_str)
                        if abs(percent - last_percent) >= 5:
                            last_percent = percent
                            if progress_callback:
                                progress_callback(percent / 100, f"Converting... {percent:.0f}%")
                    except:
                        pass
                else:
                    print(f"[RVC] {line}")
                output_lines.append(line)

        return_code = process.wait()
        print()

        if return_code != 0:
            raise Exception(f"RVC failed with code {return_code}")

        final_output_path = output_lines[-1].strip() if output_lines else output_path
        if not os.path.exists(final_output_path):
            raise Exception("RVC did not create valid output file")

        if progress_callback:
            progress_callback(1.0, "Voice conversion complete")

        return final_output_path

    except Exception as e:
        raise

def merge_audio(input_paths, output_path, progress_callback=None):
    """מאחד מספר קבצי אודיו - כמו בקוד המקורי"""
    try:
        if progress_callback:
            progress_callback(0.0, "Merging audio...")

        command = ['ffmpeg', '-y']

        for path in input_paths:
            command.extend(['-i', path])

        amix_inputs = ''.join([f'[{i}:a]' for i in range(len(input_paths))])
        filter_complex = f'{amix_inputs}amix=inputs={len(input_paths)}:duration=longest'

        command.extend(['-filter_complex', filter_complex, '-c:a', 'libmp3lame', '-q:a', '2', output_path])

        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')

        if result.returncode != 0:
            raise Exception(f"Merge failed: {result.stderr}")

        if progress_callback:
            progress_callback(1.0, "Merge complete")

        return output_path

    except Exception as e:
        raise

def apply_speed_pitch(input_path, speed=1.07, pitch_shift=1.03, progress_callback=None):
    """מחיל שינוי מהירות וpitch' - כמו בקוד המקורי"""
    try:
        if progress_callback:
            progress_callback(0.0, "Applying speed/pitch modifications...")

        output_path = os.path.join(OUTPUT_DIR, f"final_modified_{uuid.uuid4()}.mp3")

        filters = []
        if speed and speed != 1.0:
            filters.append(f"atempo={speed}")
        if pitch_shift and pitch_shift != 1.0:
            filters.append(f"asetrate=44100*{pitch_shift},aresample=44100")

        if not filters:
            shutil.copy(input_path, output_path)
            return output_path

        command = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-af", ",".join(filters),
            output_path
        ]

        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')

        if result.returncode != 0:
            raise Exception(f"Speed/pitch modification failed: {result.stderr}")

        if progress_callback:
            progress_callback(1.0, "Modifications applied")

        return output_path

    except Exception as e:
        raise

# ====== הפונקציה הראשית לעיבוד ======

def process_song(youtube_url, audio_file, heavy_processing, progress=gr.Progress()):
    """
    פונקציה ראשית לעיבוד שיר
    מיושמת בדיוק כמו runLocalChangesongForCover + שלבי העיבוד במקור
    """
    temp_files = []

    def update_progress(value, desc):
        """עדכון התקדמות"""
        progress(value, desc=desc)

    try:
        # שלב 1: קבלת קובץ האודיו המקורי
        progress(0.05, desc="Preparing file...")

        if youtube_url and youtube_url.strip():
            source_audio = download_youtube_audio(
                youtube_url.strip(),
                lambda p, d: update_progress(0.05 + p * 0.1, d)
            )
            temp_files.append(source_audio)
        elif audio_file is not None:
            source_audio = audio_file
        else:
            return None, "Please enter YouTube URL or upload audio file"

        if not os.path.exists(source_audio):
            return None, "Audio file not found"

        # בחירת פרמטרים לפי סוג העיבוד - כמו בקוד המקורי (שורות 1878-1897)
        if heavy_processing:
            model_name = 'האק'
            separation_model = 'bs_roformer_vocals_gabox.ckpt'  # Fallback #2
            processing_type = "Enhanced Processing"
        else:
            model_name = 'האק'
            separation_model = 'UVR_MDXNET_KARA_2.onnx'  # Default
            processing_type = "Regular Processing"

        progress(0.15, desc=f"Starting {processing_type}...")

        # שלב 2: הפרדת vocals מ-instrumental
        progress(0.2, desc="Separating vocals from instrumental...")
        separation_paths = run_separation(
            source_audio,
            model_filename=separation_model,
            vocals_keyword='vocals',
            instrumental_keyword='instrumental',
            progress_callback=lambda p, d: update_progress(0.2 + p * 0.3, d)
        )

        vocals_path = separation_paths['vocals_path']
        instrumental_path = separation_paths['instrumental_path']
        temp_files.extend([vocals_path, instrumental_path])

        # שלב 3: הכנת RVC Model
        progress(0.5, desc=f"Loading model {model_name}...")
        model_pth_path, model_pitch = prepare_model_files(model_name)

        # שלב 4: המרת ה-vocals עם RVC (pitch=0 כמו בקוד המקורי שורה 10531)
        progress(0.55, desc=f"Voice conversion with {model_name} model...")
        new_vocals_path = run_rvc_conversion(
            vocals_path,
            model_pth_path,
            pitch=0,
            progress_callback=lambda p, d: update_progress(0.55 + p * 0.2, d)
        )
        temp_files.append(new_vocals_path)

        # שלב 5: איחוד vocals חדש עם instrumental
        progress(0.75, desc="Merging new vocals with instrumental...")
        merged_path = os.path.join(OUTPUT_DIR, f"merged_{uuid.uuid4()}.mp3")
        merge_audio(
            [new_vocals_path, instrumental_path],
            merged_path,
            progress_callback=lambda p, d: update_progress(0.75 + p * 0.1, d)
        )
        temp_files.append(merged_path)

        # שלב 6: החלת שינוי מהירות וpitch' (כמו בשורות 10896-10898)
        progress(0.85, desc="Applying speed and pitch modifications...")
        final_output = apply_speed_pitch(
            merged_path,
            speed=1.07,
            pitch_shift=1.03,
            progress_callback=lambda p, d: update_progress(0.85 + p * 0.15, d)
        )

        progress(1.0, desc="Complete!")

        # חישוב גודל הקובץ
        file_size_mb = os.path.getsize(final_output) / (1024 * 1024)

        # ניקוי temp files (לא כולל הפלט הסופי)
        cleanup_count = 0
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file) and temp_file != final_output:
                    os.remove(temp_file)
                    cleanup_count += 1
            except Exception as e:
                print(f"⚠️ Cannot delete temp file: {temp_file} - {e}")


        success_msg = f"""Complete! Size: {file_size_mb:.2f} MB"""

        return final_output, success_msg

    except Exception as e:
        # ניקוי בשגיאה
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass

        error_msg = f"""Error: {str(e)}"""
        print(f"\n{error_msg}\n")
        return None, error_msg

# ====== יצירת ממשק Gradio ======

def create_interface():
    """יוצר את ממשק ה-Gradio"""

    # טעינת מודלים וקאש
    models_loaded = load_local_models_config()
    load_youtube_cache()

    # בדיקת זמינות כלים
    tools_status = []

    # בדיקת yt-dlp
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True)
        yt_dlp_version = result.stdout.strip()
        tools_status.append(f"✅ yt-dlp: {yt_dlp_version}")
    except:
        tools_status.append("❌ yt-dlp: לא מותקן")

    # בדיקת ffmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        ffmpeg_version = result.stdout.split('\n')[0].split('version')[1].split()[0]
        tools_status.append(f"✅ ffmpeg: {ffmpeg_version}")
    except:
        tools_status.append("❌ ffmpeg: לא מותקן")

    tools_status_text = "\n".join(tools_status)

    with gr.Blocks(
        title="RVC Song Processor",
        theme=gr.themes.Soft(primary_hue="purple", secondary_hue="blue")
    ) as demo:
        gr.Markdown("""
        # RVC Song Processor

        **Processing Steps:**
        1. Download from YouTube / Upload file
        2. Separate vocals from instrumental
        3. Voice conversion with RVC
        4. Merge new vocals + instrumental
        5. Speed x1.07 and pitch x1.03 modification
        """)

        if not models_loaded:
            gr.Warning("Models missing! Ensure local_models.json exists with Hack and Guitar models")

        with gr.Accordion("System Status", open=False):
            gr.Markdown(f"""
**Tools:**
```
{tools_status_text}
```

**Models:** {len(local_models)} | **Cache:** {len(youtube_audio_cache)} files
            """)

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Input")

                with gr.Tabs():
                    with gr.Tab("YouTube"):
                        youtube_url = gr.Textbox(
                            label="YouTube URL",
                            placeholder="https://www.youtube.com/watch?v=...",
                            lines=1
                        )
                    with gr.Tab("File"):
                        audio_file = gr.Audio(
                            label="Upload Audio File",
                            type="filepath"
                        )

                gr.Markdown("---")

                heavy_processing = gr.Checkbox(
                    label="Enhanced Processing",
                    value=False
                )

                process_btn = gr.Button(
                    "Process Song",
                    variant="primary",
                    size="lg"
                )

            with gr.Column(scale=1):
                gr.Markdown("### Output")

                output_audio = gr.Audio(
                    label="Processed Song",
                    type="filepath",
                    interactive=False
                )

                status_text = gr.Markdown(
                    value="Waiting for input...",
                    elem_classes=["status-box"]
                )

        gr.Markdown("""
        ---
        **Technical Details:**
        - Local processing on your machine
        - GPU with CUDA recommended for faster processing
        - Files cached for reuse
        """)

        # חיבור הכפתור לפונקציה
        process_btn.click(
            fn=process_song,
            inputs=[youtube_url, audio_file, heavy_processing],
            outputs=[output_audio, status_text]
        )

    return demo

# ====== הרצה ======

if __name__ == "__main__":
    print("="*60)
    print("RVC Song Processor")
    print("="*60)
    print()

    print("Loading configuration...")
    models_ok = load_local_models_config()
    load_youtube_cache()

    if not models_ok:
        print("WARNING: Models issue!")
        print("Ensure local_models.json exists with Hack and Guitar models")
        print()

    print("Starting interface...")
    print()

    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        favicon_path=None
    )
