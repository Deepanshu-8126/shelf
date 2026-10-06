import sys
print('Script started')
print('Sys path[:3]:', str(sys.path[:3]))
try:
    from agent.db import list_channels
    print('Successfully imported list_channels')
    channels = list_channels()
    print('Channels:', channels)
except Exception as e:
    print('Error:', str(e))
    import traceback
    traceback.print_exc()
