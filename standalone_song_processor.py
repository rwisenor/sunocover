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

def search_youtube(query, progress_callback=None):
    """
    מחפש שיר ביוטיוב ומחזיר 3 תוצאות ראשונות
    """
    try:
        if progress_callback:
            progress_callback(0.1, f"Searching YouTube for: {query}")

        # חיפוש ביוטיוב - ytsearch3 מחזיר 3 תוצאות
        cmd = [
            'yt-dlp',
            '--get-id',
            '--get-title',
            '--no-playlist',
            '--extractor-args', 'youtube:player_client=android',
            f'ytsearch3:{query}'
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'  # Replace invalid UTF-8 chars
        )

        if result.returncode != 0:
            raise Exception(f"Search failed: {result.stderr if result.stderr else 'Unknown error'}")

        if not result.stdout or not result.stdout.strip():
            raise Exception("No results found")

        lines = result.stdout.strip().split('\n')
        if len(lines) < 2:
            raise Exception("No results found")

        # Parse results - format is: title\nid\ntitle\nid\n...
        results = []
        for i in range(0, len(lines), 2):
            if i + 1 < len(lines):
                title = lines[i].strip()
                video_id = lines[i + 1].strip()
                if title and video_id:
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    results.append({
                        'title': title,
                        'url': url,
                        'display': f"{title}"
                    })

        if not results:
            raise Exception("No valid results found")

        if progress_callback:
            progress_callback(1.0, f"Found {len(results)} results")

        print(f"✅ Search results: {len(results)} videos found")
        return results

    except Exception as e:
        print(f"❌ Search error: {e}")
        raise

