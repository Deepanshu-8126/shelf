import os, sys
print('Script started')
print('Current directory:', os.getcwd())
print('Sys path[0]:', sys.path[0] if sys.path else 'None')
try:
    from agent.db import list_channels
    print('Successfully imported list_channels')
    channels = list_channels()
    print('Channels:', channels)
except Exception as e:
    print('Error:', str(e))
    import traceback
    traceback.print_exc()
