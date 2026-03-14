"""Client for Xiaohongshu API using xiaohongshu-cli library."""

import asyncio
import json
import os
from pathlib import Path
from typing import Any
from xhs_cli.client import XhsClient
from xhs_cli.cookies import get_cookies


class XiaohongshuClient:
    """Async wrapper for xiaohongshu-cli library."""
    
    def __init__(self):
        """Initialize client with auto cookie extraction."""
        self._client = None
    
    def _load_cookies(self) -> dict[str, str]:
        """Load cookies from file or browser."""
        cookie_file = Path(__file__).parent.parent / "cookies.json"
        
        if cookie_file.exists():
            with open(cookie_file) as f:
                return json.load(f)
        
        _, cookies = get_cookies()
        return cookies
    
    def _get_client(self) -> XhsClient:
        """Lazy initialize client."""
        if self._client is None:
            cookies = self._load_cookies()
            self._client = XhsClient(cookies=cookies)
        return self._client
    
    async def search_notes(
        self,
        keyword: str,
        page: int = 1,
        sort: str = "general",
        note_type: int = 0
    ) -> dict[str, Any]:
        """Search notes by keyword.
        
        Args:
            keyword: Search keyword
            page: Page number (starts from 1)
            sort: Sort method (general/time_descending/popularity_descending)
            note_type: 0=all, 1=video, 2=image
        """
        client = self._get_client()
        
        # Map note_type to xiaohongshu-cli format
        type_map = {0: 0, 1: 1, 2: 2}
        mapped_type = type_map.get(note_type, 0)
        
        # Run sync method in thread pool
        result = await asyncio.to_thread(
            client.search_notes,
            keyword=keyword,
            page=page,
            sort=sort,
            note_type=mapped_type
        )
        
        return {"success": True, "data": result}
    
    async def get_note_image(self, note_id: str) -> dict[str, Any]:
        """Get image note details."""
        return await self._get_note_detail(note_id)
    
    async def get_note_video(self, note_id: str) -> dict[str, Any]:
        """Get video note details."""
        return await self._get_note_detail(note_id)
    
    async def _get_note_detail(self, note_id: str) -> dict[str, Any]:
        """Get note details (works for both image and video)."""
        client = self._get_client()
        
        # Run sync method in thread pool
        result = await asyncio.to_thread(
            client.get_note_by_id,
            note_id=note_id
        )
        
        return {"success": True, "data": result}
    
    async def get_note_comments(
        self,
        note_id: str,
        cursor: str = "",
        xsec_token: str = ""
    ) -> dict[str, Any]:
        """Get note comments with pagination."""
        client = self._get_client()
        
        result = await asyncio.to_thread(
            client.get_comments,
            note_id=note_id,
            cursor=cursor,
            xsec_token=xsec_token
        )
        
        return {"success": True, "data": result}
    
    async def get_comment_replies(
        self,
        note_id: str,
        comment_id: str,
        cursor: str = ""
    ) -> dict[str, Any]:
        """Get replies to a specific comment."""
        client = self._get_client()
        
        result = await asyncio.to_thread(
            client.get_sub_comments,
            note_id=note_id,
            root_comment_id=comment_id,
            cursor=cursor
        )
        
        return {"success": True, "data": result}
    
    async def get_user_info(self, user_id: str) -> dict[str, Any]:
        """Get user profile information."""
        client = self._get_client()
        
        result = await asyncio.to_thread(
            client.get_user_info,
            user_id=user_id
        )
        
        return {"success": True, "data": result}
    
    async def get_user_notes(
        self,
        user_id: str,
        cursor: str = ""
    ) -> dict[str, Any]:
        """Get notes published by user."""
        client = self._get_client()
        
        result = await asyncio.to_thread(
            client.get_user_notes,
            user_id=user_id,
            cursor=cursor
        )
        
        return {"success": True, "data": result}
    
    async def get_user_collections(
        self,
        user_id: str,
        cursor: str = ""
    ) -> dict[str, Any]:
        """Get notes collected/favorited by user."""
        client = self._get_client()
        
        result = await asyncio.to_thread(
            client.get_user_favorites,
            user_id=user_id,
            cursor=cursor
        )
        
        return {"success": True, "data": result}
    
    async def search_users(self, keyword: str) -> dict[str, Any]:
        """Search users by keyword."""
        client = self._get_client()
        
        result = await asyncio.to_thread(
            client.search_users,
            keyword=keyword
        )
        
        return {"success": True, "data": result}
    
    async def search_topics(self, keyword: str) -> dict[str, Any]:
        """Search topics by keyword."""
        client = self._get_client()
        
        result = await asyncio.to_thread(
            client.search_topics,
            keyword=keyword
        )
        
        return {"success": True, "data": result}
