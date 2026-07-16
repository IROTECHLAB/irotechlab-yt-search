"""Playlist information extraction using YouTube's hidden API"""

import re
import json
import copy
import asyncio
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode
from .exceptions import RequestError, ParseError
from .utils import clean_text, get_value

logger = logging.getLogger(__name__)

# Constants from reference code
SEARCH_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
REQUEST_PAYLOAD = {
    "context": {
        "client": {
            "hl": "en",
            "gl": "US",
            "clientName": "WEB",
            "clientVersion": "2.20240425.01.00",
        },
        "user": {"lockedSafetyMode": False},
    }
}


class PlaylistInfo:
    """Playlist information extraction using YouTube's hidden API"""

    def __init__(self, proxy: Optional[str] = None, timeout: int = 15):
        self.proxy = proxy
        self.timeout = timeout
        self.session = None
        self.continuation_key = None

    async def _ensure_session(self):
        if self.session is None:
            import aiohttp
            self.session = aiohttp.ClientSession()
        return self.session

    async def _call_youtube_api(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call YouTube's internal API"""
        session = await self._ensure_session()
        url = f"https://www.youtube.com/youtubei/v1/{endpoint}?key={SEARCH_KEY}"

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

    async def get_playlist_info(self, playlist_id: str, max_videos: int = 50) -> Optional[Dict[str, Any]]:
        """Get detailed information about a playlist"""
        if not playlist_id:
            raise ValueError("Playlist ID cannot be empty")

        # Try multiple methods
        methods = [
            self._get_playlist_from_api,
            self._get_playlist_from_html,
            self._get_playlist_from_mobile_html
        ]
        
        for method in methods:
            try:
                result = await method(playlist_id, max_videos)
                if result and result.get('videos'):
                    return result
            except Exception as e:
                logger.warning(f"Method {method.__name__} failed: {e}")
                continue
        
        # If all methods fail but we have some data, return what we have
        try:
            return await self._get_playlist_from_mobile_html(playlist_id, max_videos)
        except:
            return None

    async def _get_playlist_from_api(self, playlist_id: str, max_videos: int) -> Optional[Dict[str, Any]]:
        """Get playlist data from YouTube API"""
        browse_id = f"VL{playlist_id}" if not playlist_id.startswith("VL") else playlist_id
        
        payload = copy.deepcopy(REQUEST_PAYLOAD)
        payload["browseId"] = browse_id
        
        try:
            data = await self._call_youtube_api("browse", payload)
            return self._parse_playlist_data(data, playlist_id, max_videos)
        except Exception as e:
            raise RequestError(f"Failed to get playlist from API: {e}")

    async def _get_playlist_from_html(self, playlist_id: str, max_videos: int) -> Optional[Dict[str, Any]]:
        """Extract playlist data from desktop HTML page"""
        session = await self._ensure_session()
        
        url = f"https://www.youtube.com/playlist?list={playlist_id}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        async with session.get(url, headers=headers, proxy=self.proxy, timeout=self.timeout) as response:
            if response.status != 200:
                raise RequestError(f"Failed to fetch playlist: HTTP {response.status}")
            
            html = await response.text()
            
            # Extract from ytInitialData
            match = re.search(r'var ytInitialData\s*=\s*({.+?});', html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    return self._parse_playlist_data(data, playlist_id, max_videos)
                except:
                    pass
            
            # Fallback to direct HTML extraction
            return self._extract_playlist_from_html_direct(html, playlist_id, max_videos)

    async def _get_playlist_from_mobile_html(self, playlist_id: str, max_videos: int) -> Optional[Dict[str, Any]]:
        """Extract playlist data from mobile HTML page (most reliable)"""
        session = await self._ensure_session()
        
        url = f"https://m.youtube.com/playlist?list={playlist_id}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        async with session.get(url, headers=headers, proxy=self.proxy, timeout=self.timeout) as response:
            if response.status != 200:
                raise RequestError(f"Failed to fetch mobile playlist: HTTP {response.status}")
            
            html = await response.text()
            return self._extract_mobile_playlist(html, playlist_id, max_videos)

    def _parse_playlist_data(self, data: Dict[str, Any], playlist_id: str, max_videos: int) -> Dict[str, Any]:
        """Parse regular playlist data from API response"""
        result = {
            "id": playlist_id,
            "url": f"https://www.youtube.com/playlist?list={playlist_id}",
            "title": "",
            "author": "",
            "author_id": "",
            "video_count": "0",
            "view_count": "",
            "thumbnail": "",
            "thumbnails": [],
            "videos": []
        }

        try:
            # Get sidebar info for metadata
            sidebar = data.get("sidebar", {})
            playlist_sidebar = sidebar.get("playlistSidebarRenderer", {})
            sidebar_items = playlist_sidebar.get("items", [])
            
            primary_info = None
            secondary_info = None
            
            for item in sidebar_items:
                if "playlistSidebarPrimaryInfoRenderer" in item:
                    primary_info = item["playlistSidebarPrimaryInfoRenderer"]
                elif "playlistSidebarSecondaryInfoRenderer" in item:
                    secondary_info = item["playlistSidebarSecondaryInfoRenderer"]

            if primary_info:
                result["title"] = get_value(primary_info, ["title", "runs", 0, "text"], "")
                result["video_count"] = get_value(primary_info, ["stats", 0, "runs", 0, "text"], "0")
                result["view_count"] = get_value(primary_info, ["stats", 1, "simpleText"], "")
                thumbnails = get_value(primary_info, ["thumbnailRenderer", "playlistVideoThumbnailRenderer", "thumbnail", "thumbnails"], [])
                result["thumbnails"] = thumbnails
                if thumbnails:
                    result["thumbnail"] = thumbnails[-1].get("url", "")

            if secondary_info:
                video_owner = get_value(secondary_info, ["videoOwner", "videoOwnerRenderer"], {})
                result["author"] = get_value(video_owner, ["title", "runs", 0, "text"], "")
                result["author_id"] = get_value(video_owner, ["title", "runs", 0, "navigationEndpoint", "browseEndpoint", "browseId"], "")

            # Get videos - try multiple paths
            videos_data = None
            
            # Path 1: Standard path
            videos_data = get_value(
                data,
                ["contents", "twoColumnBrowseResultsRenderer", "tabs", 0, 
                 "tabRenderer", "content", "sectionListRenderer", "contents", 0,
                 "itemSectionRenderer", "contents", 0, "playlistVideoListRenderer", "contents"],
                []
            )
            
            # Path 2: Alternative path
            if not videos_data:
                videos_data = get_value(
                    data,
                    ["contents", "twoColumnBrowseResultsRenderer", "tabs", 0,
                     "tabRenderer", "content", "sectionListRenderer", "contents", 0,
                     "playlistVideoListRenderer", "contents"],
                    []
                )
            
            # Path 3: Direct renderer
            if not videos_data:
                playlist_renderer = get_value(
                    data,
                    ["contents", "twoColumnBrowseResultsRenderer", "tabs", 0,
                     "tabRenderer", "content", "sectionListRenderer", "contents", 0,
                     "itemSectionRenderer", "contents", 0, "playlistVideoListRenderer"],
                    {}
                )
                videos_data = playlist_renderer.get("contents", [])

            # Extract videos
            videos = []
            for item in videos_data:
                if len(videos) >= max_videos:
                    break
                    
                if "continuationItemRenderer" in item:
                    continue
                    
                if "playlistVideoRenderer" in item:
                    video = item["playlistVideoRenderer"]
                    video_id = video.get("videoId", "")
                    if video_id:
                        title = get_value(video, ["title", "runs", 0, "text"], "")
                        if not title:
                            title = get_value(video, ["title", "simpleText"], "")
                        
                        duration = get_value(video, ["lengthText", "simpleText"], "")
                        views = get_value(video, ["viewCountText", "simpleText"], "")
                        thumbnails = get_value(video, ["thumbnail", "thumbnails"], [])
                        thumbnail = thumbnails[-1].get("url", "") if thumbnails else ""
                        
                        videos.append({
                            "id": video_id,
                            "title": clean_text(title) if title else "Unknown",
                            "duration": duration,
                            "views": views,
                            "thumbnail": thumbnail,
                            "url": f"https://www.youtube.com/watch?v={video_id}"
                        })

            result["videos"] = videos

            return result

        except Exception as e:
            logger.error(f"Error parsing playlist data: {e}")
            raise ParseError(f"Failed to parse playlist data: {e}")

    def _extract_mobile_playlist(self, html: str, playlist_id: str, max_videos: int) -> Dict[str, Any]:
        """Extract playlist data from mobile HTML"""
        result = {
            "id": playlist_id,
            "url": f"https://www.youtube.com/playlist?list={playlist_id}",
            "title": "",
            "author": "",
            "author_id": "",
            "video_count": "0",
            "view_count": "",
            "thumbnail": "",
            "thumbnails": [],
            "videos": []
        }

        try:
            # Extract title
            title_match = re.search(r'<meta name="title" content="([^"]+)"', html)
            if title_match:
                result["title"] = title_match.group(1).strip().replace(" - YouTube", "")
            
            # Extract author
            author_match = re.search(r'"ownerText":\{"runs":\[\{"text":"([^"]+)"', html)
            if author_match:
                result["author"] = clean_text(author_match.group(1))
            
            # Extract video count
            count_match = re.search(r'(\d+)\s*videos?', html, re.IGNORECASE)
            if count_match:
                result["video_count"] = count_match.group(1)
            
            # Extract view count
            view_match = re.search(r'(\d+[\.,]?\d*[KMB]?)\s*views?', html, re.IGNORECASE)
            if view_match:
                result["view_count"] = view_match.group(1)

            # Extract videos - multiple patterns
            videos = []
            seen_ids = set()

            # Pattern 1: Standard video entries
            video_pattern = r'"videoId":"([^"]+)".*?"title":{"runs":\[\{"text":"([^"]+)"'
            matches = re.findall(video_pattern, html, re.DOTALL)
            
            for video_id, title in matches:
                if len(videos) >= max_videos:
                    break
                if video_id not in seen_ids:
                    seen_ids.add(video_id)
                    
                    duration = ""
                    duration_match = re.search(rf'"videoId":"{video_id}".*?"lengthText":{{"simpleText":"([^"]+)"', html)
                    if duration_match:
                        duration = duration_match.group(1)
                    
                    videos.append({
                        "id": video_id,
                        "title": clean_text(title) if title else "Unknown",
                        "duration": duration,
                        "views": "",
                        "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                        "url": f"https://www.youtube.com/watch?v={video_id}"
                    })

            # Pattern 2: Simple video links
            if len(videos) < max_videos:
                video_links = re.findall(r'<a[^>]*href="\/watch\?v=([a-zA-Z0-9_-]{11})"[^>]*>([^<]+)<\/a>', html)
                for video_id, title in video_links:
                    if len(videos) >= max_videos:
                        break
                    if video_id not in seen_ids:
                        seen_ids.add(video_id)
                        videos.append({
                            "id": video_id,
                            "title": clean_text(title) if title else "Unknown",
                            "duration": "",
                            "views": "",
                            "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                            "url": f"https://www.youtube.com/watch?v={video_id}"
                        })

            result["videos"] = videos
            if videos and result["video_count"] == "0":
                result["video_count"] = str(len(videos))

            return result

        except Exception as e:
            logger.error(f"Error extracting mobile playlist: {e}")
            return result

    def _extract_playlist_from_html_direct(self, html: str, playlist_id: str, max_videos: int) -> Dict[str, Any]:
        """Extract playlist data directly from HTML using regex"""
        result = {
            "id": playlist_id,
            "url": f"https://www.youtube.com/playlist?list={playlist_id}",
            "title": "",
            "author": "",
            "author_id": "",
            "video_count": "0",
            "view_count": "",
            "thumbnail": "",
            "thumbnails": [],
            "videos": []
        }

        try:
            # Extract title
            title_match = re.search(r'<title>(.*?)</title>', html)
            if title_match:
                result["title"] = title_match.group(1).strip().replace(" - YouTube", "")
            
            # Extract videos from the page
            videos = []
            seen_ids = set()
            
            # Look for video entries
            video_patterns = [
                r'"videoId":"([^"]+)".*?"title":{"runs":\[\{"text":"([^"]+)"',
                r'"videoId":"([^"]+)".*?"title":{"simpleText":"([^"]+)"',
            ]
            
            for pattern in video_patterns:
                matches = re.findall(pattern, html, re.DOTALL)
                for video_id, title in matches:
                    if len(videos) >= max_videos:
                        break
                    if video_id not in seen_ids:
                        seen_ids.add(video_id)
                        videos.append({
                            "id": video_id,
                            "title": clean_text(title) if title else "Unknown",
                            "duration": "",
                            "views": "",
                            "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                            "url": f"https://www.youtube.com/watch?v={video_id}"
                        })
            
            result["videos"] = videos
            if videos:
                result["video_count"] = str(len(videos))
            
            return result

        except Exception as e:
            logger.error(f"Error extracting from HTML: {e}")
            return result

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None