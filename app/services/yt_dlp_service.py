from typing import Dict, List, Optional, Any, Tuple
import json
import sys
import redis
import requests
import logging
import time
from enum import Enum
from fastapi import HTTPException
from app.utils.yt_dlp_utils import get_video_info_utils, get_cookies_path
from app.models.youtube import YoutubeVideoInfo
from app.agents.openai_summarizer import summarize_youtube_video

class SubtitleError(Exception):
    """字幕处理相关的异常"""
    pass

class VideoProcessingError(Exception):
    """视频处理相关的异常"""
    pass

class YoutubeDLPService:
    # Redis key constants
    REDIS_VIDEO_INFO_KEY = 'video_info'
    REDIS_VIDEO_SUMMARY_KEY = 'video_summary'
    REDIS_TRANSCRIPT_TASK_KEY = 'video_transcript_task'

    # Language patterns for subtitle extraction
    LANGUAGE_PATTERNS = {
        'en': ['en', 'en-zh-Hans'],
        'cn': ['cn', 'zh-Hans-zh-Hans', 'zh-Hans']
    }

    class TranscriptStatus(str, Enum):
        CREATED = '101'
        PROCESSING = '102'
        SUCCESS = '103'
        ERROR = '110'
        UNKNOWN = '199'
        READ = '105'

    def __init__(
        self, 
        redis_client: redis.Redis,
        logger: Optional[logging.Logger] = None,
        download_max_retries: int = 2,
        download_timeout: int = 60
    ):
        self.redis_client = redis_client
        self.logger = logger or logging.getLogger(__name__)
        self.download_max_retries = download_max_retries
        self.download_timeout = download_timeout

        # Configure logging if no logger provided
        if logger is None:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(sys.stdout),
                    logging.StreamHandler(sys.stderr)
                ]
            )

    @property
    def default_headers(self) -> Dict[str, str]:
        return {
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

    def _handle_transcript_error(self, video_id: str, status: str, msg: str) -> Dict:
        return {
            'video_id': video_id,
            'status': status,
            'msg': msg,
            'create_time': time.time(),
            'update_time': time.time()
        }

    def _update_transcript_task_state(self, video_id: str, status: str, msg: str):
        task_data = self._handle_transcript_error(video_id, status, msg)
        self.redis_client.hset(self.REDIS_TRANSCRIPT_TASK_KEY, video_id, json.dumps(task_data))

    async def get_video_info(self, video_url: str) -> Dict[str, Any]:
        try:
            # 获取视频信息
            info = get_video_info_utils(video_url)
            if not info:
                raise VideoProcessingError("Failed to fetch video information")

            # 获取字幕URL
            en_sub_url, cn_sub_url = self._extract_subtitle_url_for_languages(info)
            info['cn_subtitle_url'] = cn_sub_url
            info['en_subtitle_url'] = en_sub_url
            
            # 创建视频信息模型
            video_info = YoutubeVideoInfo.model_validate(info)
            result = video_info.model_dump()

            # Save to Redis
            video_id = video_info.id
            self.redis_client.hset(self.REDIS_VIDEO_INFO_KEY, video_id, json.dumps(result))

            return result
        except Exception as e:
            self.logger.error(f"Error when get_video_info: {str(e)}", exc_info=True)
            raise e

    async def get_video_summary(self, video_id: str) -> Dict[str, Any]:
        try:
            # Check Redis cache first
            video_summary = self.redis_client.hget(self.REDIS_VIDEO_SUMMARY_KEY, video_id)
            if video_summary and len(video_summary) > 0:
                return json.loads(video_summary)

            # Get video info from Redis
            video_info_json = self.redis_client.hget(self.REDIS_VIDEO_INFO_KEY, video_id)
            if not video_info_json:
                raise VideoProcessingError(f"Video info not found in Redis for video_id: {video_id}")
            
            info = json.loads(video_info_json)
            video_info = YoutubeVideoInfo(**info)

            # Handle subtitle content
            subtitle_url = video_info.cn_subtitle_url or video_info.en_subtitle_url
            if not subtitle_url:
                return self._handle_missing_subtitle(video_id)

            caption_text = self._download_text(subtitle_url)
            if not caption_text:
                self.logger.error('Failed to download subtitle content')
                raise SubtitleError("Failed to download subtitle content")

            # Generate summary
            summary_result_cn = await summarize_youtube_video(
                video_title=video_info.title,
                video_description=video_info.description,
                video_tags=video_info.tags,
                video_captions=caption_text,
                output_language='Simplified Chinese'
            )
            result = [summary_result_cn]
            
            # Cache in Redis
            self.redis_client.hset(self.REDIS_VIDEO_SUMMARY_KEY, video_id, json.dumps(result))

            return result

        except Exception as e:
            self.logger.error(f"Error processing video: {str(e)}", exc_info=True)
            raise e

    def _handle_missing_subtitle(self, video_id: str) -> Dict[str, Any]:
        # Check existing transcript task
        transcript_task = self.redis_client.hget(self.REDIS_TRANSCRIPT_TASK_KEY, video_id)
        if transcript_task:
            task_dict = json.loads(transcript_task)
            status = task_dict['status']
            
            if status == self.TranscriptStatus.CREATED:
                return {'code': '101', "msg": "transcript task created"}
            elif status == self.TranscriptStatus.PROCESSING:
                return {'code': '102', "msg": "transcript task processing"}
            elif status == self.TranscriptStatus.SUCCESS:
                caption_text = task_dict['msg']
                task_dict['code'] = self.TranscriptStatus.READ
                self.redis_client.hset(self.REDIS_TRANSCRIPT_TASK_KEY, video_id, json.dumps(task_dict))
                return {'code': '103', "msg": caption_text}
            elif status == self.TranscriptStatus.ERROR:
                return {'code': '110', "msg": f"transcript task failed, {task_dict['msg']}"}
            else:
                return {'code': '199', "msg": f"transcript task status unknown, {status}"}

        # Create new transcript task
        self._update_transcript_task_state(
            video_id, 
            self.TranscriptStatus.CREATED, 
            "transcript task created"
        )
        return {'code': '101', "msg": "transcript task created"}

    def _download_text(self, url: str) -> Optional[str]:
        cookies_path = get_cookies_path()
        cookies = None
        if cookies_path:
            try:
                import http.cookiejar
                cookie_jar = http.cookiejar.MozillaCookieJar(cookies_path)
                cookie_jar.load(ignore_discard=True, ignore_expires=True)
                cookies = cookie_jar
            except Exception as e:
                self.logger.warning(f"Failed to load cookies from {cookies_path}: {e}")

        for attempt in range(self.download_max_retries + 1):
            try:
                self.logger.info(f"Attempting to download text from URL: {url}")
                response = requests.get(
                    url,
                    headers=self.default_headers,
                    cookies=cookies,
                    timeout=self.download_timeout,
                    allow_redirects=True
                )
                response.raise_for_status()
                
                if not response.text:
                    raise SubtitleError("Failed to download text content.")
                    
                self.logger.info("Successfully downloaded text content")
                return response.text
                
            except requests.RequestException as e:
                if attempt < self.download_max_retries:
                    wait_time = (attempt + 1) * 2
                    self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s... Error: {e}")
                    time.sleep(wait_time)
                    continue
                self.logger.error(f"Error downloading {url} after {self.download_max_retries + 1} attempts: {e}")
                return None

    def _get_subtitle_url(
        self, 
        languages: Dict[str, List[Dict[str, str]]], 
        lang_code: str, 
        format: str = 'vtt'
    ) -> str:
        if not languages:
            return ''
            
        patterns = self.LANGUAGE_PATTERNS.get(lang_code, [])
        
        for pattern in patterns:
            for lang_key in languages:
                if lang_key.startswith(pattern):
                    for sub in languages[lang_key]:
                        if sub['ext'] == format:
                            return sub['url']
        
        return ''

    def _extract_subtitle_url_for_languages(
        self, 
        info: Dict[str, Any], 
        lang_codes: List[str] = ['cn', 'en']
    ) -> Tuple[str, str]:
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
                    en_sub_url = self._get_subtitle_url(languages, 'en')
                elif lang_key.startswith('zh-Hans') or lang_key == 'cn':
                    cn_sub_url = self._get_subtitle_url(languages, 'cn')

        return en_sub_url, cn_sub_url


