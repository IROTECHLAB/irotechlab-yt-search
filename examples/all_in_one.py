"""All-in-one demo for irotechlab-yt-search module
Demonstrates: Search, Video Info, Channel Info, Playlist Info
"""

import asyncio
import json
import os
from datetime import datetime
from irotechlab_yt_search import (
    YouTubeSearch,
    VideoInfo,
    ChannelInfo,
    PlaylistInfo,
    extract_video_id,
    extract_channel_id,
    extract_playlist_id,
    format_duration,
    format_view_count,
    get_video_id
)


async def demo_search():
    """Demo: Search for videos"""
    print("\n" + "="*70)
    print("🔍 SEARCH DEMO")
    print("="*70)
    
    search = YouTubeSearch()
    
    try:
        print("\n📌 Searching for 'python programming'...")
        videos = await search.search(
            query="python programming",
            max_results=5,
            filter_type="video",
            sort_by="view_count"
        )
        
        if videos:
            print(f"\n✅ Found {len(videos)} videos:\n")
            for idx, video in enumerate(videos, 1):
                print(f"{idx}. 📹 {video.title}")
                print(f"   👤 Channel: {video.channel}")
                print(f"   👀 Views: {video.views}")
                print(f"   ⏱️ Duration: {video.duration}")
                print(f"   🔗 URL: {video.url}")
                print()
        else:
            print("\n❌ No videos found.")
            
    except Exception as e:
        print(f"❌ Search error: {e}")
    
    finally:
        await search.close()


async def demo_video_info():
    """Demo: Get detailed video information"""
    print("\n" + "="*70)
    print("📹 VIDEO INFO DEMO")
    print("="*70)
    
    video_info = VideoInfo()
    
    try:
        video_ids = [
            "_uQrJ0TkZlc",
            "dQw4w9WgXcQ",
        ]
        
        for video_id in video_ids:
            print(f"\n📌 Getting info for: {video_id}")
            print("-" * 50)
            
            try:
                info = await video_info.get_video_info(video_id)
                
                print(f"📹 Title: {info['title']}")
                print(f"👤 Channel: {info['channel']}")
                if info.get('channel_url'):
                    print(f"🔗 Channel URL: {info['channel_url']}")
                print(f"👀 Views: {format_view_count(info['views'])}")
                if info.get('duration_seconds'):
                    print(f"⏱️ Duration: {format_duration(info['duration_seconds'])}")
                print(f"📅 Published: {info.get('published', 'N/A')}")
                if info.get('category'):
                    print(f"📂 Category: {info['category']}")
                if info.get('tags'):
                    print(f"🏷️ Tags: {len(info['tags'])} tags")
                    print(f"   First 3 tags: {', '.join(info['tags'][:3])}")
                
                if info.get('description'):
                    desc = info['description'][:150]
                    if len(info['description']) > 150:
                        desc += "..."
                    print(f"📝 Description: {desc}")
                
                if info.get('formats'):
                    print(f"📊 Available formats: {len(info['formats'])}")
                
                print("✅ Success!")
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"❌ Video info error: {e}")
    
    finally:
        await video_info.close()


async def demo_channel_info():
    """Demo: Get channel information"""
    print("\n" + "="*70)
    print("📺 CHANNEL INFO DEMO")
    print("="*70)
    
    channel_info = ChannelInfo()
    
    try:
        channels = [
            "@ProgrammingwithMosh",
            "@freecodecamp",
        ]
        
        for channel_id in channels:
            print(f"\n📌 Getting info for channel: {channel_id}")
            print("-" * 50)
            
            try:
                channel = await channel_info.get_channel_info(channel_id)
                
                if channel:
                    print(f"📺 Name: {channel.get('name', 'Unknown')}")
                    print(f"🆔 ID: {channel.get('id', 'Unknown')}")
                    print(f"🔗 URL: {channel.get('url', '')}")
                    if channel.get('subscribers'):
                        print(f"👥 Subscribers: {channel['subscribers']}")
                    if channel.get('video_count'):
                        print(f"📹 Videos: {channel['video_count']}")
                    if channel.get('view_count'):
                        print(f"👀 Views: {channel['view_count']}")
                    if channel.get('joined_date'):
                        print(f"📅 Joined: {channel['joined_date']}")
                    if channel.get('country'):
                        print(f"🌍 Country: {channel['country']}")
                    
                    if channel.get('description'):
                        desc = channel['description'][:150]
                        if len(channel['description']) > 150:
                            desc += "..."
                        print(f"📝 Description: {desc}")
                    
                    print("✅ Success!")
                else:
                    print("❌ Channel not found")
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"❌ Channel info error: {e}")
    
    finally:
        await channel_info.close()


