# 小红书 MCP Server

基于 [xiaohongshu-cli](https://github.com/jackwener/xiaohongshu-cli) 的 MCP (Model Context Protocol) 服务器，为 OpenCode 提供小红书数据访问能力。

## ✨ 特性

- 🔍 **搜索笔记** - 关键词搜索，支持排序和类型过滤
- 📝 **笔记详情** - 获取完整内容、图片/视频、互动数据
- 💬 **评论系统** - 获取评论和子评论（支持分页）
- 👤 **用户信息** - 用户资料、发布笔记、收藏列表
- 🔎 **搜索用户/话题** - 发现博主和热门话题
- 🆓 **完全免费** - 基于开源库，无 API 调用费用
- 🔒 **隐私安全** - Cookie 本地存储，不上传第三方

## 📦 安装

### 前置要求

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (推荐) 或 pip

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/xiaohongshu-mcp.git
cd xiaohongshu-mcp

# 2. 创建虚拟环境并安装依赖
uv venv venv
uv pip install --python venv/bin/python -e .
uv pip install --python venv/bin/python xiaohongshu-cli

# 3. 配置 Cookie
# 从浏览器获取 Cookie（见下方说明）
cat > cookies.json << 'EOF'
{
  "web_session": "你的web_session",
  "a1": "你的a1",
  "webId": "你的webId"
}
EOF

# 4. 配置 OpenCode
# 在 ~/.config/opencode/opencode.json 的 mcpServers 中添加：
{
  "xiaohongshu": {
    "type": "local",
    "command": ["/绝对路径/xiaohongshu-mcp/venv/bin/python", "-m", "xiaohongshu_mcp.server"],
    "environment": {
      "PYTHONPATH": "/绝对路径/xiaohongshu-mcp"
    },
    "enabled": true
  }
}
```

### 获取 Cookie

1. 在浏览器中访问 https://www.xiaohongshu.com/ 并登录
2. 按 F12 打开开发者工具 → Application/存储 → Cookies → https://www.xiaohongshu.com
3. 复制以下三个 Cookie 的值：
   - `web_session`
   - `a1`
   - `webId`
4. 粘贴到 `cookies.json` 文件中

**Cookie 有效期：** 约 7 天，过期后重新获取即可。

## 🔧 可用工具

### 笔记相关

#### `xiaohongshu_search_notes` - 搜索笔记
搜索小红书笔记，支持关键词、排序和类型筛选。

**参数：**
- `keyword` (必填): 搜索关键词
- `page` (可选): 页码，默认 1
- `sort` (可选): 排序方式
  - `general`: 综合排序（默认）
  - `time_descending`: 最新发布
  - `popularity_descending`: 最热门
- `note_type` (可选): 笔记类型
  - `0`: 全部类型（默认）
  - `1`: 仅视频
  - `2`: 仅图文

#### `xiaohongshu_get_note` - 获取笔记详情
获取笔记的完整内容、图片/视频 URL、作者信息、互动数据。

**参数：**
- `note_id` (必填): 笔记 ID
- `note_type` (可选): `image` 或 `video`，默认 `image`

#### `xiaohongshu_get_note_comments` - 获取笔记评论
获取笔记的评论列表，支持分页。

**参数：**
- `note_id` (必填): 笔记 ID
- `cursor` (可选): 分页游标
- `xsec_token` (可选): 安全令牌（从搜索结果获取）

#### `xiaohongshu_get_comment_replies` - 获取评论回复
获取某条评论的子评论列表，支持分页。

**参数：**
- `note_id` (必填): 笔记 ID
- `comment_id` (必填): 评论 ID
- `cursor` (可选): 分页游标

### 用户相关

#### `xiaohongshu_get_user_info` - 获取用户资料
获取用户昵称、简介、粉丝数、关注数、获赞数。

**参数：**
- `user_id` (必填): 用户 ID

#### `xiaohongshu_get_user_notes` - 获取用户笔记
获取用户发布的笔记列表，支持分页。

**参数：**
- `user_id` (必填): 用户 ID
- `cursor` (可选): 分页游标

#### `xiaohongshu_get_user_collections` - 获取用户收藏
获取用户收藏的笔记列表，支持分页。

**参数：**
- `user_id` (必填): 用户 ID
- `cursor` (可选): 分页游标

### 搜索相关

#### `xiaohongshu_search_users` - 搜索用户
按关键词搜索用户。

**参数：**
- `keyword` (必填): 搜索关键词

#### `xiaohongshu_search_topics` - 搜索话题
按关键词搜索话题。

**参数：**
- `keyword` (必填): 搜索关键词

## 🚀 使用示例

在 OpenCode 中与 AI 对话：

```
# 搜索笔记
帮我搜索小红书上关于"旅游攻略"的热门笔记

# 获取笔记详情
获取这条笔记的详细内容：697c0eee000000000a03c308

# 获取评论
获取这条笔记的评论：66f906a5000000001b022fc4

# 搜索用户
搜索小红书上的"美妆博主"

# 组合使用
搜索"美食推荐"，然后获取第一条笔记的详情和评论
```

## ⚠️ 常见问题

### Cookie 过期

**现象：** 返回错误 "Cookie 已过期"

**解决：** 按照上方"获取 Cookie"步骤重新获取并更新 `cookies.json`

### 需要验证码

**现象：** 返回 "需要验证码或账号被风控"

**解决：** 在浏览器中完成验证后重试

### 请求频繁

**现象：** 返回 "请求过于频繁"

**解决：** 等待几秒后重试

## 📝 项目结构

```
xiaohongshu-mcp/
├── .gitignore              # Git 忽略文件
├── pyproject.toml          # 项目配置
├── README.md               # 本文档
├── cookies.json            # Cookie 配置（不提交到 Git）
├── venv/                   # 虚拟环境（不提交到 Git）
└── xiaohongshu_mcp/
    ├── __init__.py
    ├── server.py           # MCP 服务器主逻辑
    └── client.py           # xiaohongshu-cli 封装
```

## 🙏 致谢

- [xiaohongshu-cli](https://github.com/jackwener/xiaohongshu-cli) - 提供核心功能
- [MCP](https://modelcontextprotocol.io/) - Model Context Protocol

## 📄 License

MIT License
