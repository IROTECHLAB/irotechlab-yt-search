"""Channel information extraction using YouTube's hidden API"""

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


class ChannelInfo:
    """Channel information extraction using YouTube's hidden API"""

    def __init__(self, proxy: Optional[str] = None, timeout: int = 15):
        """
        Initialize channel info extractor
        
        Args:
            proxy: Proxy URL (optional)
            timeout: Request timeout in seconds
        """
        self.proxy = proxy
        self.timeout = timeout
        self.session = None
        self.continuation_key = None

    async def _ensure_session(self):
        """Get or create HTTP session"""
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

    async def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a channel
        
        Args:
            channel_id: YouTube channel ID (UC... format) or handle (@username)
            
        Returns:
            Dictionary with channel metadata
        """
        if not channel_id:
            raise ValueError("Channel ID cannot be empty")

        # Try HTML extraction first (more reliable)
        try:
            return await self._get_channel_from_html(channel_id)
        except Exception as e:
            logger.warning(f"HTML extraction failed: {e}, trying API...")
            return await self._get_channel_from_api(channel_id)

    async def _get_channel_from_html(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Extract channel data from HTML page"""
        session = await self._ensure_session()
        
        # Construct URL based on channel ID type
        if channel_id.startswith("@"):
            url = f"https://www.youtube.com/{channel_id}"
        else:
            url = f"https://www.youtube.com/channel/{channel_id}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        async with session.get(url, headers=headers, proxy=self.proxy, timeout=self.timeout) as response:
            if response.status != 200:
                raise RequestError(f"Failed to fetch channel page: HTTP {response.status}")

            html = await response.text()

            # Try multiple methods to extract channel data
            # Method 1: Extract from ytInitialData
            match = re.search(r'var ytInitialData\s*=\s*({.+?});', html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    result = self._parse_channel_data(data, channel_id)
                    if result and result.get('name'):
                        return result
                except json.JSONDecodeError:
                    pass

            # Method 2: Extract with regex fallback
            return self._extract_channel_from_regex(html, channel_id)

    async def _get_channel_from_api(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get channel data from YouTube API"""
        payload = copy.deepcopy(REQUEST_PAYLOAD)
        
        # Determine browse ID
        if channel_id.startswith("@"):
            payload["browseId"] = channel_id
        else:
            payload["browseId"] = channel_id

        try:
            data = await self._call_youtube_api("browse", payload)
            return self._parse_channel_data(data, channel_id)
        except Exception as e:
            raise RequestError(f"Failed to get channel from API: {e}")

    def _parse_channel_data(self, data: Dict[str, Any], channel_id: str) -> Dict[str, Any]:
        """Parse channel data from API response"""
        result = {
            "id": channel_id,
            "name": "",
            "url": "",
            "thumbnail": "",
            "thumbnails": [],
            "subscribers": "",
            "subscriber_count": None,
            "video_count": "",
            "view_count": "",
            "description": "",
            "joined_date": "",
            "country": "",
            "banner_url": "",
            "links": [],
            "is_verified": False
        }

        try:
            # Get channel metadata from various sources
            # Source 1: channelMetadataRenderer
            channel_metadata = get_value(data, ["metadata", "channelMetadataRenderer"], {})
            if channel_metadata:
                result["id"] = channel_metadata.get("externalId", channel_id)
                result["name"] = channel_metadata.get("title", "")
                result["url"] = channel_metadata.get("channelUrl", "")
                result["description"] = channel_metadata.get("description", "")
                
                # Get thumbnails
                thumbnails = get_value(channel_metadata, ["avatar", "thumbnails"], [])
                if thumbnails:
                    result["thumbnails"] = thumbnails
                    result["thumbnail"] = thumbnails[-1].get("url", "")

            # Source 2: c4TabbedHeaderRenderer
            header = get_value(data, ["header", "c4TabbedHeaderRenderer"], {})
            if header:
                if not result["name"]:
                    result["name"] = header.get("title", "")
                
                # Get subscriber count
                subscriber_text = get_value(header, ["subscriberCountText", "simpleText"], "")
                if subscriber_text:
                    result["subscribers"] = subscriber_text
                
                # Get banner
                banners = get_value(header, ["banner", "thumbnails"], [])
                if banners:
                    result["banner_url"] = banners[-1].get("url", "")
                
                # Get thumbnails if not already set
                if not result["thumbnails"]:
                    avatar = get_value(header, ["avatar", "thumbnails"], [])
                    if avatar:
                        result["thumbnails"] = avatar
                        result["thumbnail"] = avatar[-1].get("url", "")

            # Source 3: microformatDataRenderer
            microformat = get_value(data, ["microformat", "microformatDataRenderer"], {})
            if microformat:
                if not result["url"]:
                    result["url"] = microformat.get("urlCanonical", "")
                if not result["description"]:
                    result["description"] = microformat.get("description", "")
                if not result["thumbnails"]:
                    thumbnails = get_value(microformat, ["thumbnail", "thumbnails"], [])
                    if thumbnails:
                        result["thumbnails"] = thumbnails
                        result["thumbnail"] = thumbnails[-1].get("url", "")

            # Get About tab data
            about_data = None
            tabs = get_value(data, ["contents", "twoColumnBrowseResultsRenderer", "tabs"], [])
            
            for tab in tabs:
                tab_title = get_value(tab, ["tabRenderer", "title"], "")
                if tab_title == "About":
                    tab_renderer = tab.get("tabRenderer", {})
                    about_data = get_value(
                        tab_renderer,
                        ["content", "sectionListRenderer", "contents", 0, 
                         "itemSectionRenderer", "contents", 0, "channelAboutFullMetadataRenderer"],
                        {}
                    )
                    break

            if about_data:
                result["view_count"] = get_value(about_data, ["viewCountText", "simpleText"], "")
                result["video_count"] = get_value(about_data, ["videoCountText", "simpleText"], "")
                
                joined_date = get_value(about_data, ["joinedDateText", "runs", -1, "text"], "")
                if not joined_date:
                    joined_date = get_value(about_data, ["joinedDateText", "simpleText"], "")
                result["joined_date"] = joined_date
                
                result["country"] = get_value(about_data, ["country", "simpleText"], "")
                
                # Get description if not already set
                if not result["description"]:
                    result["description"] = get_value(about_data, ["description", "simpleText"], "")

            # Alternative about data location (new YouTube layout)
            if not about_data:
                about_data = get_value(
                    data,
                    ["contents", "twoColumnBrowseResultsRenderer", "tabs", 0,
                     "tabRenderer", "content", "sectionListRenderer", "contents", 0,
                     "itemSectionRenderer", "contents", 0, "aboutChannelRenderer", 
                     "metadata", "aboutChannelMetadataViewModel"],
                    {}
                )
                if about_data:
                    result["view_count"] = about_data.get("viewCount", "")
                    result["joined_date"] = about_data.get("joinedDateText", "")
                    result["country"] = about_data.get("country", "")
                    result["description"] = about_data.get("description", "")

            # Check if verified
            if "badges" in header:
                for badge in header.get("badges", []):
                    if "metadataBadgeRenderer" in badge:
                        if badge["metadataBadgeRenderer"].get("style") == "BADGE_STYLE_TYPE_VERIFIED":
                            result["is_verified"] = True

            # Clean up
            result["name"] = clean_text(result["name"])
            result["description"] = clean_text(result["description"])
            
            # Set URL if not set
            if not result["url"]:
                if channel_id.startswith("@"):
                    result["url"] = f"https://www.youtube.com/{channel_id}"
                else:
                    result["url"] = f"https://www.youtube.com/channel/{channel_id}"

            return result

        except Exception as e:
            logger.error(f"Error parsing channel data: {e}")
            raise ParseError(f"Failed to parse channel data: {e}")

    def _extract_channel_from_regex(self, html: str, channel_id: str) -> Dict[str, Any]:
        """Fallback: Extract channel data using regex patterns"""
        result = {
            "id": channel_id,
            "name": "",
            "url": "",
            "thumbnail": "",
            "thumbnails": [],
            "subscribers": "",
            "subscriber_count": None,
            "video_count": "",
            "view_count": "",
            "description": "",
            "joined_date": "",
            "country": "",
            "banner_url": "",
            "links": [],
            "is_verified": False
        }

        try:
            # Extract channel name
            name_match = re.search(r'"name":"([^"]+)"', html)
            if name_match:
                result["name"] = clean_text(name_match.group(1))
            else:
                # Try alternative pattern
                name_match = re.search(r'"title":"([^"]+)"', html)
                if name_match:
                    result["name"] = clean_text(name_match.group(1))
            
            # Set URL
            if channel_id.startswith("@"):
                result["url"] = f"https://www.youtube.com/{channel_id}"
            else:
                result["url"] = f"https://www.youtube.com/channel/{channel_id}"
            
            # Extract subscriber count
            subs_match = re.search(r'(\d+[\.,]?\d*[KMB]?)\s*subscribers?', html, re.IGNORECASE)
            if subs_match:
                result["subscribers"] = subs_match.group(1)
            
            # Extract video count
            video_match = re.search(r'(\d+[\.,]?\d*[KMB]?)\s*videos?', html, re.IGNORECASE)
            if video_match:
                result["video_count"] = video_match.group(1)
            
            # Extract view count
            view_match = re.search(r'(\d+[\.,]?\d*[KMB]?)\s*views?', html, re.IGNORECASE)
            if view_match:
                result["view_count"] = view_match.group(1)
            
            # Extract description
            desc_match = re.search(r'"description":"([^"]+)"', html)
            if desc_match:
                result["description"] = clean_text(desc_match.group(1))
            
            # Extract joined date
            joined_match = re.search(r'Joined\s+(\w+\s+\d+,\s+\d+)', html, re.IGNORECASE)
            if joined_match:
                result["joined_date"] = joined_match.group(1)
            
            # Extract thumbnail
            thumb_match = re.search(r'"avatar".*?"thumbnails":\[\{"url":"([^"]+)"', html)
            if thumb_match:
                result["thumbnail"] = thumb_match.group(1)
                result["thumbnails"] = [{"url": thumb_match.group(1)}]
            
            # Extract banner
            banner_match = re.search(r'"banner".*?"thumbnails":\[\{"url":"([^"]+)"', html)
            if banner_match:
                result["banner_url"] = banner_match.group(1)
            
            # Check if verified
            if "Verified" in html:
                result["is_verified"] = True

        except Exception as e:
            logger.warning(f"Error extracting channel with regex: {e}")

        return result

    async def get_channel_videos(self, channel_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get videos from a channel
        
        Args:
            channel_id: YouTube channel ID or handle
            max_results: Maximum number of videos to return
            
        Returns:
            List of video dictionaries
        """
        from .search import YouTubeSearch
        search = YouTubeSearch(proxy=self.proxy)
        
        try:
            # Search for videos from this channel
            videos = await search.search(
                query=f"channel:{channel_id}",
                max_results=max_results,
                filter_type="video"
            )
            
            # Convert Video objects to dictionaries
            result = []
            for video in videos:
                result.append({
                    "id": video.id,
                    "title": video.title,
                    "channel": video.channel,
                    "channel_id": video.channel_id,
                    "url": video.url,
                    "thumbnail": video.thumbnail,
                    "duration": video.duration,
                    "duration_seconds": video.duration_seconds,
                    "views": video.views,
                    "view_count": video.view_count,
                    "published": video.published
                })
            
            return result
        finally:
            await search.close()

    async def close(self):
        """Close client session"""
        if self.session:
            await self.session.close()
            self.session = None