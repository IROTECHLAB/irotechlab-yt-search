"""HTTP client for InnerTube API"""

import aiohttp
import asyncio
import time
import logging
import json
import random
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode
from .exceptions import RequestError, RateLimitError
from .utils import generate_user_agent

logger = logging.getLogger(__name__)

class InnerTubeClient:
    """HTTP client for YouTube's internal API"""
    
    BASE_URL = "https://www.youtube.com/youtubei/v1"
    
    # API Keys for different clients
    API_KEYS = {
        "WEB": "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8",
        "ANDROID": "AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w",
        "IOS": "AIzaSyB-63vPrdThhKuerbB2N_l7Kwwcxj6yUAc",
        "TV": "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
    }
    
    # Client configurations
    CLIENTS = {
        "WEB": {
            "clientName": "WEB",
            "clientVersion": "2.20260404.01.00"
        },
        "ANDROID": {
            "clientName": "ANDROID",
            "clientVersion": "19.09.37"
        },
        "IOS": {
            "clientName": "IOS", 
            "clientVersion": "19.09.37"
        },
        "TV": {
            "clientName": "TVHTML5",
            "clientVersion": "7.0.12"
        }
    }
    
    def __init__(
        self,
        client_type: str = "WEB",
        proxy: Optional[str] = None,
        timeout: int = 15,
        max_retries: int = 3,
        rate_limit: float = 0.5
    ):
        """
        Initialize InnerTube client
        
        Args:
            client_type: WEB, ANDROID, IOS, or TV
            proxy: Proxy URL (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            rate_limit: Minimum delay between requests
        """
        self.client_type = client_type
        self.proxy = proxy
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit = rate_limit
        self.session: Optional[aiohttp.ClientSession] = None
        self._last_request_time = 0
        
        # Set client config
        self.client_config = self.CLIENTS.get(client_type, self.CLIENTS["WEB"])
        self.api_key = self.API_KEYS.get(client_type, self.API_KEYS["WEB"])
        
    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _rate_limit_wait(self):
        """Wait to respect rate limit"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            await asyncio.sleep(self.rate_limit - elapsed)
        self._last_request_time = time.time()
    
    async def request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make request to InnerTube API
        
        Args:
            endpoint: API endpoint (e.g., "search", "player")
            payload: Request payload
            retry_count: Current retry attempt
            
        Returns:
            Response JSON
            
        Raises:
            RequestError: If request fails
            RateLimitError: If rate limited
        """
        await self._rate_limit_wait()
        
        session = await self._ensure_session()
        url = f"{self.BASE_URL}/{endpoint}?key={self.api_key}"
        
        headers = {
            "User-Agent": generate_user_agent(),
            "Content-Type": "application/json",
            "Origin": "https://www.youtube.com",
            "Referer": "https://www.youtube.com",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        
        try:
            async with session.post(
                url,
                json=payload,
                headers=headers,
                proxy=self.proxy,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    raise RateLimitError(f"Rate limit exceeded (429)")
                else:
                    text = await response.text()
                    # Try to parse error
                    try:
                        error_data = json.loads(text)
                        if "error" in error_data:
                            error_msg = error_data["error"].get("message", text[:200])
                            raise RequestError(f"HTTP {response.status}: {error_msg}")
                    except:
                        pass
                    raise RequestError(f"HTTP {response.status}: {text[:200]}")
                    
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if retry_count < self.max_retries:
                wait_time = (2 ** retry_count) + random.uniform(0, 1)
                logger.warning(f"Request failed, retrying in {wait_time:.2f}s: {e}")
                await asyncio.sleep(wait_time)
                return await self.request(endpoint, payload, retry_count + 1)
            raise RequestError(f"Request failed after {self.max_retries} retries: {e}")
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None