async def demo_playlist_info():
    """Demo: Get playlist information"""
    print("\n" + "="*70)
    print("📋 PLAYLIST INFO DEMO")
    print("="*70)
    
    playlist_info = PlaylistInfo()
    
    try:
        playlists = [
            {
                "id": "PLBhyt-fTQqzQ3AieF-XlYMSAC1Wvpv5Qd",
                "name": "Goosbumps Season 1"
            },
            {
                "id": "PLWKjhJtqVAbnqBxcdjVGgT3uVR10bzTEB",
                "name": "Python for Beginners"
            }
        ]
        
        for playlist_data in playlists:
            playlist_id = playlist_data["id"]
            playlist_name = playlist_data["name"]
            
            print(f"\n📌 Getting info for playlist: {playlist_name}")
            print("-" * 50)
            
            try:
                playlist = await playlist_info.get_playlist_info(playlist_id, max_videos=10)
                
                if playlist:
                    print(f"📋 Title: {playlist.get('title', 'Unknown')}")
                    print(f"👤 Author: {playlist.get('author', 'Unknown')}")
                    print(f"📹 Video Count: {playlist.get('video_count', '0')}")
                    if playlist.get('view_count'):
                        print(f"👀 Views: {playlist.get('view_count')}")
                    
                    videos = playlist.get('videos', [])
                    if videos:
                        print(f"\n📹 Videos in playlist ({len(videos)}):")
                        for idx, video in enumerate(videos, 1):
                            title = video.get('title', 'Unknown')[:50]
                            print(f"   {idx}. {title}...")
                            if video.get('duration'):
                                print(f"      ⏱️ Duration: {video.get('duration')}")
                            if video.get('url'):
                                print(f"      🔗 {video.get('url')}")
                    else:
                        print("\n⚠️ No videos found in this playlist")
                else:
                    print("❌ Playlist not found")
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"❌ Playlist error: {e}")
    
    finally:
        await playlist_info.close()


async def demo_search_filters():
    """Demo: Search with filters"""
    print("\n" + "="*70)
    print("🎯 SEARCH FILTERS DEMO")
    print("="*70)
    
    search = YouTubeSearch()
    
    try:
        filters = [
            ("all", "All Results"),
            ("video", "Videos Only"),
        ]
        
        query = "coding tutorials"
        
        for filter_type, filter_name in filters:
            print(f"\n📌 Filter: {filter_name}")
            print("-" * 40)
            
            try:
                results = await search.search(
                    query=query,
                    max_results=3,
                    filter_type=filter_type
                )
                
                if results:
                    print(f"✅ Found {len(results)} results:")
                    for idx, result in enumerate(results, 1):
                        print(f"   {idx}. 📹 {result.title[:50]}...")
                        print(f"      Channel: {result.channel}")
                else:
                    print("   No results found")
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            await asyncio.sleep(0.5)
            
    finally:
        await search.close()


async def demo_sorting():
    """Demo: Search with sorting"""
    print("\n" + "="*70)
    print("📊 SORTING DEMO")
    print("="*70)
    
    search = YouTubeSearch()
    
    try:
        sort_options = [
            ("relevance", "Relevance"),
            ("view_count", "Most Views"),
        ]
        
        query = "python tutorial"
        
        for sort_by, sort_name in sort_options:
            print(f"\n📌 Sort: {sort_name}")
            print("-" * 40)
            
            try:
                results = await search.search(
                    query=query,
                    max_results=3,
                    sort_by=sort_by
                )
                
                if results:
                    print(f"✅ Found {len(results)} results:")
                    for idx, result in enumerate(results, 1):
                        print(f"   {idx}. 📹 {result.title[:50]}...")
                        print(f"      👀 {result.views}")
                        print(f"      📅 {result.published}")
                else:
                    print("   No results found")
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            await asyncio.sleep(0.5)
            
    finally:
        await search.close()


