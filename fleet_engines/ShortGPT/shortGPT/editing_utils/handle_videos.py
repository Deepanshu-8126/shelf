import os
import random
import yt_dlp
import subprocess
import json

def getYoutubeVideoLink(url):
    format_filter = "[height<=1920]" if 'shorts' in url else "[height<=1080]"
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "no_color": True,
        "no_call_home": True,
        "no_check_certificate": True,
        # Look for m3u8 formats first, then fall back to regular formats
        "format": f"bestvideo[ext=m3u8]{format_filter}/bestvideo{format_filter}"
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            dictMeta = ydl.extract_info(
                url,
                download=False)
            return dictMeta['url'], dictMeta['duration']
    except Exception as e:
        raise Exception(f"Failed getting video link from the following video/url {url} {e.args[0]}")

def extract_random_clip_from_video(video_url, video_duration, clip_duration, output_file):
    """Extracts a clip from a video using a signed URL or local path."""
    if not video_duration:
        video_duration = 90
    
    # Calculate a valid random start time without arbitrary restrictions
    if float(video_duration) > float(clip_duration):
        max_start = max(0.0, float(video_duration) - float(clip_duration) - 2.0)
        start_time = random.uniform(0.0, max_start)
    else:
        start_time = 0.0
    
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    command = [
        'ffmpeg',
        '-y',
        '-loglevel', 'error',
        '-ss', str(round(start_time, 2)),
        '-t', str(round(clip_duration, 2)),
        '-i', str(video_url),
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        str(output_file)
    ]
    
    subprocess.run(command, check=True)
    
    if not os.path.exists(output_file):
        raise Exception("Random clip failed to be written")
    return output_file


def get_aspect_ratio(video_file):
    cmd = 'ffprobe -i "{}" -v quiet -print_format json -show_format -show_streams'.format(video_file)
#     jsonstr = subprocess.getoutput(cmd)
    jsonstr = subprocess.check_output(cmd, shell=True, encoding='utf-8')
    r = json.loads(jsonstr)
    # look for "codec_type": "video". take the 1st one if there are mulitple
    video_stream_info = [x for x in r['streams'] if x['codec_type']=='video'][0]
    if 'display_aspect_ratio' in video_stream_info and video_stream_info['display_aspect_ratio']!="0:1":
        a,b = video_stream_info['display_aspect_ratio'].split(':')
        dar = int(a)/int(b)
    else:
        # some video do not have the info of 'display_aspect_ratio'
        w,h = video_stream_info['width'], video_stream_info['height']
        dar = int(w)/int(h)
        ## not sure if we should use this
        #cw,ch = video_stream_info['coded_width'], video_stream_info['coded_height']
        #sar = int(cw)/int(ch)
    if 'sample_aspect_ratio' in video_stream_info and video_stream_info['sample_aspect_ratio']!="0:1":
        # some video do not have the info of 'sample_aspect_ratio'
        a,b = video_stream_info['sample_aspect_ratio'].split(':')
        sar = int(a)/int(b)
    else:
        sar = dar
    par = dar/sar
    return dar