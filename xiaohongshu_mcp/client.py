"""Client for Xiaohongshu API using xiaohongshu-cli library."""

import asyncio
import json
from pathlib import Path
from typing import Any

from xhs_cli.client import XhsClient
from xhs_cli.cookies import cache_note_context, get_cookies


def _first_text(*values: Any) -> str:
    """Return the first non-empty value as text."""
    for value in values:
        if value is None:
            continue
        text = str(value)
        if text:
            return text
    return ""


def _first_value(*values: Any) -> Any:
    """Return the first non-empty value without coercion."""
    for value in values:
        if value not in (None, ""):
            return value
    return ""


def _as_dict(value: Any) -> dict[str, Any]:
    """Return value if it is a dictionary, otherwise an empty dictionary."""
    return value if isinstance(value, dict) else {}


class XiaohongshuClient:
    """Async wrapper for xiaohongshu-cli library."""

    def __init__(self):
        """Initialize client with auto cookie extraction."""
        self._client = None

    def _load_cookies(self) -> dict[str, str]:
        """Load cookies from file or browser."""
        cookie_file = Path(__file__).parent.parent / "cookies.json"

        if cookie_file.exists():
            try:
                with open(cookie_file) as f:
                    return json.load(f)
            except Exception:
                pass

        try:
            _, cookies = get_cookies()
            return cookies
        except Exception:
            return {}

    def _get_client(self) -> XhsClient:
        """Lazy initialize client."""
        if self._client is None:
            cookies = self._load_cookies()
            self._client = XhsClient(cookies=cookies)
        return self._client

    async def set_cookies(self, cookies_input: str) -> dict[str, Any]:
        try:
            try:
                cookies = json.loads(cookies_input)
            except json.JSONDecodeError:
                cookies = {}
                for part in cookies_input.split(";"):
                    part = part.strip()
                    if "=" in part:
                        k, _, v = part.partition("=")
                        cookies[k.strip()] = v.strip()

            if not cookies:
                return {
                    "success": False,
                    "message": "无法解析 cookies，请提供 JSON 对象或 Cookie 请求头字符串",
                }

            cookie_file = Path(__file__).parent.parent / "cookies.json"
            with open(cookie_file, "w") as f:
                json.dump(cookies, f, indent=2)

            self._client = XhsClient(cookies=cookies)

            try:
                await asyncio.to_thread(self._client.get_self_info)
                return {"success": True, "message": "Cookie 有效，登录成功"}
            except Exception:
                return {
                    "success": False,
                    "message": "Cookie 已保存，但验证失败，可能已过期或无效",
                }
        except Exception as e:
            return {"success": False, "message": f"保存失败: {str(e)}"}

    async def search_notes(
        self, keyword: str, page: int = 1, sort: str = "general", note_type: int = 0
    ) -> dict[str, Any]:
        """Search notes by keyword.

        Args:
            keyword: Search keyword
            page: Page number (starts from 1)
            sort: Sort method (general/time_descending/popularity_descending)
            note_type: 0=all, 1=video, 2=image
        """
        client = self._get_client()

        type_map = {0: 0, 1: 1, 2: 2}
        mapped_type = type_map.get(note_type, 0)

        result = await asyncio.to_thread(
            client.search_notes,
            keyword=keyword,
            page=page,
            sort=sort,
            note_type=mapped_type,
        )

        compact_items: list[dict[str, Any]] = []
        for item in result.get("items", []):
            if item.get("model_type") != "note":
                continue

            note_card = item.get("note_card", {})
            interact_info = note_card.get("interact_info", {})
            user = note_card.get("user", {})
            note_id = _first_text(item.get("id"), note_card.get("note_id"), note_card.get("noteId"))
            xsec_token = _first_text(item.get("xsec_token"), note_card.get("xsec_token"), note_card.get("xsecToken"))

            if note_id and xsec_token:
                cache_note_context(note_id, xsec_token, "pc_search", context="search_notes")

            publish_time_text = ""
            corner_tag_info = note_card.get("corner_tag_info", [])
            if corner_tag_info and isinstance(corner_tag_info, list):
                first_tag = corner_tag_info[0]
                if isinstance(first_tag, dict):
                    publish_time_text = first_tag.get("text", "")

            compact_items.append(
                {
                    "id": note_id,
                    "xsec_token": xsec_token,
                    "xsec_source": "pc_search" if xsec_token else "",
                    "title": note_card.get("display_title", ""),
                    "nickname": user.get("nickname", ""),
                    "interact_info": {
                        "liked_count": interact_info.get("liked_count", "0"),
                        "collected_count": interact_info.get("collected_count", "0"),
                        "comment_count": interact_info.get("comment_count", "0"),
                        "shared_count": interact_info.get("shared_count", "0"),
                    },
                    "publish_time_text": publish_time_text,
                }
            )

        return {"success": True, "data": {"items": compact_items}}

    async def search_note_suggestions(
        self,
        keyword: str,
        page: int = 1,
        sort: str = "general",
        note_type: int = 0,
    ) -> dict[str, Any]:
        client = self._get_client()

        type_map = {0: 0, 1: 1, 2: 2}
        mapped_type = type_map.get(note_type, 0)

        result = await asyncio.to_thread(
            client.search_notes,
            keyword=keyword,
            page=page,
            sort=sort,
            note_type=mapped_type,
        )

        suggestions: list[str] = []
        seen: set[str] = set()
        for item in result.get("items", []):
            if item.get("model_type") != "rec_query":
                continue

            rec_query = item.get("rec_query", {})
            for query in rec_query.get("queries", []):
                if not isinstance(query, dict):
                    continue
                search_word = query.get("search_word", "")
                if search_word and search_word not in seen:
                    seen.add(search_word)
                    suggestions.append(search_word)

        return {
            "success": True,
            "data": {
                "keyword": keyword,
                "suggestions": suggestions,
            },
        }

    async def get_note_image(
        self, note_id: str, xsec_token: str = "", xsec_source: str = ""
    ) -> dict[str, Any]:
        """Get image note details."""
        return await self._get_note_detail(note_id, xsec_token, xsec_source)

    async def get_note_video(
        self, note_id: str, xsec_token: str = "", xsec_source: str = ""
    ) -> dict[str, Any]:
        """Get video note details."""
        return await self._get_note_detail(note_id, xsec_token, xsec_source)

    async def _get_note_detail(
        self, note_id: str, xsec_token: str = "", xsec_source: str = ""
    ) -> dict[str, Any]:
        """Get note details via xiaohongshu-cli token resolution."""
        client = self._get_client()

        result = await asyncio.to_thread(
            client.get_note_detail,
            note_id=note_id,
            xsec_token=xsec_token,
            xsec_source=xsec_source,
        )

        note_item: dict[str, Any] = {}
        if isinstance(result, dict):
            items = result.get("items", [])
            if isinstance(items, list) and items:
                first_item = items[0]
                if isinstance(first_item, dict):
                    note_item = first_item
            elif isinstance(result.get("note_card"), dict):
                note_item = result
            else:
                note_item = {"id": note_id, "note_card": result}

        note_card = _as_dict(note_item.get("note_card")) if isinstance(note_item, dict) else {}
        user = _as_dict(
            _first_value(
                note_card.get("user"),
                note_card.get("user_info"),
                note_card.get("userInfo"),
                note_card.get("author"),
            )
        )
        interact_info = _as_dict(
            _first_value(note_card.get("interact_info"), note_card.get("interactInfo"))
        )

        images: list[str] = []
        image_list = _first_value(note_card.get("image_list"), note_card.get("imageList"), [])
        if isinstance(image_list, list):
            for image in image_list:
                if not isinstance(image, dict):
                    continue
                info_list = _first_value(image.get("info_list"), image.get("infoList"), [])
                if not isinstance(info_list, list):
                    continue
                chosen_url = ""
                for info in info_list:
                    if isinstance(info, dict) and info.get("url"):
                        chosen_url = info.get("url", "")
                        if info.get("image_scene") == "WB_DFT":
                            break
                if chosen_url:
                    images.append(chosen_url)

        video_url = ""
        video = _as_dict(note_card.get("video"))
        if isinstance(video, dict):
            media = video.get("media", {})
            if isinstance(media, dict):
                stream = media.get("stream", {})
                if isinstance(stream, dict):
                    h264 = stream.get("h264", [])
                    if isinstance(h264, list) and h264:
                        first_stream = h264[0]
                        if isinstance(first_stream, dict):
                            master_url = first_stream.get("master_url", "")
                            if isinstance(master_url, str):
                                video_url = master_url

        return {
            "success": True,
            "data": {
                "id": _first_text(
                    note_item.get("id"), note_card.get("note_id"), note_card.get("noteId"), note_id
                ),
                "title": _first_text(note_card.get("title"), note_card.get("display_title"), note_card.get("displayTitle")),
                "desc": _first_text(note_card.get("desc"), note_card.get("description")),
                "type": _first_text(note_card.get("type"), note_card.get("note_type"), note_card.get("noteType")),
                "nickname": _first_text(user.get("nickname"), user.get("nick_name"), user.get("nickName")),
                "user_id": _first_text(user.get("user_id"), user.get("userId"), user.get("id")),
                "interact_info": {
                    "liked_count": _first_text(interact_info.get("liked_count"), interact_info.get("likedCount"), "0"),
                    "collected_count": _first_text(interact_info.get("collected_count"), interact_info.get("collectedCount"), "0"),
                    "comment_count": _first_text(interact_info.get("comment_count"), interact_info.get("commentCount"), "0"),
                    "share_count": _first_text(interact_info.get("share_count"), interact_info.get("shareCount"), "0"),
                },
                "time": _first_value(note_item.get("time"), note_card.get("time"), note_card.get("timestamp"), 0),
                "images": images,
                "video_url": video_url,
            },
        }

    async def get_note_comments(
        self, note_id: str, cursor: str = "", xsec_token: str = ""
    ) -> dict[str, Any]:
        """Get note comments with pagination."""
        client = self._get_client()

        result = await asyncio.to_thread(
            client.get_comments, note_id=note_id, cursor=cursor, xsec_token=xsec_token
        )

        compact_comments: list[dict[str, Any]] = []
        for comment in result.get("comments", []):
            if not isinstance(comment, dict):
                continue
            user_info = comment.get("user_info", {})
            compact_comments.append(
                {
                    "id": comment.get("id", ""),
                    "content": comment.get("content", ""),
                    "nickname": user_info.get("nickname", "")
                    if isinstance(user_info, dict)
                    else "",
                    "user_id": user_info.get("user_id", "")
                    if isinstance(user_info, dict)
                    else "",
                    "like_count": comment.get("like_count", "0"),
                    "sub_comment_count": comment.get("sub_comment_count", "0"),
                    "create_time": comment.get("create_time", 0),
                    "ip_location": comment.get("ip_location", ""),
                }
            )

        return {
            "success": True,
            "data": {
                "comments": compact_comments,
                "cursor": result.get("cursor", ""),
                "has_more": result.get("has_more", False),
            },
        }

    async def get_comment_replies(
        self, note_id: str, comment_id: str, cursor: str = ""
    ) -> dict[str, Any]:
        """Get replies to a specific comment."""
        client = self._get_client()

        result = await asyncio.to_thread(
            client.get_sub_comments,
            note_id=note_id,
            root_comment_id=comment_id,
            cursor=cursor,
        )

        compact_replies: list[dict[str, Any]] = []
        for reply in result.get("comments", []):
            if not isinstance(reply, dict):
                continue
            user_info = reply.get("user_info", {})
            compact_replies.append(
                {
                    "id": reply.get("id", ""),
                    "content": reply.get("content", ""),
                    "nickname": user_info.get("nickname", "")
                    if isinstance(user_info, dict)
                    else "",
                    "user_id": user_info.get("user_id", "")
                    if isinstance(user_info, dict)
                    else "",
                    "like_count": reply.get("like_count", "0"),
                    "create_time": reply.get("create_time", 0),
                    "ip_location": reply.get("ip_location", ""),
                }
            )

        return {
            "success": True,
            "data": {
                "comments": compact_replies,
                "cursor": result.get("cursor", ""),
                "has_more": result.get("has_more", False),
            },
        }

    async def get_user_info(self, user_id: str) -> dict[str, Any]:
        """Get user profile information."""
        client = self._get_client()

        result = await asyncio.to_thread(client.get_user_info, user_id=user_id)

        basic_info = result.get("basic_info", {}) if isinstance(result, dict) else {}
        verify_info = result.get("verify_info", {}) if isinstance(result, dict) else {}

        stats: dict[str, str] = {}
        interactions = (
            result.get("interactions", []) if isinstance(result, dict) else []
        )
        if isinstance(interactions, list):
            for item in interactions:
                if not isinstance(item, dict):
                    continue
                stat_type = item.get("type", "")
                count = item.get("count", "")
                if stat_type:
                    stats[stat_type] = count

        tags: list[str] = []
        raw_tags = result.get("tags", []) if isinstance(result, dict) else []
        if isinstance(raw_tags, list):
            for tag in raw_tags:
                if isinstance(tag, dict):
                    name = tag.get("name", "")
                    if name:
                        tags.append(name)

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "nickname": basic_info.get("nickname", ""),
                "desc": basic_info.get("desc", ""),
                "red_id": basic_info.get("red_id", ""),
                "ip_location": basic_info.get("ip_location", ""),
                "gender": basic_info.get("gender", 0),
                "verified_type": verify_info.get("red_official_verify_type", 0),
                "stats": stats,
                "tags": tags,
            },
        }

    async def get_user_notes(self, user_id: str, cursor: str = "") -> dict[str, Any]:
        """Get notes published by user."""
        client = self._get_client()

        result = await asyncio.to_thread(
            client.get_user_notes, user_id=user_id, cursor=cursor
        )

        compact_notes: list[dict[str, Any]] = []
        for note in result.get("notes", []):
            if not isinstance(note, dict):
                continue
            interact_info = note.get("interact_info", {})
            compact_notes.append(
                {
                    "id": note.get("note_id", ""),
                    "xsec_token": note.get("xsec_token", ""),
                    "title": note.get("display_title", ""),
                    "type": note.get("type", ""),
                    "nickname": (note.get("user", {}) or {}).get("nickname", ""),
                    "liked_count": (interact_info or {}).get("liked_count", "0"),
                }
            )

        return {
            "success": True,
            "data": {
                "notes": compact_notes,
                "cursor": result.get("cursor", ""),
                "has_more": result.get("has_more", False),
            },
        }

    async def get_user_collections(
        self, user_id: str, cursor: str = ""
    ) -> dict[str, Any]:
        """Get notes collected/favorited by user."""
        client = self._get_client()

        result = await asyncio.to_thread(
            client.get_user_favorites, user_id=user_id, cursor=cursor
        )

        compact_notes: list[dict[str, Any]] = []
        for note in result.get("notes", []):
            if not isinstance(note, dict):
                continue
            interact_info = note.get("interact_info", {})
            compact_notes.append(
                {
                    "id": note.get("note_id", ""),
                    "xsec_token": note.get("xsec_token", ""),
                    "title": note.get("display_title", ""),
                    "type": note.get("type", ""),
                    "nickname": (note.get("user", {}) or {}).get("nickname", ""),
                    "liked_count": (interact_info or {}).get("liked_count", "0"),
                }
            )

        return {
            "success": True,
            "data": {
                "notes": compact_notes,
                "cursor": result.get("cursor", ""),
                "has_more": result.get("has_more", False),
            },
        }

    async def search_users(self, keyword: str) -> dict[str, Any]:
        """Search users by keyword."""
        client = self._get_client()

        result = await asyncio.to_thread(client.search_users, keyword=keyword)

        users: list[dict[str, Any]] = []
        for item in result.get("user_info_dtos", []):
            if not isinstance(item, dict):
                continue
            user_base = item.get("user_base_dto", {})
            if not isinstance(user_base, dict):
                continue
            users.append(
                {
                    "user_id": user_base.get("user_id", ""),
                    "nickname": user_base.get("user_nickname", ""),
                    "red_id": user_base.get("red_id", ""),
                    "desc": user_base.get("desc", ""),
                    "verified": user_base.get("red_official_verified", False),
                    "verified_type": user_base.get("red_official_verify_type", 0),
                }
            )

        return {"success": True, "data": {"users": users}}

    async def search_topics(self, keyword: str) -> dict[str, Any]:
        """Search topics by keyword."""
        client = self._get_client()

        result = await asyncio.to_thread(client.search_topics, keyword=keyword)

        topics: list[dict[str, Any]] = []
        for topic in result.get("topic_info_dtos", []):
            if not isinstance(topic, dict):
                continue
            topics.append(
                {
                    "id": topic.get("id", ""),
                    "name": topic.get("name", ""),
                    "view_num": topic.get("view_num", 0),
                    "type": topic.get("type", ""),
                    "link": topic.get("link", ""),
                }
            )

        return {"success": True, "data": {"topics": topics}}