async def demo_extract_video_id():
    """Demo: Video ID extraction"""
    print("\n" + "="*70)
    print("🔗 VIDEO ID EXTRACTION DEMO")
    print("="*70)
    
    urls = [
        "https://www.youtube.com/watch?v=_uQrJ0TkZlc",
        "https://youtu.be/dQw4w9WgXcQ",
        "_uQrJ0TkZlc",
    ]
    
    for url in urls:
        video_id = get_video_id(url)
        print(f"📌 URL: {url[:50]}...")
        print(f"   🆔 Video ID: {video_id}")
        print()


async def demo_export_to_json():
    """Demo: Export video info to JSON"""
    print("\n" + "="*70)
    print("💾 EXPORT TO JSON DEMO")
    print("="*70)
    
    video_info = VideoInfo()
    
    try:
        video_id = "_uQrJ0TkZlc"
        print(f"\n📌 Getting info for: {video_id}")
        
        info = await video_info.get_video_info(video_id)
        
        info["scraped_at"] = datetime.now().isoformat()
        
        def json_serializable(data):
            if isinstance(data, dict):
                return {k: json_serializable(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [json_serializable(item) for item in data]
            elif isinstance(data, datetime):
                return data.isoformat()
            else:
                return data
        
        info_serializable = json_serializable(info)
        
        # Try multiple writable paths
        writable_paths = [
            "/data/data/ru.iiec.pydroid3/files/video_info_export.json",
            os.path.join(os.getcwd(), "video_info_export.json"),
            "/sdcard/video_info_export.json",
            "/storage/emulated/0/video_info_export.json"
        ]
        
        saved = False
        for path in writable_paths:
            try:
                dirname = os.path.dirname(path)
                if dirname and not os.path.exists(dirname):
                    try:
                        os.makedirs(dirname, exist_ok=True)
                    except:
                        pass
                
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(info_serializable, f, indent=2, ensure_ascii=False)
                print(f"✅ Exported to: {path}")
                
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"📊 File size: {len(content)} characters")
                saved = True
                break
            except:
                continue
        
        if not saved:
            print("⚠️ Could not save file. Data printed below:")
            print(f"   Title: {info['title']}")
            print(f"   Channel: {info['channel']}")
            print(f"   Views: {info['views']}")
            print(f"   Tags: {len(info.get('tags', []))} tags")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'info' in locals():
            print(f"   Title: {info.get('title', 'N/A')}")
            print(f"   Channel: {info.get('channel', 'N/A')}")
            print(f"   Views: {info.get('views', 'N/A')}")
    
    finally:
        await video_info.close()


async def demo_enhanced_search():
    """Enhanced search with yt-dlp style"""
    print("\n" + "="*70)
    print("🔍 ENHANCED SEARCH DEMO")
    print("="*70)
    
    search = YouTubeSearch()
    
    try:
        searches = [
            ("python programming", "video", "view_count"),
            ("machine learning", "video", "upload_date"),
        ]
        
        for query, filter_type, sort_by in searches:
            print(f"\n📌 Searching: '{query}'")
            print("-" * 50)
            
            videos = await search.search(
                query=query,
                max_results=3,
                filter_type=filter_type,
                sort_by=sort_by
            )
            
            if videos:
                print(f"✅ Found {len(videos)} videos:")
                for idx, video in enumerate(videos, 1):
                    print(f"   {idx}. 📹 {video.title[:50]}...")
                    print(f"      👤 Channel: {video.channel}")
                    print(f"      👀 Views: {video.views}")
                    print(f"      ⏱️ Duration: {video.duration}")
            else:
                print("   No results found")
                
    except Exception as e:
        print(f"❌ Search error: {e}")
    
    finally:
        await search.close()


async def main():
    """Run all demos"""
    print("\n" + "🚀"*35)
    print("   IROTECHLAB YOUTUBE SEARCH - COMPLETE DEMO")
    print("🚀"*35)
    
    await demo_extract_video_id()
    await demo_search()
    await demo_enhanced_search()
    await demo_video_info()
    await demo_channel_info()
    await demo_playlist_info()
    await demo_search_filters()
    await demo_sorting()
    await demo_export_to_json()
    
    print("\n" + "="*70)
    print("✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())