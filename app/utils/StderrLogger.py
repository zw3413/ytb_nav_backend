"""自定义日志记录器，用于将yt-dlp的输出重定向到stderr。"""
import sys
from typing import Any


class StderrLogger:
    """将yt-dlp的日志输出重定向到stderr的日志记录器。"""

    def debug(self, msg: Any) -> None:
        """记录调试信息。

        Args:
            msg: 要记录的调试信息
        """
        print(f"[yt-dlp-debug] {msg}", file=sys.stderr)

    def warning(self, msg: Any) -> None:
        """记录警告信息。

        Args:
            msg: 要记录的警告信息
        """
        print(f"[yt-dlp-warning] {msg}", file=sys.stderr)

    def error(self, msg: Any) -> None:
        """记录错误信息。

        Args:
            msg: 要记录的错误信息
        """
        print(f"[yt-dlp-error] {msg}", file=sys.stderr)