def download_youtube_audio(url, progress_callback=None):
    """
    מוריד אודיו מיוטיוב - בדיוק כמו בקוד המקורי
    משתמש במערכת קאש עם שמות נורמליים
    """
    global youtube_audio_cache

    try:
        # קודם כל, נחלץ את ה-title של הוידאו
        if progress_callback:
            progress_callback(0.05, "Getting video info...")

        # חילוץ title
        cmd_title = ['yt-dlp', '--get-title', '--extractor-args', 'youtube:player_client=android', url]
        result = subprocess.run(cmd_title, capture_output=True, text=True, encoding='utf-8', errors='replace')

        if result.returncode != 0:
            raise Exception(f"Failed to get video title: {result.stderr}")

        video_title = result.stdout.strip()
        # ניקוי שם הקובץ - הסרת תווים לא חוקיים
        safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title[:100]  # הגבלת אורך

        cached_path = os.path.join(MEDIA_CACHE_DIR, f"{safe_title}.mp3")

        # קאש HIT מהזיכרון
        if url in youtube_audio_cache and os.path.exists(youtube_audio_cache[url]):
            print(f"✅ [YouTube Audio Cache] HIT: Found existing audio file for {url}")
            if progress_callback:
                progress_callback(1.0, "Found in cache!")
            return youtube_audio_cache[url], video_title

        # קאש HIT מהדיסק
        if os.path.exists(cached_path):
            print(f"✅ [YouTube Audio Cache] HIT: Found existing audio file on disk: {safe_title}.mp3")
            youtube_audio_cache[url] = cached_path
            save_youtube_cache()
            if progress_callback:
                progress_callback(1.0, "Found in cache!")
            return cached_path, video_title

        print(f"[YouTube Cache] MISS: No valid cached file found for {url}. Starting download...")

        if progress_callback:
            progress_callback(0.1, "Downloading from YouTube...")

        # בדיקה אם יש cookies.txt (כמו בקוד המקורי)
        cookies_path = os.path.join(BASE_DIR, 'cookies.txt')

        # פקודת yt-dlp - איכות מקסימלית, ללא thumbnail
        cmd = [
            'yt-dlp',
            url,
            '-f', 'bestaudio[ext=m4a]/bestaudio/best',
            '-x',  # חילוץ אודיו
            '--audio-format', 'mp3',
            '--audio-quality', '0',  # איכות מקסימלית
            '--no-playlist',
            '--extractor-args', 'youtube:player_client=android',
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
            errors='replace',
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

        print(f"✅ Downloaded and cached: {safe_title}.mp3")
        return cached_path, video_title

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
            errors='replace',
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
            progress_callback(0.0, "Processing vocals...")

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
            errors='replace',
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
                                progress_callback(percent / 100, f"Processing... {percent:.0f}%")
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
            progress_callback(1.0, "Processing complete")

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

        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')

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

        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')

        if result.returncode != 0:
            raise Exception(f"Speed/pitch modification failed: {result.stderr}")

        if progress_callback:
            progress_callback(1.0, "Modifications applied")

        return output_path

    except Exception as e:
        raise

# ====== פונקציות עזר ======

def clear_youtube_cache():
    """Clears YouTube cache files and JSON"""
    try:
        global youtube_audio_cache
        # Delete cache files
        if os.path.exists(MEDIA_CACHE_DIR):
            for file in os.listdir(MEDIA_CACHE_DIR):
                file_path = os.path.join(MEDIA_CACHE_DIR, file)
                try:
                    os.remove(file_path)
                except:
                    pass
        # Clear cache dict
        youtube_audio_cache = {}
        # Save empty cache
        if os.path.exists(YOUTUBE_AUDIO_CACHE_PATH):
            os.remove(YOUTUBE_AUDIO_CACHE_PATH)
        save_youtube_cache()
        return "YouTube cache cleared"
    except Exception as e:
        return f"Error: {e}"

# ====== הפונקציה הראשית לעיבוד ======

def process_song(youtube_url, search_query, search_result, audio_file, heavy_processing, progress=gr.Progress()):
    """
    פונקציה ראשית לעיבוד שיר
    מיושמת בדיוק כמו runLocalChangesongForCover + שלבי העיבוד במקור
    """
    temp_files = []
    video_title = None

    def update_progress(value, desc):
        """עדכון התקדמות"""
        progress(value, desc=desc)

    try:
        # שלב 1: קבלת קובץ האודיו המקורי
        progress(0.05, desc="Preparing...")

        # אם נבחרה תוצאת חיפוש
        if search_result and search_result not in ["Results", "Click Search button first", "No results found", "Search failed - try again"]:
            # search_result הוא URL
            youtube_url = search_result

        if youtube_url and youtube_url.strip():
            source_audio, video_title = download_youtube_audio(
                youtube_url.strip(),
                lambda p, d: update_progress(0.1 + p * 0.1, d)
            )
            # Don't add to temp_files - keep YouTube cache
        elif audio_file is not None:
            source_audio = audio_file
            video_title = None
        else:
            return None, "Please provide a song (search, URL, or upload file)"

        if not os.path.exists(source_audio):
            return None, "Audio file not found"

        # בחירת פרמטרים לפי סוג העיבוד - כמו בקוד המקורי (שורות 1878-1897)
        if heavy_processing:
            model_name = 'האק'
            separation_model = 'bs_roformer_vocals_gabox.ckpt'  # Fallback #2
            processing_type = "Enhanced Processing - Check this ONLY if the first try blocked by suno"
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
        progress(0.55, desc=f"Processing with {model_name}...")
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

        # שלב 6: החלת שינוי מהירות ופיץ' (כמו בשורות 10896-10898)
        progress(0.85, desc="Applying speed and pitch modifications...")
        temp_output = apply_speed_pitch(
            merged_path,
            speed=1.07,
            pitch_shift=1.03,
            progress_callback=lambda p, d: update_progress(0.85 + p * 0.15, d)
        )

        # Rename using video title
        if video_title:
            # שימוש בשם השיר מיוטיוב
            safe_name = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = f"{safe_name} - processed"
            final_output = os.path.join(OUTPUT_DIR, f"{safe_name}.mp3")
            shutil.move(temp_output, final_output)
        else:
            final_output = temp_output

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
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, encoding='utf-8', errors='replace')
        yt_dlp_version = result.stdout.strip()
        tools_status.append(f"✅ yt-dlp: {yt_dlp_version}")
    except:
        tools_status.append("❌ yt-dlp: Not installed")

    # בדיקת ffmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, encoding='utf-8', errors='replace')
        ffmpeg_version = result.stdout.split('\n')[0].split('version')[1].split()[0]
        tools_status.append(f"✅ ffmpeg: {ffmpeg_version}")
    except:
        tools_status.append("❌ ffmpeg: Not installed")

    tools_status_text = "\n".join(tools_status)

    # Custom CSS
    custom_css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

        * {
            font-family: 'Inter', sans-serif !important;
        }

        .gradio-container {
            max-width: none !important;
            width: 100% !important;
            margin: 0 !important;
            padding: 15px 40px !important;
        }

        .main.svelte-1cl284s {
            max-width: none !important;
            width: 100% !important;
            margin: 0 !important;
        }

        .header-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            text-align: center;
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
            width: 100% !important;
        }

        .header-section h1 {
            color: white;
            font-size: 28px;
            font-weight: 700;
            margin: 0 0 6px 0;
            text-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }

        .header-section p {
            color: rgba(255,255,255,0.95);
            font-size: 14px;
            margin: 0;
            font-weight: 400;
        }


        .section-title {
            font-size: 20px;
            font-weight: 700;
            color: #2d3748;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .section-icon {
            font-size: 22px;
        }

        /* Remove gaps in output section */
        .output-section audio {
            margin-top: 0 !important;
        }

        .status-box {
            background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-size: 15px;
            font-weight: 600;
            color: #2d3748;
            margin-top: 15px;
            box-shadow: 0 4px 15px rgba(132, 250, 176, 0.3);
        }

        .feature-box {
            background: #f7fafc;
            border-left: 4px solid #667eea;
            padding: 12px 16px;
            margin: 10px 0;
            border-radius: 8px;
            font-size: 14px;
        }

        .feature-box strong {
            color: #667eea;
            font-weight: 600;
        }

        .gradio-container .wrap {
            gap: 6px !important;
        }

        .tabs {
            gap: 0 !important;
        }

        /* Hide duplicate progress bars */
        .progress-text {
            display: none !important;
        }

        .wrap.svelte-1cl284s {
            gap: 6px !important;
        }

        /* Make columns wider and responsive */
        .col {
            min-width: 0 !important;
            flex: 1 !important;
        }

        /* Expand rows to full width */
        .row {
            width: 100% !important;
            gap: 30px !important;
        }

        /* Dropdown styling */
        select, .dropdown {
            font-size: 14px !important;
            width: 100% !important;
        }

        /* Audio player full width */
        audio {
            width: 100% !important;
        }

        /* Full width form elements */
        .form {
            width: 100% !important;
        }

        .block {
            width: 100% !important;
        }

        button.primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            border: none !important;
            font-weight: 700 !important;
            font-size: 18px !important;
            padding: 18px 40px !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
            margin: 0 !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        }

        button.primary:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 30px rgba(102, 126, 234, 0.5) !important;
        }

        button.primary:active {
            transform: translateY(0px) !important;
        }

        .tab-nav button {
            font-weight: 600 !important;
            font-size: 15px !important;
        }

        .info-panel {
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            padding: 15px;
            border-radius: 10px;
            margin-top: 0;
        }

        .info-panel h3 {
            color: #d35400;
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .info-item {
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 5px 0;
            color: #2d3748;
            font-size: 14px;
        }


        input[type="text"], textarea {
            border-radius: 8px !important;
            border: 2px solid #e2e8f0 !important;
            font-size: 15px !important;
            width: 100% !important;
        }

        input[type="text"]:focus, textarea:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        }

        .tabs {
            margin-bottom: 0 !important;
        }

        .tab-nav {
            border-radius: 10px 10px 0 0 !important;
            overflow: hidden;
        }

    </style>
    """

    with gr.Blocks(
        title="🎵 Suno Song Processor",
        theme=gr.themes.Soft(
            primary_hue="purple",
            secondary_hue="blue",
            neutral_hue="slate",
            font=["Inter", "sans-serif"]
        ),
        css=custom_css
    ) as demo:

        # Header
        gr.HTML("""
        <div class="header-section">
            <h1>🎵 Suno Song Processor</h1>
            <p>Process any song to bypass Suno copyright detection • By PresidentPikachu</p>
        </div>
        """)

        if not models_loaded:
            gr.Warning("⚠️ Models missing! Ensure local_models.json exists with required models")

        # Main Processing Area
        with gr.Row(equal_height=False):
            # Input Column
            with gr.Column(scale=1):
                gr.HTML('<div class="section-title"><span class="section-icon">📥</span> Input Source</div>')

                with gr.Tabs() as input_tabs:
                    with gr.Tab("🔍 Search Song"):
                        search_query = gr.Textbox(
                            label="",
                            placeholder="Search song on YouTube (e.g. Bohemian Rhapsody Queen)",
                            lines=1,
                            max_lines=1,
                            show_label=False
                        )
                        search_btn = gr.Button("🔍 Search YouTube", size="sm", variant="secondary")
                        search_result = gr.Dropdown(
                            label="Select Result (choose from 3 options)",
                            choices=["Results"],
                            value="Results",
                            interactive=True,
                            container=True
                        )

                    with gr.Tab("🎬 YouTube URL"):
                        youtube_url = gr.Textbox(
                            label="",
                            placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                            lines=1,
                            max_lines=1,
                            show_label=False
                        )

                    with gr.Tab("📁 Upload File"):
                        audio_file = gr.Audio(
                            label="",
                            type="filepath",
                            show_label=False
                        )

                gr.HTML('<div style="margin: 8px 0;"></div>')

                process_btn = gr.Button(
                    "🚀 Process Song",
                    variant="primary",
                    size="lg",
                    elem_classes="primary"
                )

                gr.HTML('<div style="margin: 8px 0;"></div>')

                heavy_processing = gr.Checkbox(
                    label="⚡ Enhanced Processing (use only if regular fails)",
                    value=False
                )

                gr.HTML('<div style="margin: 15px 0;"></div>')

                # Info Panel
                gr.HTML("""
                <div class="info-panel">
                    <h3>ℹ️ How to Use</h3>
                    <div class="info-item">
                        <strong>1.</strong> Enter song name or YouTube link
                    </div>
                    <div class="info-item">
                        <strong>2.</strong> Click Process Song
                    </div>
                    <div class="info-item">
                        <strong>3.</strong> Download and upload to Suno
                    </div>
                </div>
                """)

            # Output Column
            with gr.Column(scale=1, elem_classes="output-section"):
                gr.HTML('<div class="section-title"><span class="section-icon">🎧</span> Output</div>')

                output_audio = gr.Audio(
                    label="",
                    type="filepath",
                    interactive=False,
                    show_label=False,
                    container=False
                )

                status_text = gr.HTML(
                    value='<div class="status-box">Waiting for input...</div>'
                )

                output_filename = gr.Textbox(visible=False)

        # System Status Accordion
        with gr.Accordion("🔧 System Status & Tools", open=False):
            gr.Markdown(f"""
