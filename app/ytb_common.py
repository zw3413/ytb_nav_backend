import sys
class StderrLogger:
    def debug(self, msg):
        print(f"[yt-dlp-debug] {msg}", file=sys.stderr)

    def warning(self, msg):
        print(f"[yt-dlp-warning] {msg}", file=sys.stderr)

    def error(self, msg):
        print(f"[yt-dlp-error] {msg}", file=sys.stderr)