"""Utility functions for irotechlab-yt-search"""

import re
import time
import random
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs


def get_video_id(video_link: str) -> Optional[str]:
    """
    Extract video ID from YouTube URL or return the ID if already extracted
    
    Examples:
        "https://www.youtube.com/watch?v=abc123" -> "abc123"
        "https://youtu.be/abc123" -> "abc123"
        "abc123" -> "abc123"
    """
    if not video_link:
        return None
    
    # If it's already just the ID
    if re.match(r'^[\w-]{11}$', video_link):
        return video_link
    
    # Try to extract from URL
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([\w-]+)',
        r'(?:youtu\.be\/)([\w-]+)',
        r'(?:youtube\.com\/embed\/)([\w-]+)',
        r'(?:youtube\.com\/v\/)([\w-]+)',
        r'(?:youtube\.com\/shorts\/)([\w-]+)',
        r'(?:youtube\.com\/watch\?.*v=)([\w-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, video_link)
        if match:
            return match.group(1)
    
    return None


def get_value(source: Dict[str, Any], path: List[str], default: Any = None) -> Any:
    """
    Safely extracts a value from a nested dictionary using a list of keys.
    This is the core utility for navigating YouTube's complex JSON responses.
    
    Examples:
        get_value(data, ["videoDetails", "title"], "Unknown")
        get_value(data, ["contents", "twoColumnSearchResultsRenderer", "primaryContents"])
    """
    result = source
    try:
        for key in path:
            if isinstance(result, dict):
                result = result.get(key)
                if result is None:
                    return default
            elif isinstance(result, list):
                # If the key is an integer, treat it as an index
                if isinstance(key, int) and 0 <= key < len(result):
                    result = result[key]
                else:
                    return default
            else:
                return default
        return result if result is not None else default
    except (KeyError, TypeError, IndexError, AttributeError):
        return default


# Alias for get_value (for backwards compatibility)
traverse_obj = get_value


def safe_get(data: Dict, *keys, default=None):
    """
    Safely get nested dictionary value using variable arguments.
    Alias for get_value with different parameter style.
    
    Examples:
        safe_get(data, "contents", "twoColumnSearchResultsRenderer", "primaryContents")
        safe_get(data, "videoDetails", "title", default="Unknown")
    """
    return get_value(data, list(keys), default)


def parse_duration(duration_str: str) -> Optional[int]:
    """
    Parse YouTube duration string to seconds
    
    Examples:
        "10:30" -> 630
        "1:10:30" -> 4230
        "10 min" -> 600
        "10:30:15" -> 37815
        "184" -> 184
    """
    if not duration_str:
        return None
    
    # Clean the string
    duration_str = duration_str.replace(" min", "").replace(" sec", "").strip()
    
    # If it's just a number (seconds)
    if duration_str.isdigit():
        return int(duration_str)
    
    # Split by colon
    parts = duration_str.split(":")
    
    try:
        if len(parts) == 1:
            # Single number - could be seconds or minutes
            return int(parts[0])
        elif len(parts) == 2:
            # MM:SS format
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            # HH:MM:SS format
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        else:
            return None
    except (ValueError, TypeError):
        return None


