"""Video data model"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from .utils import (
    parse_duration,
    parse_view_count,
    parse_upload_date,
    clean_text,
    extract_video_id
)

@dataclass
class Video:
    """YouTube video metadata"""
    
    id: str
    title: str
    channel: str
    channel_id: Optional[str] = None
    url: str = ""
    thumbnail: str = ""
    duration: str = ""
    duration_seconds: Optional[int] = None
    views: str = ""
    view_count: Optional[int] = None
    published: str = ""
    published_date: Optional[datetime] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)
    likes: Optional[int] = None
    comments: Optional[int] = None
    is_live: bool = False
    is_premium: bool = False
    
    def __post_init__(self):
        """Initialize derived fields"""
        if not self.url and self.id:
            self.url = f"https://www.youtube.com/watch?v={self.id}"
        
        if self.duration and not self.duration_seconds:
            self.duration_seconds = parse_duration(self.duration)
        
        if self.views and not self.view_count:
            self.view_count = parse_view_count(self.views)
        
        if self.published and not self.published_date:
            self.published_date = parse_upload_date(self.published)
    
    @classmethod
    def from_renderer(cls, renderer: Dict[str, Any]) -> Optional['Video']:
        """Create Video from InnerTube video renderer"""
        try:
            # Extract title
            title_runs = renderer.get("title", {}).get("runs", [])
            title = "".join(run.get("text", "") for run in title_runs)
            title = clean_text(title)
            
            # Extract basic info
            video_id = renderer.get("videoId", "")
            
            # Extract channel info
            channel_runs = renderer.get("ownerText", {}).get("runs", [])
            channel = channel_runs[0].get("text", "") if channel_runs else ""
            channel_id = renderer.get("ownerText", {}).get(
                "runs", [{}]
            )[0].get("navigationEndpoint", {}).get(
                "browseEndpoint", {}
            ).get("browseId", "")
            
            # Extract metadata
            views = renderer.get("viewCountText", {}).get("simpleText", "")
            published = renderer.get("publishedTimeText", {}).get("simpleText", "")
            duration = renderer.get("lengthText", {}).get("simpleText", "")
            
            # Extract thumbnails
            thumbnails = renderer.get("thumbnail", {}).get("thumbnails", [])
            thumbnail = thumbnails[-1].get("url", "") if thumbnails else ""
            
            # Check if live
            is_live = "live" in renderer.get("badges", [{}])[0].get(
                "metadataBadgeRenderer", {}
            ).get("label", "").lower()
            
            return cls(
                id=video_id,
                title=title,
                channel=channel,
                channel_id=channel_id,
                thumbnail=thumbnail,
                duration=duration,
                views=views,
                published=published,
                is_live=is_live
            )
        except Exception:
            return None
    
    @classmethod
    def from_url(cls, url: str) -> Optional['Video']:
        """Create Video from YouTube URL"""
        video_id = extract_video_id(url)
        if not video_id:
            return None
        return cls(id=video_id, title="", channel="")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "channel": self.channel,
            "channel_id": self.channel_id,
            "url": self.url,
            "thumbnail": self.thumbnail,
            "duration": self.duration,
            "duration_seconds": self.duration_seconds,
            "views": self.views,
            "view_count": self.view_count,
            "published": self.published,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "is_live": self.is_live,
            "is_premium": self.is_premium
        }
    
    def __str__(self) -> str:
        return f"{self.title} - {self.channel} ({self.duration})"