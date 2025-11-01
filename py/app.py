#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flask backend for Suno Song Processor
"""

from flask import Flask, render_template, request, jsonify, send_file
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

def search_youtube(query):
    """מחפש שיר ביוטיוב ומחזיר 3 תוצאות ראשונות"""
    try:
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
            errors='replace'
        )

        if result.returncode != 0:
            raise Exception(f"Search failed: {result.stderr if result.stderr else 'Unknown error'}")

        if not result.stdout or not result.stdout.strip():
            raise Exception("No results found")

        lines = result.stdout.strip().split('\n')
        if len(lines) < 2:
            raise Exception("No results found")

        results = []
        for i in range(0, len(lines), 2):
            if i + 1 < len(lines):
                title = lines[i].strip()
                video_id = lines[i + 1].strip()
                if title and video_id:
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    results.append({
                        'title': title,
                        'url': url
                    })

        if not results:
            raise Exception("No valid results found")

        print(f"✅ Search results: {len(results)} videos found")
        return results

    except Exception as e:
        print(f"❌ Search error: {e}")
        raise

def prepare_model_files(model_name):
    """מכין את קבצי המודל (חילוץ מ-ZIP אם צריך)"""
    global local_models

    if model_name not in local_models:
        raise Exception(f"מודל '{model_name}' not found")

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

def download_youtube_audio(url):
    """מוריד אודיו מיוטיוב"""
    global youtube_audio_cache

    try:
        cmd_title = ['yt-dlp', '--get-title', '--extractor-args', 'youtube:player_client=android', url]
        result = subprocess.run(cmd_title, capture_output=True, text=True, encoding='utf-8', errors='replace')

        if result.returncode != 0:
            raise Exception(f"Failed to get video title: {result.stderr}")

        video_title = result.stdout.strip()
        safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title[:100]

        cached_path = os.path.join(MEDIA_CACHE_DIR, f"{safe_title}.mp3")

        if url in youtube_audio_cache and os.path.exists(youtube_audio_cache[url]):
            print(f"✅ [YouTube Audio Cache] HIT")
            return youtube_audio_cache[url], video_title

        if os.path.exists(cached_path):
            print(f"✅ [YouTube Audio Cache] HIT from disk")
            youtube_audio_cache[url] = cached_path
            save_youtube_cache()
            return cached_path, video_title

        print(f"[YouTube Cache] MISS. Starting download...")

        cookies_path = os.path.join(BASE_DIR, 'cookies.txt')

        cmd = [
            'yt-dlp',
            url,
            '-f', 'bestaudio[ext=m4a]/bestaudio/best',
            '-x',
            '--audio-format', 'mp3',
            '--audio-quality', '0',
            '--no-playlist',
            '--extractor-args', 'youtube:player_client=android',
            '-o', cached_path
        ]

        if os.path.exists(cookies_path):
            cmd.extend(['--cookies', cookies_path])

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
                print(f"[yt-dlp] {line}")

        return_code = process.wait()

        if return_code != 0:
            raise Exception(f"Download failed with code {return_code}")

        if not os.path.exists(cached_path):
            raise Exception("Downloaded file not found")

        youtube_audio_cache[url] = cached_path
        save_youtube_cache()

        print(f"✅ Downloaded and cached: {safe_title}.mp3")
        return cached_path, video_title

    except Exception as e:
        raise

def run_separation(input_path, model_filename='UVR_MDXNET_KARA_2.onnx',
                   vocals_keyword='vocals', instrumental_keyword='instrumental'):
    """מפריד vocals מ-instrumental"""
    try:
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

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                print(f"[Separation] {line}")
                output_lines.append(line)

                try:
                    paths = json.loads(line)
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

        if return_code != 0:
            raise Exception(f"Separation failed with code {return_code}")

        if paths_result is None:
            raise Exception("No result from separation script")

        return paths_result

    except Exception as e:
        raise

def run_rvc_conversion(input_path, model_pth_path, pitch):
    """מריץ המרת קול עם RVC"""
    try:
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

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                print(f"[RVC] {line}")
                output_lines.append(line)

        return_code = process.wait()

        if return_code != 0:
            raise Exception(f"RVC failed with code {return_code}")

        final_output_path = output_lines[-1].strip() if output_lines else output_path
        if not os.path.exists(final_output_path):
            raise Exception("RVC did not create valid output file")

        return final_output_path

    except Exception as e:
        raise

def merge_audio(input_paths, output_path):
    """מאחד מספר קבצי אודיו"""
    try:
        command = ['ffmpeg', '-y']

        for path in input_paths:
            command.extend(['-i', path])

        amix_inputs = ''.join([f'[{i}:a]' for i in range(len(input_paths))])
        filter_complex = f'{amix_inputs}amix=inputs={len(input_paths)}:duration=longest'

        command.extend(['-filter_complex', filter_complex, '-c:a', 'libmp3lame', '-q:a', '2', output_path])

        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')

        if result.returncode != 0:
            raise Exception(f"Merge failed: {result.stderr}")

        return output_path

    except Exception as e:
        raise

def apply_speed_pitch(input_path, speed=1.07, pitch_shift=1.03):
    """מחיל שינוי מהירות ופיץ'"""
    try:
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

        return output_path

    except Exception as e:
        raise

