from typing import Dict, Any, Optional
import yt_dlp
import contextlib
import io
from app.utils.StderrLogger import StderrLogger
import sys
import os
from pathlib import Path
import time
import random
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)


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
            
            # 添加更多伪装选项
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'sec-ch-ua': '"Chromium";v="123", "Google Chrome";v="123", "Not:A-Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'DNT': '1',
                'Referer': 'https://www.youtube.com/'
            },
            
            # 添加更多高级选项
            'socket_timeout': 30,  # 增加超时时间
            'retries': 10,         # 增加重试次数
            'fragment_retries': 10,
            'extractor_retries': 10,
            'skip_unavailable_fragments': True,
            'keepvideo': False,
            'writedescription': False,
            'writeinfojson': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'postprocessors': [],
            'geo_bypass': True,    # 绕过地理限制
            'geo_verification_proxy': None,
            'geo_bypass_country': None,
            'geo_bypass_ip_block': None,
            
            # 添加新的反检测选项
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage', 'configs'],
                    'skip': ['dash', 'hls'],
                    'formats': 'missing_pot',  # 允许使用缺少 PO Token 的格式
                    'visitor_data': 'CgtQc0FfV2FfV0FfUSiImZ6qBjIGCgJHQg%3D%3D',  # 添加访客数据
                }
            },
            'format_sort': ['res', 'ext:mp4:m4a'],
            'format': 'best',
            'nocheckcertificate': True,
            'legacy_server_connect': True,
        }
        
        # 如果存在 cookies 文件，添加到选项中
        if cookies_path:
            ydl_opts['cookiefile'] = cookies_path
        
        # 使用yt-dlp获取视频信息
        with contextlib.redirect_stdout(io.StringIO()):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 添加随机延迟，模拟人类行为
                time.sleep(random.uniform(1, 3))
                
                try:
                    info = ydl.extract_info(url, download=False)
                except Exception as e:
                    logger.warning(f"First attempt failed: {e}")
                    # 如果第一次尝试失败，等待更长时间后重试
                    time.sleep(random.uniform(5, 10))
                    info = ydl.extract_info(url, download=False)
                
                # 检查是否获取到字幕信息
                if info and not (info.get('automatic_captions') or info.get('subtitles')):
                    print("No subtitle information found, retrying...", file=sys.stderr)
                    # 重试前添加随机延迟
                    time.sleep(random.uniform(2, 5))
                    # 重试一次
                    info = ydl.extract_info(url, download=False)
                
        if not info:
            raise VideoInfoError("Failed to extract video information")
            
        return info
            
    except yt_dlp.utils.DownloadError as e:
        raise VideoInfoError(f"Download error: {str(e)}")
    except Exception as e:
        raise VideoInfoError(f"Unexpected error: {str(e)}")