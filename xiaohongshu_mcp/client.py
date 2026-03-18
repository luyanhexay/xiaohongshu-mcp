"""Client for Xiaohongshu API using xiaohongshu-cli library."""

import asyncio
import json
from pathlib import Path
from typing import Any
from xhs_cli.client import XhsClient
from xhs_cli.cookies import get_cookies

_qr_session: dict[str, Any] = {}


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
    
    # async def login_qr_start(self) -> dict[str, Any]:
    #     global _qr_session
    #     try:
    #         a1 = "".join(random.choices("0123456789abcdef", k=24)) + str(int(time.time() * 1000)) + "".join(random.choices("0123456789abcdef", k=15))
    #         webid = "".join(random.choices("0123456789abcdef", k=32))
    #         tmp_cookies = {"a1": a1, "webId": webid}
    #         client = XhsClient(tmp_cookies, request_delay=0)
    #
    #         qr_data = await asyncio.to_thread(client.create_qr_login)
    #         qr_id = qr_data["qr_id"]
    #         code = qr_data["code"]
    #         qr_url = qr_data["url"]
    #
    #         qr = qrcode.QRCode(error_correction=ERROR_CORRECT_L, border=1)
    #         qr.add_data(qr_url)
    #         qr.make(fit=True)
    #         matrix = qr.get_matrix()
    #         lines = []
    #         for i in range(0, len(matrix) - 1, 2):
    #             row = ""
    #             for j in range(len(matrix[i])):
    #                 top = matrix[i][j]
    #                 bot = matrix[i + 1][j] if i + 1 < len(matrix) else False
    #                 if top and bot:
    #                     row += "█"
    #                 elif top:
    #                     row += "▀"
    #                 elif bot:
    #                     row += "▄"
    #                 else:
    #                     row += " "
    #             lines.append(row)
    #         qr_text = "\n".join(lines)
    #
    #         _qr_session = {"client": client, "qr_id": qr_id, "code": code, "a1": a1, "webid": webid}
    #         return {"success": True, "qr_text": qr_text, "qr_url": qr_url}
    #     except Exception as e:
    #         return {"success": False, "message": f"创建二维码失败: {str(e)}"}

    # async def login_qr_poll(self) -> dict[str, Any]:
    #     global _qr_session
    #     if not _qr_session:
    #         return {"success": False, "message": "未找到登录会话，请先调用 xiaohongshu_login_start"}
    #
    #     client: XhsClient = _qr_session["client"]
    #     qr_id = _qr_session["qr_id"]
    #     code = _qr_session["code"]
    #     a1 = _qr_session["a1"]
    #     webid = _qr_session["webid"]
    #
    #     try:
    #         deadline = time.time() + 120
    #         while time.time() < deadline:
    #             status = await asyncio.to_thread(client.check_qr_status, qr_id, code)
    #             code_status = status.get("codeStatus", -1)
    #
    #             if code_status == 2:
    #                 await asyncio.to_thread(client.complete_qr_login, qr_id, code)
    #                 cookies = {
    #                     "a1": a1,
    #                     "webId": webid,
    #                     "web_session": client.cookies.get("web_session", ""),
    #                     "web_session_sec": client.cookies.get("web_session_sec", ""),
    #                 }
    #                 cookie_file = Path(__file__).parent.parent / "cookies.json"
    #                 with open(cookie_file, "w") as f:
    #                     json.dump(cookies, f, indent=2)
    #                 self._client = XhsClient(cookies=cookies)
    #                 _qr_session = {}
    #                 return {"success": True, "message": "登录成功"}
    #
    #             await asyncio.sleep(2)
    #
    #         _qr_session = {}
    #         return {"success": False, "message": "登录超时（2分钟），请重新调用 xiaohongshu_login_start 获取新二维码"}
    #     except Exception as e:
    #         _qr_session = {}
    #         return {"success": False, "message": f"登录出错: {str(e)}"}

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
                return {"success": False, "message": "无法解析 cookies，请提供 JSON 对象或 Cookie 请求头字符串"}

            cookie_file = Path(__file__).parent.parent / "cookies.json"
            with open(cookie_file, "w") as f:
                json.dump(cookies, f, indent=2)

            self._client = XhsClient(cookies=cookies)

            try:
                await asyncio.to_thread(self._client.get_self_info)
                return {"success": True, "message": "Cookie 有效，登录成功"}
            except Exception:
                return {"success": False, "message": "Cookie 已保存，但验证失败，可能已过期或无效"}
        except Exception as e:
            return {"success": False, "message": f"保存失败: {str(e)}"}

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
        
        type_map = {0: 0, 1: 1, 2: 2}
        mapped_type = type_map.get(note_type, 0)
        
        result = await asyncio.to_thread(
            client.search_notes,
            keyword=keyword,
            page=page,
            sort=sort,
            note_type=mapped_type
        )

        compact_items: list[dict[str, Any]] = []
        for item in result.get("items", []):
            if item.get("model_type") != "note":
                continue

            note_card = item.get("note_card", {})
            interact_info = note_card.get("interact_info", {})
            user = note_card.get("user", {})

            publish_time_text = ""
            corner_tag_info = note_card.get("corner_tag_info", [])
            if corner_tag_info and isinstance(corner_tag_info, list):
                first_tag = corner_tag_info[0]
                if isinstance(first_tag, dict):
                    publish_time_text = first_tag.get("text", "")

            compact_items.append(
                {
                    "id": item.get("id", ""),
                    "xsec_token": item.get("xsec_token", ""),
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
    
    async def get_note_image(self, note_id: str) -> dict[str, Any]:
        """Get image note details."""
        return await self._get_note_detail(note_id)
    
    async def get_note_video(self, note_id: str) -> dict[str, Any]:
        """Get video note details."""
        return await self._get_note_detail(note_id)
    
    async def _get_note_detail(self, note_id: str) -> dict[str, Any]:
        """Get note details (works for both image and video)."""
        client = self._get_client()
        
        result = await asyncio.to_thread(
            client.get_note_by_id,
            note_id=note_id
        )

        note_item: dict[str, Any] = {}
        if isinstance(result, dict):
            items = result.get("items", [])
            if isinstance(items, list) and items:
                first_item = items[0]
                if isinstance(first_item, dict):
                    note_item = first_item

        note_card = note_item.get("note_card", {}) if isinstance(note_item, dict) else {}
        user = note_card.get("user", {}) if isinstance(note_card, dict) else {}
        interact_info = note_card.get("interact_info", {}) if isinstance(note_card, dict) else {}

        images: list[str] = []
        image_list = note_card.get("image_list", []) if isinstance(note_card, dict) else []
        if isinstance(image_list, list):
            for image in image_list:
                if not isinstance(image, dict):
                    continue
                info_list = image.get("info_list", [])
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
        video = note_card.get("video", {}) if isinstance(note_card, dict) else {}
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
                "id": note_item.get("id", note_id),
                "title": note_card.get("title") or note_card.get("display_title", ""),
                "desc": note_card.get("desc", ""),
                "type": note_card.get("type", ""),
                "nickname": user.get("nickname", ""),
                "user_id": user.get("user_id", ""),
                "interact_info": {
                    "liked_count": interact_info.get("liked_count", "0"),
                    "collected_count": interact_info.get("collected_count", "0"),
                    "comment_count": interact_info.get("comment_count", "0"),
                    "share_count": interact_info.get("share_count", "0"),
                },
                "time": note_item.get("time", note_card.get("time", 0)),
                "images": images,
                "video_url": video_url,
            },
        }
    
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

        compact_comments: list[dict[str, Any]] = []
        for comment in result.get("comments", []):
            if not isinstance(comment, dict):
                continue
            user_info = comment.get("user_info", {})
            compact_comments.append(
                {
                    "id": comment.get("id", ""),
                    "content": comment.get("content", ""),
                    "nickname": user_info.get("nickname", "") if isinstance(user_info, dict) else "",
                    "user_id": user_info.get("user_id", "") if isinstance(user_info, dict) else "",
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

        compact_replies: list[dict[str, Any]] = []
        for reply in result.get("comments", []):
            if not isinstance(reply, dict):
                continue
            user_info = reply.get("user_info", {})
            compact_replies.append(
                {
                    "id": reply.get("id", ""),
                    "content": reply.get("content", ""),
                    "nickname": user_info.get("nickname", "") if isinstance(user_info, dict) else "",
                    "user_id": user_info.get("user_id", "") if isinstance(user_info, dict) else "",
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
