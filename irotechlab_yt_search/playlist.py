"""Playlist data model and extraction"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from .utils import clean_text, get_value


@dataclass
class Playlist:
    """YouTube playlist metadata"""
    
    id: str
    title: str
    url: str = ""
    thumbnail: str = ""
    thumbnails: List[Dict] = field(default_factory=list)
    video_count: str = ""
    video_count_int: Optional[int] = None
    author: str = ""
    author_id: Optional[str] = None
    author_url: str = ""
    description: str = ""
    videos: List[Dict] = field(default_factory=list)
    is_private: bool = False
    is_unlisted: bool = False
    created_date: Optional[str] = None
    updated_date: Optional[str] = None
    
    def __post_init__(self):
        if not self.url and self.id:
            self.url = f"https://www.youtube.com/playlist?list={self.id}"
        
        if self.video_count and not self.video_count_int:
            try:
                self.video_count_int = int(self.video_count.replace(",", ""))
            except:
                pass
        
        if self.author_id and not self.author_url:
            self.author_url = f"https://www.youtube.com/channel/{self.author_id}"
    
    @classmethod
    def from_renderer(cls, renderer: Dict[str, Any]) -> Optional['Playlist']:
        """Create Playlist from InnerTube renderer"""
        try:
            playlist_id = renderer.get("playlistId", "")
            
            title_runs = renderer.get("title", {}).get("runs", [])
            title = "".join(run.get("text", "") for run in title_runs)
            
            video_count = renderer.get("videoCount", "")
            
            # Get author info
            author_runs = renderer.get("longBylineText", {}).get("runs", [])
            author = author_runs[0].get("text", "") if author_runs else ""
            author_id = author_runs[0].get("navigationEndpoint", {}).get(
                "browseEndpoint", {}
            ).get("browseId", "") if author_runs else ""
            
            # Get thumbnails
            thumbnails = renderer.get("thumbnail", {}).get("thumbnails", [])
            thumbnail = thumbnails[-1].get("url", "") if thumbnails else ""
            
            # Get description
            description = renderer.get("descriptionSnippet", {}).get("runs", [{}])[0].get("text", "")
            
            return cls(
                id=playlist_id,
                title=title,
                thumbnail=thumbnail,
                thumbnails=thumbnails,
                video_count=video_count,
                author=author,
                author_id=author_id,
                description=clean_text(description)
            )
        except Exception:
            return None
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> Optional['Playlist']:
        """Create Playlist from API data"""
        try:
            playlist_id = data.get("playlistId", "")
            title = data.get("title", "")
            description = data.get("description", "")
            video_count = data.get("videoCount", "")
            
            # Get author
            author = data.get("author", {})
            author_name = author.get("name", "")
            author_id = author.get("id", "")
            
            # Get thumbnails
            thumbnails = data.get("thumbnails", [])
            thumbnail = thumbnails[-1].get("url", "") if thumbnails else ""
            
            # Get privacy status
            privacy = data.get("privacy", "")
            
            return cls(
                id=playlist_id,
                title=title,
                thumbnail=thumbnail,
                thumbnails=thumbnails,
                video_count=video_count,
                author=author_name,
                author_id=author_id,
                description=clean_text(description),
                is_private="private" in privacy.lower() if privacy else False,
                is_unlisted="unlisted" in privacy.lower() if privacy else False
            )
        except Exception:
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "thumbnail": self.thumbnail,
            "thumbnails": self.thumbnails,
            "video_count": self.video_count,
            "video_count_int": self.video_count_int,
            "author": self.author,
            "author_id": self.author_id,
            "author_url": self.author_url,
            "description": self.description,
            "is_private": self.is_private,
            "is_unlisted": self.is_unlisted,
            "created_date": self.created_date,
            "updated_date": self.updated_date,
            "videos": self.videos[:10]  # Only include first 10 videos to avoid large output
        }
    
    def __str__(self) -> str:
        return f"{self.title} - {self.author} ({self.video_count} videos)"