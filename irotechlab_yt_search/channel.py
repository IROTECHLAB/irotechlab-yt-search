"""Channel data model and extraction"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from .utils import clean_text, parse_view_count, get_value


@dataclass
class Channel:
    """YouTube channel metadata"""
    
    id: str
    name: str
    url: str = ""
    thumbnail: str = ""
    thumbnails: List[Dict] = field(default_factory=list)
    subscribers: str = ""
    subscriber_count: Optional[int] = None
    video_count: str = ""
    video_count_int: Optional[int] = None
    view_count: str = ""
    view_count_int: Optional[int] = None
    description: str = ""
    joined_date: Optional[str] = None
    joined_date_obj: Optional[datetime] = None
    country: str = ""
    is_verified: bool = False
    is_artist: bool = False
    is_creator: bool = False
    links: List[Dict[str, str]] = field(default_factory=list)
    banner_url: str = ""
    avatar_url: str = ""
    
    def __post_init__(self):
        if not self.url and self.id:
            self.url = f"https://www.youtube.com/channel/{self.id}"
        
        if self.subscribers and not self.subscriber_count:
            self.subscriber_count = parse_view_count(self.subscribers)
        
        if self.view_count and not self.view_count_int:
            self.view_count_int = parse_view_count(self.view_count)
    
    @classmethod
    def from_renderer(cls, renderer: Dict[str, Any]) -> Optional['Channel']:
        """Create Channel from InnerTube renderer"""
        try:
            channel_id = renderer.get("channelId", "")
            name_runs = renderer.get("title", {}).get("runs", [])
            name = name_runs[0].get("text", "") if name_runs else ""
            
            subscribers = renderer.get("subscriberCountText", {}).get("simpleText", "")
            video_count = renderer.get("videoCountText", {}).get("runs", [{}])[0].get("text", "")
            
            thumbnails = renderer.get("thumbnail", {}).get("thumbnails", [])
            thumbnail = thumbnails[-1].get("url", "") if thumbnails else ""
            
            return cls(
                id=channel_id,
                name=name,
                thumbnail=thumbnail,
                thumbnails=thumbnails,
                subscribers=subscribers,
                video_count=video_count,
                url=f"https://www.youtube.com/channel/{channel_id}" if channel_id else ""
            )
        except Exception:
            return None
    
    @classmethod
    def from_api_data(cls, data: Dict[str, Any]) -> Optional['Channel']:
        """Create Channel from API data (browse endpoint)"""
        try:
            # Extract from aboutChannelViewModel
            about = data.get("aboutChannelViewModel", {})
            
            channel_id = data.get("channelId", "")
            name = data.get("title", {}).get("simpleText", "")
            
            if not name and about:
                name = about.get("title", {}).get("content", "")
            
            # Get subscriber count
            subscribers = about.get("subscriberCountText", "")
            
            # Get video count
            video_count = about.get("videoCountText", "")
            
            # Get view count
            view_count = about.get("viewCountText", "")
            
            # Get description
            description = about.get("description", "")
            
            # Get joined date
            joined_date = about.get("joinedDateText", {}).get("content", "")
            
            # Get country
            country = about.get("country", "")
            
            # Get links
            links = []
            for link in about.get("links", []):
                link_data = link.get("channelExternalLinkViewModel", {})
                links.append({
                    "title": link_data.get("title", {}).get("content", ""),
                    "url": link_data.get("link", {}).get("content", ""),
                    "favicon": link_data.get("favicon", "")
                })
            
            # Get thumbnails
            thumbnails = data.get("thumbnail", {}).get("thumbnails", [])
            thumbnail = thumbnails[-1].get("url", "") if thumbnails else ""
            
            return cls(
                id=channel_id,
                name=name,
                url=f"https://www.youtube.com/channel/{channel_id}" if channel_id else "",
                thumbnail=thumbnail,
                thumbnails=thumbnails,
                subscribers=subscribers,
                video_count=video_count,
                view_count=view_count,
                description=clean_text(description),
                joined_date=joined_date,
                country=country,
                links=links
            )
        except Exception as e:
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "thumbnail": self.thumbnail,
            "thumbnails": self.thumbnails,
            "subscribers": self.subscribers,
            "subscriber_count": self.subscriber_count,
            "video_count": self.video_count,
            "view_count": self.view_count,
            "description": self.description,
            "joined_date": self.joined_date,
            "country": self.country,
            "is_verified": self.is_verified,
            "links": self.links,
            "banner_url": self.banner_url
        }
    
    def __str__(self) -> str:
        return f"{self.name} - {self.subscribers} subscribers"