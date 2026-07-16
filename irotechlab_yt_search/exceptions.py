"""Custom exceptions for irotechlab-yt-search"""

class YouTubeSearchError(Exception):
    """Base exception for all YouTube search errors"""
    pass

class RequestError(YouTubeSearchError):
    """Raised when HTTP request fails"""
    pass

class ParseError(YouTubeSearchError):
    """Raised when parsing response fails"""
    pass

class RateLimitError(YouTubeSearchError):
    """Raised when rate limit is exceeded"""
    pass

class InvalidQueryError(YouTubeSearchError):
    """Raised when search query is invalid"""
    pass

class VideoUnavailableError(YouTubeSearchError):
    """Raised when video is unavailable"""
    pass

class ChannelNotFoundError(YouTubeSearchError):
    """Raised when channel is not found"""
    pass

class PlaylistNotFoundError(YouTubeSearchError):
    """Raised when playlist is not found"""
    pass

class VideoNotFoundError(YouTubeSearchError):
    """Raised when video is not found"""
    pass

class AuthenticationError(YouTubeSearchError):
    """Raised when authentication fails"""
    pass

class InvalidURLError(YouTubeSearchError):
    """Raised when URL is invalid"""
    pass