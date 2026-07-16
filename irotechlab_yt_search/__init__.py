"""
irotechlab-yt-search - YouTube search without official API
"""

__version__ = "0.1.0"
__author__ = "IrotechLab"

from .search import YouTubeSearch
from .video import Video
from .channel import Channel
from .playlist import Playlist
from .video_info import VideoInfo
from .channel_info import ChannelInfo
from .playlist_info import PlaylistInfo
from .exceptions import (
    YouTubeSearchError,
    RequestError,
    ParseError,
    RateLimitError,
    InvalidQueryError,
    VideoUnavailableError,
    ChannelNotFoundError,
    PlaylistNotFoundError,
    VideoNotFoundError,
    AuthenticationError,
    InvalidURLError
)

# Export utility functions
from .utils import (
    get_video_id,
    get_value,
    traverse_obj,  # Added for backwards compatibility
    safe_get,
    parse_duration,
    parse_view_count,
    parse_upload_date,
    generate_user_agent,
    extract_video_id,
    extract_channel_id,
    extract_playlist_id,
    format_duration,
    clean_text,
    random_delay,
    is_valid_youtube_url,
    truncate_text,
    chunks,
    format_number,
    extract_thumbnail_url,
    format_view_count,
    extract_continuation_token,
    parse_search_results,
    clean_url,
    extract_channel_name_from_url,
    get_playability_reason,
    is_video_available,
    get_error_message
)

__all__ = [
    "YouTubeSearch",
    "Video",
    "Channel", 
    "Playlist",
    "VideoInfo",
    "ChannelInfo",
    "PlaylistInfo",
    "YouTubeSearchError",
    "RequestError",
    "ParseError",
    "RateLimitError",
    "InvalidQueryError",
    "VideoUnavailableError",
    "ChannelNotFoundError",
    "PlaylistNotFoundError",
    "VideoNotFoundError",
    "AuthenticationError",
    "InvalidURLError",
    # Utility functions
    "get_video_id",
    "get_value",
    "traverse_obj",  # Added for backwards compatibility
    "safe_get",
    "parse_duration",
    "parse_view_count", 
    "parse_upload_date",
    "generate_user_agent",
    "extract_video_id",
    "extract_channel_id",
    "extract_playlist_id",
    "format_duration",
    "clean_text",
    "random_delay",
    "is_valid_youtube_url",
    "truncate_text",
    "chunks",
    "format_number",
    "extract_thumbnail_url",
    "format_view_count",
    "extract_continuation_token",
    "parse_search_results",
    "clean_url",
    "extract_channel_name_from_url",
    "get_playability_reason",
    "is_video_available",
    "get_error_message"
]