### 🛠️ Installed Tools
```
{tools_status_text}
```

### 📊 Statistics
- **Models Available:** {len(local_models)}
- **Cached YouTube Files:** {len(youtube_audio_cache)}
- **Processing Mode:** GPU Accelerated (CUDA) if available
            """)

            with gr.Row():
                clear_cache_btn = gr.Button("🗑️ Clear YouTube Cache", variant="secondary", size="sm")
                cache_status = gr.Textbox(label="Cache Status", lines=1, interactive=False, show_label=False)

        # Footer
        gr.HTML("""
        <div class="feature-box">
            <strong>💡 Tip:</strong>
            Use Search to find any song instantly. Only enable Enhanced Mode if regular processing doesn't work.
        </div>
        """)

        gr.Markdown("""
        ---
        <div style="text-align: center; color: #718096; font-size: 14px; padding: 20px;">
            <strong>Suno Song Processor</strong> • Made by PresidentPikachu<br>
            Bypass copyright detection • Upload any song to Suno
        </div>
        """)

        # Event Handlers
        # Global storage for search results (mapping display -> URL)
        search_results_map = {}

        def handle_search(query):
            """טיפול בחיפוש - מחזיר רשימת אפשרויות"""
            nonlocal search_results_map

            if not query or not query.strip():
                search_results_map = {}
                return gr.Dropdown(
                    choices=["Results"],
                    value="Results",
                    label="Select Result"
                )

            try:
                results = search_youtube(query.strip())
                if not results:
                    search_results_map = {}
                    return gr.Dropdown(
                        choices=["No results found"],
                        value="No results found",
                        label="Select Result"
                    )

                # שמירת mapping: display -> URL
                search_results_map = {}
                display_choices = []
                for r in results:
                    display = r['display']
                    search_results_map[display] = r['url']
                    display_choices.append(display)

                return gr.Dropdown(
                    choices=display_choices,
                    value=display_choices[0] if display_choices else "No results found",
                    label="Select Result"
                )
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Search error: {error_msg}")
                search_results_map = {}
                return gr.Dropdown(
                    choices=["Search failed - try again"],
                    value="Search failed - try again",
                    label="Select Result"
                )

        def process_with_status_update(youtube_url, search_query, search_result_display, audio_file, heavy_processing):
            nonlocal search_results_map

            # המרת הבחירה ל-URL
            actual_search_result = ""
            if search_result_display and search_result_display not in ["Results", "Click Search button first", "No results found", "Search failed - try again"]:
                if search_result_display in search_results_map:
                    actual_search_result = search_results_map[search_result_display]

            result_audio, result_msg = process_song(
                youtube_url, search_query, actual_search_result, audio_file, heavy_processing
            )

            if result_audio:
                status_html = f'<div class="status-box" style="background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);">✅ {result_msg}</div>'
            else:
                status_html = f'<div class="status-box" style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);">❌ {result_msg}</div>'

            return result_audio, status_html

        # חיבור כפתור החיפוש
        search_btn.click(
            fn=handle_search,
            inputs=[search_query],
            outputs=[search_result]
        )

        # חיבור כפתור Process
        process_btn.click(
            fn=process_with_status_update,
            inputs=[youtube_url, search_query, search_result, audio_file, heavy_processing],
            outputs=[output_audio, status_text]
        )

        clear_cache_btn.click(
            fn=clear_youtube_cache,
            outputs=[cache_status]
        )

    return demo

# ====== הרצה ======

if __name__ == "__main__":
    print("="*60)
    print("Suno Song Processor - By PresidentPikachu")
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
