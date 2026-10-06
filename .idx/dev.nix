# Google Project IDX / Monospace Cloud Environment Specification
{ pkgs, ... }: {
  channel = "stable-23.11";
  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.virtualenv
    pkgs.ffmpeg
  ];
  env = {};
  idx = {
    extensions = [
      "ms-python.python"
    ];
    workspace = {
      onCreate = {
        pip-install = "pip install -r super_youtube_agent/01_facts_shorts/requirements.txt && pip install httpx edge-tts kokoro";
      };
    };
  };
}
