import sys
import os
sys.path.insert(0, 'D:\facts_yt\super_youtube_agent\01_facts_shorts')

from factshorts.tts_local import synthesize_local
from factshorts.config import get_config
from pathlib import Path
import asyncio

async def test_voice(voice_name, text='This is a test of the Kokoro voice system. How does this voice sound to you?'):
    '''Test a specific Kokoro voice and save to file'''
    cfg = get_config()
    
    # Create output directory
    output_dir = Path('D:\facts_yt\super_youtube_agent\01_facts_shorts\voice_tests')
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f'{voice_name}.mp3'
    
    print(f'Testing voice: {voice_name}')
    print(f'Saving to: {output_file}')
    
    try:
        result = await synthesize_local(
            text=text,
            out_path=output_file,
            engine='kokoro',
            voice=voice_name,
            speed=1.0,
            cfg=cfg
        )
        print(f'Success! Duration: {result.duration:.2f} seconds')
        return True
    except Exception as e:
        print(f'Error with voice {voice_name}: {e}')
        return False

async def main():
    # Test voices we know about from the configuration
    voices_to_test = [
        'am_michael',  # The one you liked
        'af_heart',
        'af_bella', 
        'bm_george',
        'af_nicole',
        'bf_emma',
        'am_adam',
        'bm_lewis',
        'af_nova',
        'af_sarah',
        'bf_alice',
        'bf_isabella'
    ]
    
    print('Testing Kokoro voices...')
    print('=' * 50)
    
    for voice in voices_to_test:
        await test_voice(voice)
        print()

if __name__ == '__main__':
    asyncio.run(main())
