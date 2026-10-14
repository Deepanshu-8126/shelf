import subprocess, os
ass_txt = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: MrBeast,Impact,78,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,8,2,2,60,60,260,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:02.00,MrBeast,,0,0,0,,HELLO WORLD
"""
open('test_sub.ass', 'w', encoding='utf-8').write(ass_txt)
esc = os.path.abspath('test_sub.ass').replace('\\', '/').replace(':', r'\:')
cmd = ['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=1080x1920:d=1', '-filter_complex', f"[0:v]ass='{esc}'[vout]", '-map', '[vout]', 'test_out.mp4']
p = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
print('returncode:', p.returncode)
if p.returncode != 0:
    print('Error tail:\n', p.stderr[-800:])
else:
    print('Success!')
for x in ['test_sub.ass', 'test_out.mp4']:
    if os.path.exists(x): os.remove(x)
