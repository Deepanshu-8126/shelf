import os
import subprocess
import time

import yt_dlp

from shortGPT.audio.audio_duration import get_asset_duration

CONST_CHARS_PER_SEC = 20.5  # Arrived to this result after whispering a ton of shorts and calculating the average number of characters per second of speech.

WHISPER_MODEL = None



def downloadYoutubeAudio(url, outputFile):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "no_color": True,
        "no_call_home": True,
        "no_check_certificate": True,
        "format": "bestaudio/best", 
        "outtmpl": outputFile
    }

    attempts = 0
    max_attempts = 4
    while attempts < max_attempts:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                dictMeta = ydl.extract_info(
                    url,
                    download=True)
                if (not os.path.exists(outputFile)):
                    raise Exception("Audio Download Failed")
                return outputFile, dictMeta['duration']
        except Exception as e:
            attempts += 1
            if attempts == max_attempts:
                print(f"⚠️ YouTube blocked yt-dlp audio download: {e}. Falling back to local/synthetic audio.", flush=True)
                local_fallback = os.path.abspath("public/Music dj quads.wav")
                if os.path.exists(local_fallback):
                    import shutil
                    os.makedirs(os.path.dirname(os.path.abspath(outputFile)), exist_ok=True)
                    shutil.copyfile(local_fallback, outputFile)
                    return outputFile, 60
                os.makedirs(os.path.dirname(os.path.abspath(outputFile)), exist_ok=True)
                subprocess.run([
                    'ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
                    '-t', '60', '-q:a', '9', outputFile
                ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return outputFile, 60
            time.sleep(1)
            continue
    return None

def speedUpAudio(tempAudioPath, outputFile, expected_duration=None):
    tempAudioPath, duration = get_asset_duration(tempAudioPath, False)
    if not expected_duration:
        if (duration > 57):
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', tempAudioPath, '-af', f'atempo={(duration/57):.5f}', outputFile])
        else:
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', tempAudioPath, outputFile])
    else:
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', tempAudioPath, '-af', f'atempo={(duration/expected_duration):.5f}', outputFile])
    if (os.path.exists(outputFile)):
        return outputFile

def ChunkForAudio(alltext, chunk_size=2500):
    alltext_list = alltext.split('.')
    chunks = []
    curr_chunk = ''
    for text in alltext_list:
        if len(curr_chunk) + len(text) <= chunk_size:
            curr_chunk += text + '.'
        else:
            chunks.append(curr_chunk)
            curr_chunk = text + '.'
    if curr_chunk:
        chunks.append(curr_chunk)
    return chunks


def audioToText(filename, model_size="base"):
    global WHISPER_MODEL
    try:
        from whisper_timestamped import load_model, transcribe_timestamped
        if (WHISPER_MODEL == None):
            WHISPER_MODEL = load_model(model_size)
        gen = transcribe_timestamped(WHISPER_MODEL, filename, verbose=False, fp16=False)
        return gen
    except Exception as e:
        print(f"⚠️ Falling back to standard whisper: {e}", flush=True)
        import whisper
        if WHISPER_MODEL is None:
            WHISPER_MODEL = whisper.load_model(model_size)
        gen = WHISPER_MODEL.transcribe(filename, verbose=False, fp16=False, word_timestamps=True)
        return gen


def getWordsPerSec(filename):
    a = audioToText(filename)
    return len(a['text'].split()) / a['segments'][-1]['end']


def getCharactersPerSec(filename):
    a = audioToText(filename)
    return len(a['text']) / a['segments'][-1]['end']

def run_background_audio_split(sound_file_path):
    try:
        # Run spleeter command
        # Get absolute path of sound file 
        output_dir = os.path.dirname(sound_file_path)
        command = f"spleeter separate -p spleeter:2stems -o '{output_dir}' '{sound_file_path}'"

        process = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # If spleeter runs successfully, return the path to the background music file
        if process.returncode == 0:
            return os.path.join(output_dir, sound_file_path.split("/")[-1].split(".")[0], "accompaniment.wav")
        else:
            return None
    except Exception:
        # If spleeter crashes, return None
        return None
