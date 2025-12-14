
import asyncio
import time
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class InMemoryCache:
    def __init__(self):
        self._cache = {}
        self._ttl = {}
        self._max_size = 1000
        self._cleanup_threshold = 0.9
        self._lock = asyncio.Lock()
        self._background_cleanup_task = None

    async def get(self, key: str) -> Optional[Dict]:
        async with self._lock:
            if key in self._cache:
                if self._ttl[key] > time.time():
                    return self._cache[key]
                else:
                    del self._cache[key]
                    del self._ttl[key]
            return None

    async def set(self, key: str, value: Dict, ex: int = None):
        try:
            async with self._lock:
                if len(self._cache) >= self._max_size * self._cleanup_threshold:
                    await self._cleanup_expired()
                
                self._cache[key] = value
                self._ttl[key] = time.time() + (ex if ex else 3600)
        except Exception as e:
            logger.error(f"캐시 설정 실패: {key} - {e}")

    async def delete(self, key: str) -> bool:
        """캐시에서 데이터 삭제"""
        try:
            async with self._lock:
                if key in self._cache:
                    del self._cache[key]
                    del self._ttl[key]
                return True
        except Exception as e:
            logger.error(f"캐시 삭제 실패: {key} - {e}")
            return False

    async def start_background_cleanup(self):
        """주기적으로 만료된 캐시 정리"""
        if self._background_cleanup_task is None:
            self._background_cleanup_task = asyncio.create_task(self._periodic_cleanup())

    async def _periodic_cleanup(self):
        while True:
            await asyncio.sleep(3600)  # 1시간마다 정리
            await self._cleanup_expired()

    async def _cleanup_expired(self):
        current_time = time.time()
        async with self._lock:
            expired_keys = [k for k, v in self._ttl.items() if v <= current_time]
            for k in expired_keys:
                del self._cache[k]
                del self._ttl[k]

cache_manager = InMemoryCache()
