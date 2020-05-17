ffmpeg -safe 0 -f concat -i list -c copy -f mpegts pipe:1 | ffplay -
    # /Applications/VLC.app/Contents/MacOS/VLC -
