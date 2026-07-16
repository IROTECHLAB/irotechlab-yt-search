"""Search functionality for YouTube"""

from typing import List, Dict, Optional, Any
import asyncio
import random
import logging
from .client import InnerTubeClient
from .video import Video
from .channel import Channel
from .playlist import Playlist
from .exceptions import InvalidQueryError, ParseError
from .utils import (
    random_delay, 
    clean_text, 
    get_value, 
    extract_continuation_token,
    parse_search_results
)

logger = logging.getLogger(__name__)

class YouTubeSearch:
    """
    Main class for searching YouTube content
    
    Example:
        >>> search = YouTubeSearch()
        >>> videos = search.search("python tutorial")
        >>> for video in videos:
        ...     print(video.title, video.url)
    """
    
    SEARCH_FILTERS = {
        "all": "",
        "video": "EgIQAQ%3D%3D",
        "channel": "EgIQAg%3D%3D",
        "playlist": "EgIQAw%3D%3D",
        "movie": "EgIQBA%3D%3D",
        "live": "EgIQBQ%3D%3D"
    }
    
    SORT_FILTERS = {
        "relevance": "",
        "upload_date": "CAI%3D",
        "view_count": "CAM%3D",
        "rating": "CAE%3D"
    }
    
    def __init__(
        self,
        client_type: str = "WEB",
        proxy: Optional[str] = None,
        timeout: int = 10
    ):
        """
        Initialize YouTube search
        
        Args:
            client_type: WEB, ANDROID, IOS, or TV
            proxy: Proxy URL (optional)
            timeout: Request timeout in seconds
        """
        self.client = InnerTubeClient(
            client_type=client_type,
            proxy=proxy,
            timeout=timeout
        )
        self._continuation_token = None
        
    async def search(
        self,
        query: str,
        max_results: int = 10,
        filter_type: str = "all",
        sort_by: str = "relevance",
        region_code: str = "US",
        language: str = "en",
        safe_search: bool = False
    ) -> List[Video]:
        """
        Search YouTube videos
        
        Args:
            query: Search query string
            max_results: Maximum number of results
            filter_type: all, video, channel, playlist, movie, live
            sort_by: relevance, upload_date, view_count, rating
            region_code: Two-letter country code
            language: Language code
            safe_search: Enable safe search
            
        Returns:
            List of Video objects
            
        Raises:
            InvalidQueryError: If query is empty
            ParseError: If response parsing fails
        """
        if not query or not query.strip():
            raise InvalidQueryError("Search query cannot be empty")
        
        query = clean_text(query)
        
        # Build context with proper client
        context = {
            "client": {
                "hl": language,
                "gl": region_code,
                "clientName": self.client.client_config["clientName"],
                "clientVersion": self.client.client_config["clientVersion"],
                "platform": "DESKTOP"
            },
            "user": {
                "lockedSafetyMode": safe_search
            },
            "request": {
                "useSsl": True
            }
        }
        
        # Build search params
        params = self.SEARCH_FILTERS.get(filter_type, "")
        if sort_by != "relevance":
            params += self.SORT_FILTERS.get(sort_by, "")
        
        payload = {
            "context": context,
            "query": query,
            "params": params
        }
        
        # Make request
        try:
            data = await self.client.request("search", payload)
        except Exception as e:
            logger.error(f"Search request failed: {e}")
            return []
        
        # Parse results
        videos = await self._parse_search_results(data)
        
        # Get more results if needed
        while len(videos) < max_results:
            token = extract_continuation_token(data)
            if not token:
                break
                
            next_data = await self._get_continuation(token, language, region_code)
            if not next_data:
                break
                
            more_videos = await self._parse_continuation_results(next_data)
            videos.extend(more_videos)
            data = next_data
            
            await asyncio.sleep(random.uniform(0.5, 1.0))
        
        return videos[:max_results]
    
    async def search_videos(
        self,
        query: str,
        max_results: int = 10,
        **kwargs
    ) -> List[Video]:
        """Search only videos"""
        return await self.search(query, max_results, filter_type="video", **kwargs)
    
    async def search_channels(
        self,
        query: str,
        max_results: int = 10,
        **kwargs
    ) -> List[Channel]:
        """Search only channels"""
        results = await self.search(query, max_results, filter_type="channel", **kwargs)
        channels = []
        for video in results:
            if video.channel_id:
                channels.append(Channel(
                    id=video.channel_id,
                    name=video.channel,
                    url=f"https://www.youtube.com/channel/{video.channel_id}"
                ))
        return channels
    
    async def search_playlists(
        self,
        query: str,
        max_results: int = 10,
        **kwargs
    ) -> List[Playlist]:
        """Search only playlists"""
        results = await self.search(query, max_results, filter_type="playlist", **kwargs)
        return []
    
    async def _parse_search_results(self, data: Dict[str, Any]) -> List[Video]:
        """Parse search results from InnerTube response"""
        videos = []
        
        try:
            # Try different paths for search results
            contents = data.get("contents", {})
            
            # Path 1: Standard search results
            search_results = contents.get("twoColumnSearchResultsRenderer", {})
            primary = search_results.get("primaryContents", {})
            section_list = primary.get("sectionListRenderer", {})
            
            if section_list:
                for section in section_list.get("contents", []):
                    item_section = section.get("itemSectionRenderer", {})
                    for item in item_section.get("contents", []):
                        if "videoRenderer" in item:
                            video = Video.from_renderer(item["videoRenderer"])
                            if video:
                                videos.append(video)
            else:
                # Path 2: Alternative structure
                results = data.get("results", {})
                if results:
                    for item in results.get("items", []):
                        if "videoRenderer" in item:
                            video = Video.from_renderer(item["videoRenderer"])
                            if video:
                                videos.append(video)
                
        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
            # Try HTML fallback parsing
            try:
                renderers = parse_search_results(data)
                for renderer in renderers:
                    if "videoRenderer" in renderer:
                        video = Video.from_renderer(renderer["videoRenderer"])
                        if video:
                            videos.append(video)
            except:
                pass
        
        return videos
    
    async def _get_continuation(
        self,
        token: str,
        language: str = "en",
        region_code: str = "US"
    ) -> Optional[Dict[str, Any]]:
        """Fetch next page of results"""
        context = {
            "client": {
                "hl": language,
                "gl": region_code,
                "clientName": self.client.client_config["clientName"],
                "clientVersion": self.client.client_config["clientVersion"],
                "platform": "DESKTOP"
            }
        }
        
        payload = {
            "context": context,
            "continuation": token
        }
        
        try:
            return await self.client.request("search", payload)
        except Exception as e:
            logger.error(f"Failed to get continuation: {e}")
            return None
    
    async def _parse_continuation_results(
        self,
        data: Dict[str, Any]
    ) -> List[Video]:
        """Parse continuation results"""
        videos = []
        try:
            continuation_contents = data.get("continuationContents", {})
            item_section = continuation_contents.get("itemSectionContinuation", {})
            
            for item in item_section.get("contents", []):
                if "videoRenderer" in item:
                    video = Video.from_renderer(item["videoRenderer"])
                    if video:
                        videos.append(video)
        except Exception as e:
            logger.error(f"Error parsing continuation: {e}")
        return videos
    
    async def close(self):
        """Close client session"""
        await self.client.close()