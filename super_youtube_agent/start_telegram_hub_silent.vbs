Set WshShell = CreateObject("WScript.Shell")
' Run master_telegram_hub.py completely hidden in background (0 = hide window)
WshShell.Run "python super_youtube_agent\master_telegram_hub.py", 0, False
Set WshShell = Nothing