def parse_view_count(view_str: str) -> Optional[int]:
    """
    Parse YouTube view count string to integer
    
    Examples:
        "1.2M views" -> 1200000
        "1,234,567 views" -> 1234567
        "1.2B views" -> 1200000000
        "10K views" -> 10000
        "54284943" -> 54284943
    """
    if not view_str:
        return None
    
    # Remove "views" and clean
    view_str = view_str.replace(" views", "").strip()
    
    try:
        # Handle billion (B)
        if "B" in view_str:
            return int(float(view_str.replace("B", "").strip()) * 1_000_000_000)
        # Handle million (M)
        elif "M" in view_str:
            return int(float(view_str.replace("M", "").strip()) * 1_000_000)
        # Handle thousand (K)
        elif "K" in view_str:
            return int(float(view_str.replace("K", "").strip()) * 1_000)
        # Handle plain number with commas
        else:
            return int(view_str.replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def parse_upload_date(date_str: str) -> Optional[datetime]:
    """
    Parse YouTube upload date string to datetime
    
    Examples:
        "2 years ago" -> datetime(2022, ...)
        "Streamed 3 months ago" -> datetime(2023, ...)
        "Jan 1, 2024" -> datetime(2024, 1, 1)
        "2024-01-01" -> datetime(2024, 1, 1)
        "2024-01-01T00:00:00Z" -> datetime(2024, 1, 1)
    """
    if not date_str:
        return None
    
    date_str = date_str.lower().strip()
    now = datetime.now()
    
    # Try common patterns
    patterns = {
        r'(\d+)\s+second': 'seconds',
        r'(\d+)\s+minute': 'minutes', 
        r'(\d+)\s+hour': 'hours',
        r'(\d+)\s+day': 'days',
        r'(\d+)\s+week': 'weeks',
        r'(\d+)\s+month': 'months',
        r'(\d+)\s+year': 'years'
    }
    
    for pattern, unit in patterns.items():
        match = re.search(pattern, date_str)
        if match:
            try:
                value = int(match.group(1))
                kwargs = {unit: value}
                return now - timedelta(**kwargs)
            except (ValueError, TypeError):
                continue
    
    # Try parsing specific date formats
    date_formats = [
        "%b %d, %Y",  # Jan 1, 2024
        "%B %d, %Y",  # January 1, 2024
        "%Y-%m-%d",   # 2024-01-01
        "%d %b %Y",   # 01 Jan 2024
        "%Y-%m-%dT%H:%M:%SZ",  # 2024-01-01T00:00:00Z
        "%Y-%m-%dT%H:%M:%S.%fZ",  # 2024-01-01T00:00:00.000Z
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def generate_user_agent() -> str:
    """Generate random user agent to avoid detection"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
    ]
    return random.choice(user_agents)


def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL (alias for get_video_id)"""
    return get_video_id(url)


def extract_channel_id(url: str) -> Optional[str]:
    """Extract channel ID from YouTube URL"""
    if not url:
        return None
    
    patterns = [
        r'(?:youtube\.com\/channel\/)([\w-]+)',
        r'(?:youtube\.com\/c\/)([\w-]+)',
        r'(?:youtube\.com\/@)([\w-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def extract_playlist_id(url: str) -> Optional[str]:
    """Extract playlist ID from YouTube URL"""
    if not url:
        return None
    
    pattern = r'(?:youtube\.com\/playlist\?list=)([\w-]+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    
    # Try with parse_qs
    parsed = urlparse(url)
    if parsed.hostname in ['www.youtube.com', 'youtube.com']:
        params = parse_qs(parsed.query)
        if 'list' in params:
            return params['list'][0]
    
    return None


def format_duration(seconds: int) -> str:
    """Format seconds to HH:MM:SS or MM:SS"""
    if not seconds:
        return "0:00"
    
    seconds = int(seconds)
    if seconds < 3600:
        return f"{seconds // 60:02d}:{seconds % 60:02d}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def clean_text(text: str) -> str:
    """Clean text by removing extra spaces and special characters"""
    if not text:
        return ""
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def random_delay(min_seconds: float = 0.5, max_seconds: float = 2.0) -> None:
    """Sleep for random duration to avoid rate limiting"""
    time.sleep(random.uniform(min_seconds, max_seconds))


def is_valid_youtube_url(url: str) -> bool:
    """Check if a URL is a valid YouTube URL"""
    if not url:
        return False
    
    patterns = [
        r'(?:www\.)?youtube\.com',
        r'(?:www\.)?youtu\.be',
        r'(?:www\.)?youtube\.com\/watch',
        r'(?:www\.)?youtube\.com\/embed',
        r'(?:www\.)?youtube\.com\/shorts',
        r'(?:www\.)?youtube\.com\/playlist',
        r'(?:www\.)?youtube\.com\/channel',
        r'(?:www\.)?youtube\.com\/c\/',
        r'(?:www\.)?youtube\.com\/@',
    ]
    
    for pattern in patterns:
        if re.search(pattern, url):
            return True
    return False


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def chunks(lst: List, n: int):
    """Yield successive n-sized chunks from list"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def format_number(num: int) -> str:
    """Format number with K, M, B suffixes"""
    if not num:
        return "0"
    
    num = int(num)
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return str(num)


def extract_thumbnail_url(thumbnails: List[Dict[str, Any]], quality: str = "high") -> Optional[str]:
    """Extract thumbnail URL from thumbnails list"""
    if not thumbnails:
        return None
    
    if quality == "high":
        return thumbnails[-1].get("url") if thumbnails else None
    elif quality == "medium":
        mid = len(thumbnails) // 2
        return thumbnails[mid].get("url") if thumbnails else None
    elif quality == "low":
        return thumbnails[0].get("url") if thumbnails else None
    else:
        return thumbnails[-1].get("url") if thumbnails else None


def format_view_count(view_count: Union[int, str]) -> str:
    """Format view count to human-readable string"""
    if isinstance(view_count, str):
        view_count = parse_view_count(view_count)
    
    if not view_count:
        return "0 views"
    
    num = int(view_count)
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B views"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M views"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K views"
    else:
        return f"{num} views"


def extract_continuation_token(response_data: Dict[str, Any]) -> Optional[str]:
    """
    Extract continuation token from YouTube response for pagination.
    This is used to get the next page of search results.
    
    Examples:
        token = extract_continuation_token(data)
        if token:
            next_page = await get_next_page(token)
    """
    # Try different paths where continuation token might be
    paths = [
        # Search results continuation
        ["contents", "twoColumnSearchResultsRenderer", "primaryContents", 
         "sectionListRenderer", "contents", -1, "continuationItemRenderer", 
         "continuationEndpoint", "continuationCommand", "token"],
        
        # Alternative search continuation path
        ["contents", "twoColumnSearchResultsRenderer", "primaryContents", 
         "sectionListRenderer", "continuations", 0, "nextContinuationData", "continuation"],
        
        # Playlist continuation
        ["continuationContents", "playlistContinuation", "continuations", 0, 
         "nextContinuationData", "continuation"],
        
        # Comments continuation
        ["continuationContents", "commentSectionContinuation", "continuations", 0, 
         "nextContinuationData", "continuation"],
    ]
    
    for path in paths:
        token = get_value(response_data, path)
        if token:
            return token
    
    return None


def parse_search_results(response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse search results from YouTube response.
    Returns a list of video renderer objects.
    """
    results = []
    
    # Path to search results
    path = [
        "contents", "twoColumnSearchResultsRenderer", "primaryContents",
        "sectionListRenderer", "contents"
    ]
    
    contents = get_value(response_data, path, [])
    
    if not contents:
        return results
    
    for item in contents:
        if "itemSectionRenderer" in item:
            section = item["itemSectionRenderer"]
            for content in section.get("contents", []):
                if "videoRenderer" in content:
                    results.append(content["videoRenderer"])
                elif "channelRenderer" in content:
                    results.append(content["channelRenderer"])
                elif "playlistRenderer" in content:
                    results.append(content["playlistRenderer"])
    
    return results


def clean_url(url: str) -> str:
    """
    Clean YouTube URL by removing unnecessary parameters
    
    Examples:
        "https://www.youtube.com/watch?v=abc123&feature=share" -> "https://www.youtube.com/watch?v=abc123"
    """
    if not url:
        return url
    
    parsed = urlparse(url)
    if parsed.hostname in ['www.youtube.com', 'youtube.com']:
        params = parse_qs(parsed.query)
        if 'v' in params:
            return f"https://www.youtube.com/watch?v={params['v'][0]}"
    
    return url


def extract_channel_name_from_url(url: str) -> Optional[str]:
    """
    Extract channel name from YouTube channel URL
    
    Examples:
        "https://www.youtube.com/@CodeWithHarry" -> "CodeWithHarry"
        "https://www.youtube.com/c/ProgrammingwithMosh" -> "ProgrammingwithMosh"
    """
    if not url:
        return None
    
    patterns = [
        r'(?:youtube\.com\/@)([^/?]+)',
        r'(?:youtube\.com\/c\/)([^/?]+)',
        r'(?:youtube\.com\/user\/)([^/?]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def get_playability_reason(playability_status: Dict[str, Any]) -> Optional[str]:
    """
    Get the reason why a video is not available
    
    Args:
        playability_status: The playabilityStatus object from InnerTube response
    
    Returns:
        Reason string or None if video is available
    """
    if not playability_status:
        return "No playability status"
    
    if playability_status.get("status") == "OK":
        return None
    
    return playability_status.get("reason", "Unknown reason")


def is_video_available(playability_status: Dict[str, Any]) -> bool:
    """
    Check if video is available based on playability status
    
    Args:
        playability_status: The playabilityStatus object from InnerTube response
    
    Returns:
        True if video is available, False otherwise
    """
    if not playability_status:
        return False
    
    status = playability_status.get("status", "")
    return status == "OK"


# Dictionary of common YouTube error messages
YOUTUBE_ERRORS = {
    "video_unavailable": "This video is unavailable",
    "private_video": "This video is private",
    "age_restricted": "This video is age-restricted",
    "not_found": "Video not found",
    "blocked": "This video is blocked in your country",
    "removed": "This video has been removed",
    "copyright": "This video contains content from copyright holders",
    "login_required": "You need to log in to view this video",
    "embedding_disabled": "Video embedding is disabled",
}


def get_error_message(error_code: str) -> str:
    """Get human-readable error message from error code"""
    return YOUTUBE_ERRORS.get(error_code, "Unknown error occurred")