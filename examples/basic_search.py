
"""Basic search example"""

import asyncio
from irotechlab_yt_search import YouTubeSearch

async def main():
    # Initialize search
    search = YouTubeSearch()
    
    try:
        # Search for videos
        print("Searching for 'python tutorials'...")
        videos = await search.search(
            "python tutorials",
            max_results=5
        )
        
        # Display results
        print(f"\nFound {len(videos)} videos:\n")
        for idx, video in enumerate(videos, 1):
            print(f"{idx}. {video.title}")
            print(f"   Channel: {video.channel}")
            print(f"   Views: {video.views}")
            print(f"   Duration: {video.duration}")
            print(f"   URL: {video.url}\n")
            
    finally:
        # Close session
        await search.close()

if __name__ == "__main__":
    asyncio.run(main())