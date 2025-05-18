from typing import Dict, List, Optional, Any, Tuple
import json
import sys
import requests
import logging
import time
from fastapi import HTTPException
from app.utils.yt_dlp_utils import get_video_info, get_cookies_path
from app.models.youtube import YoutubeVideoInfo
from app.agents.yt_dlp_summarizer import summarize_youtube_video

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

class SubtitleError(Exception):
    """字幕处理相关的异常"""
    pass


class VideoProcessingError(Exception):
    """视频处理相关的异常"""
    pass


async def get_video_summary(video_url: str) -> Dict[str, Any]:
    """获取YouTube视频的摘要信息。

    Args:
        video_url: YouTube视频URL，例如 "https://www.youtube.com/watch?v=5F2S2UUACi4"

    Returns:
        Dict[str, Any]: 包含视频信息和摘要的字典
        {
            "video_info": {
                // 视频基本信息
            },
            "video_summary": [{
                "outline": [
                    {"timestamp": "HH:MM:SS", "topic": "Brief description"}
                ],
                "summary": "Comprehensive summary of the video",
                "keywords": ["keyword1", "keyword2", "keyword3"]
            }]
        }

    Raises:
        HTTPException: 当视频处理失败时抛出
    """
    try:
        # 获取视频信息
        info = get_video_info(video_url)
        if not info:
            raise VideoProcessingError("Failed to fetch video information")

        # 获取字幕URL
        en_sub_url, cn_sub_url = extract_subtitle_url_for_languages(info)
        info['cn_subtitle_url'] = cn_sub_url
        info['en_subtitle_url'] = en_sub_url
        
        # 创建视频信息模型
        video_info = YoutubeVideoInfo(**info)
        result = {
            "video_info": video_info.model_dump(),
            "video_summary": []  # 初始化为空列表
        }

        # 获取字幕内容
        subtitle_url = video_info.cn_subtitle_url or video_info.en_subtitle_url
        if not subtitle_url:
            logger.warning('No subtitles found')
            raise SubtitleError("No Subtitles found")
        
        caption_text = download_text(subtitle_url)
        if not caption_text:
            logger.error('Failed to download subtitle content')
            raise SubtitleError("Failed to download subtitle content")

        # 生成视频摘要
        summary_result = await summarize_youtube_video(
            video_title=video_info.title,
            video_description=video_info.description,
            video_tags=video_info.tags,
            video_captions=caption_text,
            output_language='Simplified Chinese'
        )
        
        result["video_summary"] = [summary_result]
        return result

    except Exception as e:
        logger.error(f"Error processing video: {str(e)}", exc_info=True)
        raise e


def download_text(url: str, max_retries: int = 2) -> Optional[str]:
    """下载文本内容。

    Args:
        url: 要下载的URL
        max_retries: 最大重试次数，默认为2次

    Returns:
        Optional[str]: 下载的文本内容，如果下载失败则返回None
    """
    # 设置请求头，模拟浏览器
    headers = {
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
        'Cache-Control': 'max-age=0'
    }

    # 获取 cookies 文件路径
    cookies_path = get_cookies_path()
    cookies = None
    if cookies_path:
        try:
            import http.cookiejar
            cookie_jar = http.cookiejar.MozillaCookieJar(cookies_path)
            cookie_jar.load(ignore_discard=True, ignore_expires=True)
            cookies = cookie_jar
        except Exception as e:
            logger.warning(f"Failed to load cookies from {cookies_path}: {e}")

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Attempting to download text from URL: {url}")
            response = requests.get(
                url,
                headers=headers,
                cookies=cookies,
                timeout=60,
                allow_redirects=True
            )
            response.raise_for_status()
            
            if not response.text:
                raise SubtitleError("Failed to download text content.")
                
            logger.info("Successfully downloaded text content")
            return response.text
            
        except requests.RequestException as e:
            if attempt < max_retries:
                wait_time = (attempt + 1) * 2  # 指数退避
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s... Error: {e}")
                time.sleep(wait_time)
                continue
            logger.error(f"Error downloading {url} after {max_retries + 1} attempts: {e}")
            return None


def get_subtitle_url(
    languages: Dict[str, List[Dict[str, str]]],
    lang_code: str,
    format: str = 'vtt'
) -> str:
    """获取特定语言的字幕URL。

    Args:
        languages: 可用语言及其字幕的字典
        lang_code: 语言代码 ('en' 或 'cn')
        format: 字幕格式 (默认: 'vtt')

    Returns:
        str: 字幕文件的URL，如果未找到则返回空字符串
    """
    if not languages:
        return ''
        
    # 定义可能的语言代码模式
    lang_patterns = {
        'en': ['en', 'en-zh-Hans'],
        'cn': ['cn', 'zh-Hans-zh-Hans', 'zh-Hans']
    }
    
    patterns = lang_patterns.get(lang_code, [])
    
    for pattern in patterns:
        for lang_key in languages:
            if lang_key.startswith(pattern):
                for sub in languages[lang_key]:
                    if sub['ext'] == format:
                        return sub['url']
    
    return ''


def extract_subtitle_url_for_languages(
    info: Dict[str, Any],
    lang_codes: List[str] = ['cn', 'en']
) -> Tuple[str, str]:
    """从视频信息中提取字幕URL。

    Args:
        info: 视频信息字典
        lang_codes: 要提取的语言代码列表

    Returns:
        Tuple[str, str]: 英文和中文字幕的URL
    """
    en_sub_url = ''
    cn_sub_url = ''
    languages = None

    # 优先使用自动生成的字幕
    if 'automatic_captions' in info and info['automatic_captions']:
        languages = info['automatic_captions']
    elif 'subtitles' in info and info['subtitles']:
        languages = info['subtitles']

    if languages:
        for lang_key in languages:
            if lang_key.startswith('en'):
                en_sub_url = get_subtitle_url(languages, 'en')
            elif lang_key.startswith('zh-Hans') or lang_key == 'cn':
                cn_sub_url = get_subtitle_url(languages, 'cn')

    return en_sub_url, cn_sub_url


if __name__ == "__main__":
    # 测试代码
    video_url = "https://www.youtube.com/watch?v=SUY_E-I7O_Y&t=2876s"
    video_info = get_video_info(video_url)
    print(video_info, file=sys.stderr)


