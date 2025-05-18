from typing import Dict, Any, Optional
import yt_dlp
import contextlib
import io
from app.utils.StderrLogger import StderrLogger
import sys
import os
from pathlib import Path


class VideoInfoError(Exception):
    """视频信息获取相关的异常"""
    pass


def get_cookies_path() -> Optional[str]:
    """获取 cookies 文件路径。
    
    Returns:
        Optional[str]: cookies 文件路径，如果不存在则返回 None
    """
    # 首先检查环境变量
    cookies_path = os.getenv('YOUTUBE_COOKIES_PATH')
    if cookies_path and os.path.exists(cookies_path):
        return cookies_path
        
    # 然后检查默认位置
    default_paths = [
        os.path.expanduser('~/.config/yt-dlp/cookies.txt'),
        os.path.expanduser('~/.local/share/yt-dlp/cookies.txt'),
        '/opt/ytb_nav/cookies.txt'
    ]
    
    for path in default_paths:
        if os.path.exists(path):
            return path
            
    return None


def get_video_info(url: str) -> Optional[Dict[str, Any]]:
    """获取YouTube视频的详细信息。

    Args:
        url: YouTube视频的URL

    Returns:
        Optional[Dict[str, Any]]: 包含视频信息的字典，如果获取失败则返回None

    Raises:
        VideoInfoError: 当视频信息获取失败时抛出
    """
    try:
        # 获取 cookies 路径
        cookies_path = get_cookies_path()
        
        # 配置yt-dlp选项
        ydl_opts = {
            'skip_download': True,  # 不下载视频
            'listsubtitles': True,  # 列出可用字幕
            'quiet': True,          # 静默模式
            'logger': StderrLogger(),  # 使用自定义logger
            'progress_hooks': [],      # 禁用进度回调
            'no_warnings': True,       # 禁用警告
            'extract_flat': False,     # 获取完整信息
            'ignoreerrors': False,     # 不忽略错误
        }
        
        # 如果存在 cookies 文件，添加到选项中
        if cookies_path:
            ydl_opts['cookiefile'] = cookies_path
        
        # 使用yt-dlp获取视频信息
        with contextlib.redirect_stdout(io.StringIO()):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # 检查是否获取到字幕信息
                if info and not (info.get('automatic_captions') or info.get('subtitles')):
                    print("No subtitle information found, retrying...", file=sys.stderr)
                    # 重试一次
                    info = ydl.extract_info(url, download=False)
                
        if not info:
            raise VideoInfoError("Failed to extract video information")
            
        return info
            
    except yt_dlp.utils.DownloadError as e:
        raise VideoInfoError(f"Download error: {str(e)}")
    except Exception as e:
        raise VideoInfoError(f"Unexpected error: {str(e)}")