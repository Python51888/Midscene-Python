"""
Task caching system for performance optimization
"""

import json
import hashlib
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from loguru import logger
from pydantic import BaseModel


class CacheEntry(BaseModel):
    """Cache entry model"""
    key: str
    data: Any
    timestamp: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}


class TaskCache:
    """Task caching system for storing and retrieving execution results"""
    
    def __init__(
        self, 
        cache_id: str,
        enabled: bool = True,
        cache_dir: Optional[str] = None,
        max_age_hours: int = 24
    ):
        """Initialize task cache
        
        Args:
            cache_id: Unique cache identifier
            enabled: Whether caching is enabled
            cache_dir: Cache directory path
            max_age_hours: Maximum cache age in hours
        """
        self.cache_id = cache_id
        self.enabled = enabled
        self.max_age_hours = max_age_hours
        
        # Setup cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".midscene" / "cache"
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / f"{cache_id}.json"
        
        # Load existing cache
        self._cache: Dict[str, CacheEntry] = {}
        self._load_cache()
    
    def _generate_key(self, data: Union[str, Dict, List]) -> str:
        """Generate cache key from data
        
        Args:
            data: Data to generate key from
            
        Returns:
            Cache key string
        """
        if isinstance(data, str):
            content = data
        else:
            content = json.dumps(data, sort_keys=True, ensure_ascii=False)
        
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _load_cache(self) -> None:
        """Load cache from file"""
        if not self.enabled or not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            for key, entry_data in cache_data.items():
                # Convert datetime strings back to datetime objects
                entry_data['timestamp'] = datetime.fromisoformat(entry_data['timestamp'])
                if entry_data.get('expires_at'):
                    entry_data['expires_at'] = datetime.fromisoformat(entry_data['expires_at'])
                
                self._cache[key] = CacheEntry(**entry_data)
            
            # Clean expired entries
            self._clean_expired()
            
            logger.debug(f"Loaded {len(self._cache)} cache entries")
            
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            self._cache = {}
    
    def _save_cache(self) -> None:
        """Save cache to file"""
        if not self.enabled:
            return
        
        try:
            cache_data = {}
            for key, entry in self._cache.items():
                entry_dict = entry.model_dump()
                # Convert datetime objects to strings
                entry_dict['timestamp'] = entry.timestamp.isoformat()
                if entry.expires_at:
                    entry_dict['expires_at'] = entry.expires_at.isoformat()
                
                cache_data[key] = entry_dict
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def _clean_expired(self) -> None:
        """Clean expired cache entries"""
        now = datetime.now()
        expired_keys = []
        
        for key, entry in self._cache.items():
            # Check explicit expiration
            if entry.expires_at and entry.expires_at <= now:
                expired_keys.append(key)
                continue
            
            # Check age-based expiration
            age = now - entry.timestamp
            if age > timedelta(hours=self.max_age_hours):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached data by key
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found
        """
        if not self.enabled:
            return None
        
        entry = self._cache.get(key)
        if not entry:
            return None
        
        # Check if expired
        now = datetime.now()
        if entry.expires_at and entry.expires_at <= now:
            del self._cache[key]
            return None
        
        # Check age
        age = now - entry.timestamp
        if age > timedelta(hours=self.max_age_hours):
            del self._cache[key]
            return None
        
        logger.debug(f"Cache hit for key: {key}")
        return entry.data
    
    def put(
        self, 
        key: str, 
        data: Any, 
        expires_in_hours: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store data in cache
        
        Args:
            key: Cache key
            data: Data to cache
            expires_in_hours: Custom expiration time in hours
            metadata: Additional metadata
        """
        if not self.enabled:
            return
        
        now = datetime.now()
        expires_at = None
        
        if expires_in_hours:
            expires_at = now + timedelta(hours=expires_in_hours)
        
        entry = CacheEntry(
            key=key,
            data=data,
            timestamp=now,
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        self._cache[key] = entry
        self._save_cache()
        
        logger.debug(f"Cached data with key: {key}")
    
    def get_by_data(self, data: Union[str, Dict, List]) -> Optional[Any]:
        """Get cached data by input data
        
        Args:
            data: Input data to generate key from
            
        Returns:
            Cached result or None
        """
        key = self._generate_key(data)
        return self.get(key)
    
    def put_by_data(
        self, 
        input_data: Union[str, Dict, List], 
        result_data: Any,
        expires_in_hours: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store data in cache by input data
        
        Args:
            input_data: Input data to generate key from
            result_data: Result data to cache
            expires_in_hours: Custom expiration time in hours
            metadata: Additional metadata
        """
        key = self._generate_key(input_data)
        self.put(key, result_data, expires_in_hours, metadata)
    
    def match_locate_cache(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Match locate operation from cache
        
        Args:
            prompt: Locate prompt
            
        Returns:
            Cached locate result or None
        """
        cache_key = f"locate:{self._generate_key(prompt)}"
        return self.get(cache_key)
    
    def store_locate_result(
        self, 
        prompt: str, 
        result: Dict[str, Any],
        expires_in_hours: int = 24
    ) -> None:
        """Store locate result in cache
        
        Args:
            prompt: Locate prompt
            result: Locate result
            expires_in_hours: Expiration time in hours
        """
        cache_key = f"locate:{self._generate_key(prompt)}"
        self.put(cache_key, result, expires_in_hours, {"type": "locate"})
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._cache.clear()
        if self.cache_file.exists():
            self.cache_file.unlink()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics
        
        Returns:
            Cache statistics
        """
        now = datetime.now()
        total_entries = len(self._cache)
        
        expired_count = 0
        for entry in self._cache.values():
            if entry.expires_at and entry.expires_at <= now:
                expired_count += 1
            elif (now - entry.timestamp) > timedelta(hours=self.max_age_hours):
                expired_count += 1
        
        return {
            "total_entries": total_entries,
            "expired_entries": expired_count,
            "cache_file": str(self.cache_file),
            "cache_size_mb": self.cache_file.stat().st_size / 1024 / 1024 if self.cache_file.exists() else 0,
            "enabled": self.enabled
        }