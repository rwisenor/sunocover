# your_separation_script.py
import argparse
import os
import sys
import json
import ctypes

def load_cudnn_dlls():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cudnn_dir = os.path.join(current_dir, 'venv', 'lib', 'site-packages', 'onnxruntime', 'capi')
        dlls = ['cudnn64_9.dll', 'cudnn_adv64_9.dll', 'cudnn_cnn64_9.dll', 'cudnn_ops64_9.dll', 'cudnn_graph64_9.dll']
        nvidia_cudnn_dir = r'C:\Program Files\NVIDIA\CUDNN\v9.4\bin\12.6'
        if os.path.exists(nvidia_cudnn_dir):
            for dll in dlls:
                dst_path = os.path.join(cudnn_dir, dll)
                src_path = os.path.join(nvidia_cudnn_dir, dll)
                if os.path.exists(src_path) and not os.path.exists(dst_path):
                    try:
                        import shutil
                        shutil.copy2(src_path, dst_path)
                    except:
                        pass
        loaded_count = 0
        for dll in dlls:
            dll_path = os.path.join(cudnn_dir, dll)
            if os.path.exists(dll_path):
                try:
                    ctypes.CDLL(dll_path)
                    loaded_count += 1
                except:
                    pass
        return loaded_count > 0
    except:
        return False

load_cudnn_dlls()
from audio_separator.separator import Separator

def process_separation(input_path, output_dir, model_filename, vocals_keyword='vocals', instrumental_keyword='instrumental'):
    try:
        separator = Separator(output_dir=output_dir)
        separator.load_model(model_filename=model_filename)
        output_files = separator.separate(input_path)

        # output_files are in output_dir, make sure they have full paths
        full_paths = []
        for f in output_files:
            if os.path.isabs(f):
                full_paths.append(f)
            else:
                # File is in output_dir
                full_path = os.path.join(output_dir, f)
                if not os.path.exists(full_path):
                    # Try with basename only
                    full_path = os.path.join(output_dir, os.path.basename(f))
                full_paths.append(full_path)

        result = {}

        if 'bs_roformer_male_female_by_aufr33_sdr_7.2889' in model_filename:
            male_vocals_path = next((f for f in full_paths if '(male)' in os.path.basename(f).lower()), None)
            female_vocals_path = next((f for f in full_paths if '(female)' in os.path.basename(f).lower()), None)
            if not male_vocals_path or not female_vocals_path:
                raise Exception("Failed to find male/female vocals")
            result = {"male_vocals_path": male_vocals_path, "female_vocals_path": female_vocals_path}
        else:
            vocals_keywords = [k.strip().lower() for k in vocals_keyword.split(',')]
            instrumental_keywords = [k.strip().lower() for k in instrumental_keyword.split(',')]

            vocals_path = None
            for keyword in vocals_keywords:
                # Search for keyword in parentheses to avoid matching model name
                vocals_path = next((f for f in full_paths if f"({keyword})" in os.path.basename(f).lower()), None)
                if not vocals_path:
                    # Fallback to regular search if not found in parentheses
                    vocals_path = next((f for f in full_paths if keyword in os.path.basename(f).lower()), None)
                if vocals_path:
                    break

            instrumental_path = None
            for keyword in instrumental_keywords:
                # Search for keyword in parentheses to avoid matching model name
                instrumental_path = next((f for f in full_paths if f"({keyword})" in os.path.basename(f).lower()), None)
                if not instrumental_path:
                    # Fallback to regular search if not found in parentheses
                    instrumental_path = next((f for f in full_paths if keyword in os.path.basename(f).lower()), None)
                if instrumental_path:
                    break

            if not vocals_path or not instrumental_path:
                raise Exception("Failed to find vocals/instrumental files")

            result = {"vocals_path": vocals_path, "instrumental_path": instrumental_path}

        print(json.dumps(result))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", type=str, required=True)
    parser.add_argument("--output_dir", type=str, required=True)
    parser.add_argument("--model_filename", type=str, default='UVR_MDXNET_KARA_2.onnx')
    parser.add_argument("--vocals_keyword", type=str, default='vocals')
    parser.add_argument("--instrumental_keyword", type=str, default='instrumental')
    args = parser.parse_args()

    try:
        process_separation(args.input_path, args.output_dir, args.model_filename, args.vocals_keyword, args.instrumental_keyword)
    except Exception as e:
        sys.exit(1)