def process_song(youtube_url, heavy_processing=False):
    """פונקציה ראשית לעיבוד שיר"""
    temp_files = []
    video_title = None

    try:
        print("Processing...")

        # שלב 1: הורדת אודיו
        source_audio, video_title = download_youtube_audio(youtube_url)

        # בחירת פרמטרים
        if heavy_processing:
            model_name = 'האק'
            separation_model = 'bs_roformer_vocals_gabox.ckpt'
        else:
            model_name = 'האק'
            separation_model = 'UVR_MDXNET_KARA_2.onnx'

        # שלב 2: הפרדת vocals מ-instrumental
        print("Processing audio...")
        separation_paths = run_separation(
            source_audio,
            model_filename=separation_model,
            vocals_keyword='vocals',
            instrumental_keyword='instrumental'
        )

        vocals_path = separation_paths['vocals_path']
        instrumental_path = separation_paths['instrumental_path']
        temp_files.extend([vocals_path, instrumental_path])

        # שלב 3: הכנת RVC Model
        print("Loading model...")
        model_pth_path, model_pitch = prepare_model_files(model_name)

        # שלב 4: המרת ה-vocals עם RVC
        print("Processing vocals...")
        new_vocals_path = run_rvc_conversion(
            vocals_path,
            model_pth_path,
            pitch=0
        )
        temp_files.append(new_vocals_path)

        # שלב 5: איחוד vocals חדש עם instrumental
        print("Merging audio...")
        merged_path = os.path.join(OUTPUT_DIR, f"merged_{uuid.uuid4()}.mp3")
        merge_audio(
            [new_vocals_path, instrumental_path],
            merged_path
        )
        temp_files.append(merged_path)

        # שלב 6: החלת שינוי מהירות ופיץ'
        print("Applying modifications...")
        temp_output = apply_speed_pitch(
            merged_path,
            speed=1.07,
            pitch_shift=1.03
        )

        # Rename using video title
        if video_title:
            safe_name = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = f"{safe_name} - processed"
            final_output = os.path.join(OUTPUT_DIR, f"{safe_name}.mp3")
            shutil.move(temp_output, final_output)
        else:
            final_output = temp_output

        # ניקוי temp files והתיקיות
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file) and temp_file != final_output:
                    os.remove(temp_file)
            except Exception as e:
                print(f"⚠️ Cannot delete temp file: {temp_file} - {e}")

        # ניקוי תיקיות ריקות ב-separation_outputs
        try:
            for folder in os.listdir(SEPARATION_OUTPUT_DIR):
                folder_path = os.path.join(SEPARATION_OUTPUT_DIR, folder)
                if os.path.isdir(folder_path):
                    try:
                        # מחיקת התיקייה אם היא ריקה
                        if not os.listdir(folder_path):
                            os.rmdir(folder_path)
                        else:
                            # מחיקת כל הקבצים בתיקייה ואז את התיקייה
                            shutil.rmtree(folder_path)
                    except Exception as e:
                        print(f"⚠️ Cannot delete folder: {folder_path} - {e}")
        except Exception as e:
            print(f"⚠️ Cannot clean separation folders: {e}")

        print("✅ Complete!")

        return final_output, video_title

    except Exception as e:
        # ניקוי בשגיאה
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass

        print(f"\n❌ Error: {str(e)}\n")
        raise

