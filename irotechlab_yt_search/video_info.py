"""Video information extraction for YouTube"""

import re
import json
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from urllib.parse import urlencode
from .exceptions import RequestError, ParseError, VideoUnavailableError
from .utils import (
    parse_duration,
    parse_view_count,
    parse_upload_date,
    clean_text,
    get_video_id,
    get_value,
    safe_get
)

logger = logging.getLogger(__name__)

# Client configuration
CLIENT_CONFIG = {
    "context": {
        "client": {
            "hl": "en",
            "gl": "US",
            "clientName": "WEB",
            "clientVersion": "2.20260404.01.00",
            "platform": "DESKTOP",
        },
        "user": {"lockedSafetyMode": False},
        "request": {"useSsl": True},
    }
}


class VideoInfo:
    """Video information extraction using YouTube's hidden API with HTML fallback"""
    
    def __init__(
        self,
        proxy: Optional[str] = None,
        timeout: int = 15
    ):
        self.proxy = proxy
        self.timeout = timeout
        self.session = None
        self.api_key = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
        
    async def _ensure_session(self):
        if self.session is None:
            import aiohttp
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _call_youtube_api(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        session = await self._ensure_session()
        url = f"https://www.youtube.com/youtubei/v1/{endpoint}?key={self.api_key}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "Origin": "https://www.youtube.com",
            "Referer": "https://www.youtube.com",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        async with session.post(url, json=payload, headers=headers, proxy=self.proxy, timeout=self.timeout) as response:
            if response.status == 200:
                return await response.json()
            else:
                text = await response.text()
                raise RequestError(f"HTTP {response.status}: {text[:200]}")
    
    async def _fetch_html_page(self, video_id: str) -> str:
        session = await self._ensure_session()
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        async with session.get(url, headers=headers, proxy=self.proxy, timeout=self.timeout) as response:
            if response.status == 200:
                return await response.text()
            else:
                raise RequestError(f"Failed to fetch HTML: HTTP {response.status}")
    
    def _extract_from_html(self, html: str, video_id: str) -> Dict[str, Any]:
        # Find ytInitialPlayerResponse
        match = re.search(r'var ytInitialPlayerResponse\s*=\s*({.+?});\s*var', html, re.DOTALL)
        if not match:
            match = re.search(r'ytInitialPlayerResponse\s*=\s*({.+?});', html, re.DOTALL)
        
        if not match:
            raise ParseError("Could not find ytInitialPlayerResponse in HTML")
        
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError as e:
            raise ParseError(f"Failed to parse JSON: {e}")
        
        if "playabilityStatus" in data:
            status = data["playabilityStatus"]
            if status.get("status") != "OK":
                error_msg = status.get("reason", "Video unavailable")
                raise VideoUnavailableError(f"Video unavailable: {error_msg}")
        
        return self._parse_video_info(data, video_id)
    
    async def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        if not video_id:
            raise ValueError("Video ID cannot be empty")
        
        # Try API approach
        try:
            payload = {
                "videoId": video_id,
                "context": CLIENT_CONFIG["context"]
            }
            data = await self._call_youtube_api("player", payload)
            
            if "playabilityStatus" in data:
                status = data["playabilityStatus"]
                if status.get("status") != "OK":
                    logger.warning(f"API returned unavailable: {status.get('reason')}, trying HTML fallback...")
                    html = await self._fetch_html_page(video_id)
                    return self._extract_from_html(html, video_id)
            
            return self._parse_video_info(data, video_id)
            
        except Exception as e:
            logger.warning(f"API request failed: {e}, trying HTML fallback...")
            try:
                html = await self._fetch_html_page(video_id)
                return self._extract_from_html(html, video_id)
            except Exception as html_error:
                raise RequestError(f"Both API and HTML extraction failed: {html_error}")
    
    def _parse_video_info(self, data: Dict[str, Any], video_id: str) -> Dict[str, Any]:
        result = {
            "id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "title": "",
            "channel": "",
            "channel_id": "",
            "channel_url": "",
            "description": "",
            "views": "",
            "view_count": None,
            "likes": None,
            "duration": "",
            "duration_seconds": None,
            "published": "",
            "published_date": None,
            "thumbnail": "",
            "thumbnails": [],
            "tags": [],
            "category": "",
            "is_live": False,
            "is_live_now": False,
            "allow_ratings": False,
            "average_rating": None,
            "is_family_safe": False,
            "streaming_data": None,
            "formats": [],
            "adaptive_formats": []
        }
        
        try:
            video_details = data.get("videoDetails", {})
            if video_details:
                result["title"] = video_details.get("title", "")
                result["channel"] = video_details.get("author", "")
                result["channel_id"] = video_details.get("channelId", "")
                result["views"] = video_details.get("viewCount", "")
                result["view_count"] = int(result["views"]) if result["views"].isdigit() else None
                result["duration"] = video_details.get("lengthSeconds", "")
                result["duration_seconds"] = int(result["duration"]) if result["duration"] else None
                result["is_live"] = video_details.get("isLiveContent", False)
                result["description"] = video_details.get("shortDescription", "")
                result["tags"] = video_details.get("keywords", [])
                result["category"] = video_details.get("category", "")
                result["allow_ratings"] = video_details.get("allowRatings", False)
                result["average_rating"] = video_details.get("averageRating", None)
                
                if result["channel_id"]:
                    result["channel_url"] = f"https://www.youtube.com/channel/{result['channel_id']}"
                
                thumbnails = video_details.get("thumbnail", {}).get("thumbnails", [])
                result["thumbnails"] = thumbnails
                if thumbnails:
                    result["thumbnail"] = thumbnails[-1].get("url", "")
            
            microformat = data.get("microformat", {}).get("playerMicroformatRenderer", {})
            if microformat:
                if not result["title"]:
                    result["title"] = microformat.get("title", {}).get("simpleText", "")
                if not result["description"]:
                    result["description"] = microformat.get("description", {}).get("simpleText", "")
                result["published"] = microformat.get("publishDate", "")
                result["category"] = microformat.get("category", "")
                result["is_family_safe"] = microformat.get("isFamilySafe", False)
                
                if not result["channel"]:
                    result["channel"] = microformat.get("ownerChannelName", "")
                if not result["channel_id"]:
                    result["channel_id"] = microformat.get("ownerChannelId", "")
                    if result["channel_id"]:
                        result["channel_url"] = f"https://www.youtube.com/channel/{result['channel_id']}"
                
                upload_date = microformat.get("uploadDate", "")
                if upload_date:
                    try:
                        result["published_date"] = datetime.fromisoformat(upload_date.replace("Z", "+00:00"))
                    except:
                        pass
            
            if result["published"] and not result["published_date"]:
                result["published_date"] = parse_upload_date(result["published"])
            
            result["is_live_now"] = result["is_live"] and result["duration"] == "0"
            
            streaming_data = data.get("streamingData", {})
            if streaming_data:
                result["streaming_data"] = streaming_data
                result["formats"] = streaming_data.get("formats", [])
                result["adaptive_formats"] = streaming_data.get("adaptiveFormats", [])
            
            result["description"] = clean_text(result["description"])
            
        except Exception as e:
            logger.error(f"Error parsing video info: {e}")
            raise ParseError(f"Failed to parse video info: {e}")
        
        return result
    
    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None