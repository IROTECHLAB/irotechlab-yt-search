# irotechlab-yt-search

[![PyPI version](https://badge.fury.io/py/irotechlab-yt-search.svg)](https://badge.fury.io/py/irotechlab-yt-search)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**YouTube search without official API - fast, reliable, and completely free.**

## 📌 Features

- 🔍 **Search videos, channels, and playlists** without API key
- ⚡ **Async/await support** for high performance
- 🎯 **Filter by type** (video, channel, playlist, live, movie)
- 📊 **Sort by** relevance, upload date, view count, rating
- 🌍 **Region and language support**
- 🔄 **Pagination** for unlimited results
- 📹 **Video info extraction** (title, channel, views, likes, comments)
- 💬 **Comment scraping** with replies
- 📑 **Chapter extraction**
- 🛡️ **Rate limiting and retry logic**
- 📦 **Clean dataclass models** (Video, Channel, Playlist)

## 📦 Installation

```bash
pip install irotechlab-yt-search
```

Or install from source:

```bash
git clone https://github.com/irotechlab/irotechlab-yt-search
cd irotechlab-yt-search
pip install -e .
```

## 🚀 Quick Start

```python
import asyncio
from irotechlab_yt_search import YouTubeSearch

async def main():
    search = YouTubeSearch()
    
    # Search for videos
    videos = await search.search("python programming", max_results=5)
    
    for video in videos:
        print(f"{video.title}")
        print(f"  Channel: {video.channel}")
        print(f"  Views: {video.views}")
        print(f"  URL: {video.url}\n")
    
    await search.close()

asyncio.run(main())
```

## 📹 Video Info

```python
from irotechlab_yt_search import VideoInfo, extract_video_id

async def get_video_info():
    info = VideoInfo()
    
    video_url = "https://youtube.com/watch?v=VIDEO_ID"
    video_id = extract_video_id(video_url)
    
    details = await info.get_video_info(video_id)
    
    print(f"Title: {details['title']}")
    print(f"Views: {details['views']}")
    print(f"Likes: {details['likes']}")
    print(f"Comments: {details['comment_count']}")
    
    await info.close()
```

## 📺 Channel Info

```python
from irotechlab_yt_search import ChannelInfo

async def get_channel():
    channel_info = ChannelInfo()
    channel = await channel_info.get_channel_info("@channelname")
    
    print(f"Name: {channel['name']}")
    print(f"Subscribers: {channel['subscribers']}")
    print(f"Videos: {channel['video_count']}")
    
    await channel_info.close()
```

## 📋 Playlist Info

```python
from irotechlab_yt_search import PlaylistInfo

async def get_playlist():
    playlist_info = PlaylistInfo()
    playlist = await playlist_info.get_playlist_info("PLAYLIST_ID", max_videos=10)
    
    print(f"Title: {playlist['title']}")
    print(f"Author: {playlist['author']}")
    print(f"Videos: {playlist['video_count']}")
    
    for video in playlist['videos']:
        print(f"  - {video['title']}")
    
    await playlist_info.close()
```

## 🔍 Advanced Search

### Filter by type

```python
# Only videos
videos = await search.search(
    "python tutorial",
    filter_type="video",
    max_results=10
)
```

### Sort results

```python
# Sort by view count
videos = await search.search(
    "python tutorial",
    sort_by="view_count"
)

# Sort by upload date
videos = await search.search(
    "python tutorial",
    sort_by="upload_date"
)
```

### Region and language

```python
videos = await search.search(
    "python tutorial",
    region_code="IN",
    language="hi"
)
```

## 🛠️ API Reference

### YouTubeSearch

**Parameters:**
- `query` (str): Search query
- `max_results` (int): Maximum number of results (default: 10)
- `filter_type` (str): `all`, `video`, `channel`, `playlist`, `movie`, `live`
- `sort_by` (str): `relevance`, `upload_date`, `view_count`, `rating`
- `region_code` (str): Two-letter country code
- `language` (str): Language code

**Returns:** `List[Video]`

### Video Object

```
@dataclass
class Video:
    id: str
    title: str
    channel: str
    channel_id: Optional[str]
    url: str
    thumbnail: str
    duration: str
    duration_seconds: Optional[int]
    views: str
    view_count: Optional[int]
    published: str
    published_date: Optional[datetime]
    is_live: bool
```

## 📂 Examples

Check the `examples/` directory for more usage examples:

- `basic_search.py` - Simple search
- `advanced_search.py` - Advanced filtering and sorting
- `all_in_one.py` - Complete demo of all features

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support & Community

- **Telegram Channel:** [@irotechcoders](https://t.me/irotechcoders)
- **Telegram Contact:** [@ironmanhindigaming](https://t.me/ironmanhindigaming)
- **GitHub Issues:** [Report a bug](https://github.com/irotechlab/irotechlab-yt-search/issues)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## ⚠️ Disclaimer

This package scrapes YouTube's internal API and may break if YouTube changes their structure. Use responsibly and respect YouTube's terms of service.

---

**Made with ❤️ by IrotechLab**