# Initialize Flask
app = Flask(__name__,
            template_folder='.',
            static_folder='.',
            static_url_path='')

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/api/search', methods=['POST'])
def api_search():
    try:
        data = request.json
        query = data.get('query', '').strip()

        if not query:
            return jsonify({'error': 'No query provided'}), 400

        results = search_youtube(query)
        return jsonify({'results': results})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system-info', methods=['GET'])
def api_system_info():
    try:
        # Check yt-dlp
        try:
            result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, encoding='utf-8', errors='replace')
            yt_dlp_version = result.stdout.strip()
            yt_dlp_status = f"✅ {yt_dlp_version}"
        except:
            yt_dlp_status = "❌ Not installed"

        # Check ffmpeg
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, encoding='utf-8', errors='replace')
            ffmpeg_version = result.stdout.split('\n')[0].split('version')[1].split()[0]
            ffmpeg_status = f"✅ {ffmpeg_version}"
        except:
            ffmpeg_status = "❌ Not installed"

        return jsonify({
            'yt_dlp': yt_dlp_status,
            'ffmpeg': ffmpeg_status,
            'models': len(local_models),
            'cached_files': len(youtube_audio_cache)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-cache', methods=['POST'])
def api_clear_cache():
    try:
        global youtube_audio_cache
        if os.path.exists(MEDIA_CACHE_DIR):
            for file in os.listdir(MEDIA_CACHE_DIR):
                file_path = os.path.join(MEDIA_CACHE_DIR, file)
                try:
                    os.remove(file_path)
                except:
                    pass
        youtube_audio_cache = {}
        if os.path.exists(YOUTUBE_AUDIO_CACHE_PATH):
            os.remove(YOUTUBE_AUDIO_CACHE_PATH)
        save_youtube_cache()
        return jsonify({'success': True, 'message': 'Cache cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process', methods=['POST'])
def api_process():
    """API endpoint for processing songs - FULL PIPELINE"""
    try:
        data = request.json
        youtube_url = data.get('youtube_url', '')
        enhanced = data.get('enhanced', False)

        if not youtube_url:
            return jsonify({'error': 'No input provided'}), 400

        # Run full processing pipeline
        final_output, title = process_song(youtube_url, heavy_processing=enhanced)

        # Return relative path for web serving
        relative_path = os.path.relpath(final_output, BASE_DIR)

        return jsonify({
            'success': True,
            'audio_path': '/' + relative_path.replace('\\', '/'),
            'title': f"{title} - processed" if title else 'Processed Song',
            'message': 'Complete!'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    import logging

    # Disable Flask logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    print("="*60)
    print("Suno Song Processor - Flask Backend")
    print("="*60)
    print()

    print("Loading configuration...")
    models_ok = load_local_models_config()
    load_youtube_cache()

    if not models_ok:
        print("WARNING: Models issue!")
        print()

    print("Starting server...")
    print("Open: http://localhost:7860")
    print()

    app.run(host='0.0.0.0', port=7860, debug=False, use_reloader=False)
