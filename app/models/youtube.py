from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class YoutubeVideoInfo(BaseModel):
    # Video fields
    id: str
    title: str
    fulltitle: str
    thumbnail: str
    thumbnails: List[Dict[str, Any]]
    description: Optional[str] = None
    duration: int
    duration_string: str
    view_count: int
    average_rating: Optional[int] = None
    age_limit: int
    webpage_url: str
    categories: List[str]
    tags: List[str]
    comment_count: int
    chapters: Optional[List[Any]] = None
    heatmap: Optional[List[Any]] = None
    like_count: int
    cn_subtitle_url: Optional[str] = None
    en_subtitle_url: Optional[str] = None

    # Channel fields
    channel_id: str
    channel_url: str
    channel: str
    channel_follower_count: int

    # Upload info
    uploader: str
    uploader_id: str
    uploader_url: str
    upload_date: str
    timestamp: int

    # Other fields
    original_url: str
    webpage_url_basename: str
    webpage_url_domain: str
    extractor: str
    extractor_key: str

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_json(self, indent: Optional[int] = None, ensure_ascii: bool = False) -> str:
        """保持与原类相同的JSON序列化方法"""
        return self.model_dump_json(indent=indent, ensure_ascii=ensure_ascii) 