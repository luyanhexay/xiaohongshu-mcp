"""MCP Server for Xiaohongshu API integration."""

import json
import os
import sys
from typing import Any, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ErrorData, INVALID_PARAMS, INTERNAL_ERROR
from mcp.shared.exceptions import McpError

from .client import XiaohongshuClient


# Initialize server
server = Server("xiaohongshu-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Xiaohongshu API tools."""
    return [
        Tool(
            name="search_notes",
            description="搜索小红书笔记内容。支持关键词搜索、排序和类型筛选。返回精简笔记列表（id、xsec_token、标题、作者昵称、互动数据、发布时间）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词（必填）。例如：旅游攻略、美食推荐、穿搭分享",
                    },
                    "page": {
                        "type": "integer",
                        "default": 1,
                        "minimum": 1,
                        "description": "页码，从 1 开始。每页约 20 条结果",
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["general", "time_descending", "popularity_descending"],
                        "default": "general",
                        "description": "排序方式：general=综合排序, time_descending=最新发布, popularity_descending=最热门",
                    },
                    "note_type": {
                        "type": "integer",
                        "enum": [0, 1, 2],
                        "default": 0,
                        "description": "笔记类型筛选：0=全部类型, 1=仅视频, 2=仅图文",
                    },
                },
                "required": ["keyword"],
            },
        ),
        Tool(
            name="search_note_suggestions",
            description="搜索关键词联想。返回小红书搜索结果中的推荐搜索词列表（建议词）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "搜索关键词（必填）"},
                    "page": {
                        "type": "integer",
                        "default": 1,
                        "minimum": 1,
                        "description": "页码，从 1 开始",
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["general", "time_descending", "popularity_descending"],
                        "default": "general",
                        "description": "排序方式",
                    },
                    "note_type": {
                        "type": "integer",
                        "enum": [0, 1, 2],
                        "default": 0,
                        "description": "笔记类型筛选：0=全部类型, 1=仅视频, 2=仅图文",
                    },
                },
                "required": ["keyword"],
            },
        ),
        Tool(
            name="get_note",
            description="获取小红书笔记详情（精简版）。返回标题、正文、作者、互动统计、发布时间及图片/视频链接。会优先复用搜索阶段写入的 xiaohongshu-cli xsec_token 缓存，也可显式传入 xsec_token。",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_id": {
                        "type": "string",
                        "description": "笔记 ID（必填）。可以从搜索结果或笔记 URL 中获取",
                    },
                    "note_type": {
                        "type": "string",
                        "enum": ["image", "video"],
                        "default": "image",
                        "description": "笔记类型：image=图文笔记, video=视频笔记。如果不确定类型，默认使用 image",
                    },
                    "xsec_token": {
                        "type": "string",
                        "default": "",
                        "description": "可选安全令牌。通常来自 search_notes 返回的 xsec_token；不传时会复用 xiaohongshu-cli 缓存。",
                    },
                    "xsec_source": {
                        "type": "string",
                        "default": "",
                        "description": "可选安全来源。搜索结果通常为 pc_search；不传时由 xiaohongshu-cli 决定默认值或读取缓存。",
                    },
                },
                "required": ["note_id"],
            },
        ),
        Tool(
            name="get_note_comments",
            description="获取笔记评论列表（精简版）。支持分页，返回评论内容、作者、点赞数、回复数与分页信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_id": {"type": "string", "description": "笔记 ID（必填）"},
                    "cursor": {
                        "type": "string",
                        "default": "",
                        "description": "分页游标。首次请求留空，后续请求使用上次返回的 cursor",
                    },
                    "xsec_token": {
                        "type": "string",
                        "default": "",
                        "description": "安全令牌。可以从搜索结果的 xsec_token 字段获取，用于访问评论",
                    },
                },
                "required": ["note_id"],
            },
        ),
        Tool(
            name="get_comment_replies",
            description="获取评论回复列表（精简版）。支持分页，返回回复内容、作者、点赞数与分页信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "note_id": {"type": "string", "description": "笔记 ID（必填）"},
                    "comment_id": {"type": "string", "description": "评论 ID（必填）"},
                    "cursor": {
                        "type": "string",
                        "default": "",
                        "description": "分页游标。首次请求留空，后续请求使用上次返回的 cursor",
                    },
                },
                "required": ["note_id", "comment_id"],
            },
        ),
        Tool(
            name="get_user_info",
            description="获取用户的个人资料信息。返回用户昵称、简介、粉丝数、关注数、获赞数等信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "用户 ID（必填）。可以从笔记作者信息或搜索结果中获取",
                    }
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="get_user_notes",
            description="获取用户发布的笔记列表。支持分页加载。返回笔记标题、封面图、点赞数等信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "用户 ID（必填）"},
                    "cursor": {
                        "type": "string",
                        "default": "",
                        "description": "分页游标。首次请求留空，后续请求使用上次返回的 cursor",
                    },
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="get_user_collections",
            description="获取用户收藏的笔记列表。支持分页加载。返回笔记标题、封面图、点赞数等信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "用户 ID（必填）"},
                    "cursor": {
                        "type": "string",
                        "default": "",
                        "description": "分页游标。首次请求留空，后续请求使用上次返回的 cursor",
                    },
                },
                "required": ["user_id"],
            },
        ),
        Tool(
            name="search_users",
            description="搜索小红书用户。返回用户列表，包含昵称、简介、粉丝数等信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词（必填）。例如：美妆博主、旅行达人",
                    }
                },
                "required": ["keyword"],
            },
        ),
        Tool(
            name="search_topics",
            description="搜索小红书话题。返回话题列表，包含话题名称、描述、参与人数等信息。",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词（必填）。例如：旅行、美食、穿搭",
                    }
                },
                "required": ["keyword"],
            },
        ),
        Tool(
            name="set_cookies",
            description="""手动设置小红书登录 Cookie。

从浏览器 DevTools 复制 Cookie 后调用此工具完成登录，无需扫码。
支持两种格式：
1. JSON 对象：{"a1": "...", "web_session": "...", ...}
2. Cookie 请求头字符串：a1=xxx; web_session=yyy; ...

建议至少包含 a1、web_session 字段。""",
            inputSchema={
                "type": "object",
                "properties": {
                    "cookies": {
                        "type": "string",
                        "description": "Cookie 内容，JSON 对象或 Cookie 请求头字符串均可",
                    }
                },
                "required": ["cookies"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
    """Handle tool calls."""
    try:
        # Initialize API client
        client = XiaohongshuClient()

        match name:
            case "search_notes":
                # Validate required parameters
                keyword = arguments.get("keyword")
                if not keyword:
                    raise McpError(
                        ErrorData(
                            code=INVALID_PARAMS, message="参数 'keyword' 是必填项"
                        )
                    )

                # Extract optional parameters
                page = arguments.get("page", 1)
                sort = arguments.get("sort", "general")
                note_type = arguments.get("note_type", 0)

                # Call API
                result = await client.search_notes(
                    keyword=keyword, page=page, sort=sort, note_type=note_type
                )

                # Format response
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
                    )
                ]

            case "search_note_suggestions":
                keyword = arguments.get("keyword")
                if not keyword:
                    raise McpError(
                        ErrorData(
                            code=INVALID_PARAMS, message="参数 'keyword' 是必填项"
                        )
                    )

                page = arguments.get("page", 1)
                sort = arguments.get("sort", "general")
                note_type = arguments.get("note_type", 0)

                result = await client.search_note_suggestions(
                    keyword=keyword,
                    page=page,
                    sort=sort,
                    note_type=note_type,
                )

                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
                    )
                ]

            case "get_note":
                # Validate required parameters
                note_id = arguments.get("note_id")
                if not note_id:
                    raise McpError(
                        ErrorData(
                            code=INVALID_PARAMS, message="参数 'note_id' 是必填项"
                        )
                    )

                note_type = arguments.get("note_type", "image")
                xsec_token = arguments.get("xsec_token", "")
                xsec_source = arguments.get("xsec_source", "")

                # Call appropriate API based on note type
                if note_type == "video":
                    result = await client.get_note_video(
                        note_id, xsec_token=xsec_token, xsec_source=xsec_source
                    )
                else:
                    result = await client.get_note_image(
                        note_id, xsec_token=xsec_token, xsec_source=xsec_source
                    )

                # Format response
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
                    )
                ]

            case "get_note_comments":
                note_id = arguments.get("note_id")
                if not note_id:
                    raise McpError(
                        ErrorData(
                            code=INVALID_PARAMS, message="参数 'note_id' 是必填项"
                        )
                    )

                cursor = arguments.get("cursor", "")
                xsec_token = arguments.get("xsec_token", "")
                result = await client.get_note_comments(
                    note_id=note_id, cursor=cursor, xsec_token=xsec_token
                )

                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
                    )
                ]

            case "get_comment_replies":
                note_id = arguments.get("note_id")
                comment_id = arguments.get("comment_id")
                if not note_id or not comment_id:
                    raise McpError(
                        ErrorData(
                            code=INVALID_PARAMS,
                            message="参数 'note_id' 和 'comment_id' 是必填项",
                        )
                    )

                cursor = arguments.get("cursor", "")
                result = await client.get_comment_replies(
                    note_id=note_id, comment_id=comment_id, cursor=cursor
                )

                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
                    )
                ]

            case "get_user_info":
                user_id = arguments.get("user_id")
                if not user_id:
                    raise McpError(
                        ErrorData(
                            code=INVALID_PARAMS, message="参数 'user_id' 是必填项"
                        )
                    )

                result = await client.get_user_info(user_id=user_id)

                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
                    )
                ]

            case "get_user_notes":
                user_id = arguments.get("user_id")
                if not user_id:
                    raise McpError(
                        ErrorData(
                            code=INVALID_PARAMS, message="参数 'user_id' 是必填项"
                        )
                    )

                cursor = arguments.get("cursor", "")
                result = await client.get_user_notes(user_id=user_id, cursor=cursor)

                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
                    )
                ]

            case "get_user_collections":
                user_id = arguments.get("user_id")
                if not user_id:
                    raise McpError(
                        ErrorData(
                            code=INVALID_PARAMS, message="参数 'user_id' 是必填项"
                        )
                    )

                cursor = arguments.get("cursor", "")
                result = await client.get_user_collections(
                    user_id=user_id, cursor=cursor
                )

                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
                    )
                ]

            case "search_users":
                keyword = arguments.get("keyword")
                if not keyword:
                    raise McpError(
                        ErrorData(
                            code=INVALID_PARAMS, message="参数 'keyword' 是必填项"
                        )
                    )

                result = await client.search_users(keyword=keyword)

                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
                    )
                ]

            case "search_topics":
                keyword = arguments.get("keyword")
                if not keyword:
                    raise McpError(
                        ErrorData(
                            code=INVALID_PARAMS, message="参数 'keyword' 是必填项"
                        )
                    )

                result = await client.search_topics(keyword=keyword)

                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
                    )
                ]

            case "set_cookies":
                cookies_input = arguments.get("cookies")
                if not cookies_input:
                    raise McpError(
                        ErrorData(
                            code=INVALID_PARAMS, message="参数 'cookies' 是必填项"
                        )
                    )
                result = await client.set_cookies(cookies_input)
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(result, ensure_ascii=False, indent=2),
                    )
                ]

            case _:
                raise McpError(
                    ErrorData(code=INVALID_PARAMS, message=f"未知的工具: {name}")
                )

    except McpError:
        # Re-raise MCP errors as-is
        raise
    except ValueError as e:
        # Parameter validation errors
        raise McpError(ErrorData(code=INVALID_PARAMS, message=f"参数错误: {str(e)}"))
    except Exception as e:
        # Network or API errors
        error_msg = str(e)
        error_type = type(e).__name__

        # Provide helpful error messages for common issues
        if (
            "SessionExpiredError" in error_type
            or "session expired" in error_msg.lower()
            or "登录" in error_msg
        ):
            error_msg = (
                "Cookie 已过期。请引导用户运行 'set_cookies' 工具重新设置 Cookie。"
            )
        elif "cookie" in error_msg.lower():
            error_msg = (
                f"Cookie 获取失败: {error_msg}. 请引导用户运行 'set_cookies' 工具。"
            )
        elif "验证" in error_msg or "verify" in error_msg.lower():
            error_msg = "需要验证码或账号被风控。请引导用户在浏览器完成验证，然后重新设置 Cookie。"
        elif "429" in error_msg or "频繁" in error_msg:
            error_msg = "请求过于频繁，请稍后再试。"

        raise McpError(
            ErrorData(code=INTERNAL_ERROR, message=f"API 调用失败: {error_msg}")
        )


async def main():
    """Run the MCP server."""
    # Run server with stdio transport
    async with stdio_server() as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())


if __name__ == "__main__":
    import anyio

    anyio.run(main)
