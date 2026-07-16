"""Advanced search with filters"""

import asyncio
from irotechlab_yt_search import YouTubeSearch

async def main():
    search = YouTubeSearch()
    
    try:
        # Search with filters
        print("Searching for popular Python videos...")
        videos = await search.search(
            query="python programming",
            max_results=10,
            filter_type="video",
            sort_by="view_count",
            region_code="US"
        )
        
        # Display detailed info
        print(f"\nTop 10 Most Viewed Python Videos:\n")
        for idx, video in enumerate(videos, 1):
            print(f"{idx}. {video.title[:60]}...")
            print(f"   Channel: {video.channel}")
            print(f"   Views: {video.views}")
            print(f"   Uploaded: {video.published}")
            print(f"   Duration: {video.duration}")
            print(f"   Live: {'Yes' if video.is_live else 'No'}")
            print()
            
        # Search for channels using different approach
        print("\nSearching for programming channels...")
        # Use search with channel filter and get channel IDs
        channel_results = await search.search(
            "programming",
            max_results=5,
            filter_type="channel"
        )
        
        # Since channel search returns Video objects with channel info
        channels_found = []
        for video in channel_results:
            channels_found.append({
                "name": video.channel,
                "channel_id": video.channel_id,
                "url": f"https://www.youtube.com/channel/{video.channel_id}" if video.channel_id else None
            })
        
        print(f"Found {len(channels_found)} channels:")
        for channel in channels_found:
            print(f"  - {channel['name']}")
            if channel['url']:
                print(f"    {channel['url']}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        await search.close()

if __name__ == "__main__":
    asyncio.run(main())