# 🎯 小红书 MCP Server - 测试指南

## ✅ 安装完成

原型已成功创建并配置！以下是测试步骤。

---

## 📋 测试前准备

### 1. 重新加载环境变量

```bash
# 在当前终端执行
source ~/.bashrc

# 验证 API Key 已设置
echo $XIAOHONGSHU_API_KEY
# 应该输出: sk-95c2aa7f560fd2c9b9902b6a351b409dda2b84efb8b00b2b
```

### 2. 验证 MCP Server 配置

```bash
# 检查 OpenCode 配置
cat ~/.config/opencode/opencode.json | grep -A 8 "xiaohongshu"

# 应该看到:
# "xiaohongshu": {
#   "type": "local",
#   "command": ["python3", "-m", "xiaohongshu_mcp.server"],
#   ...
# }
```

### 3. 验证模块加载

```bash
cd ~/.local/share/opencode/mcp-servers/xiaohongshu
PYTHONPATH=. python3 -c "from xiaohongshu_mcp.server import server; print('✅ OK')"
```

---

## 🚀 启动新的 OpenCode 会话

**重要**: 必须启动**新的 OpenCode 会话**才能加载 MCP Server。

```bash
# 方法 1: 重启 OpenCode
# 关闭当前会话，重新打开

# 方法 2: 启动新会话（如果支持）
opencode --new-session
```

---

## 🧪 测试 Prompts

在新的 OpenCode 会话中，依次发送以下测试 prompt：

### 测试 1: 基础搜索（推荐首次测试）

```
帮我搜索小红书上关于"咖啡"的笔记，只要前 5 条结果
```

**预期结果**:
- Agent 调用 `xiaohongshu_search_notes` 工具
- 返回 JSON 格式的搜索结果
- 包含笔记标题、作者、封面图、点赞数等

**成功标志**:
```json
{
  "success": true,
  "data": {
    "items": [...]
  }
}
```

---

### 测试 2: 获取笔记详情

```
获取这条小红书笔记的详细内容：697c0eee000000000a03c308
```

**预期结果**:
- Agent 调用 `xiaohongshu_get_note` 工具
- 返回笔记完整内容、图片列表、作者信息

**注意**: 如果遇到 "访问频繁" 错误，等待 5-10 秒后重试

---

### 测试 3: 高级搜索

```
搜索小红书上关于"旅游攻略"的最热门图文笔记
```

**预期结果**:
- Agent 自动推断参数:
  - `keyword`: "旅游攻略"
  - `sort`: "popularity_descending"
  - `note_type`: 2 (图文)

---

### 测试 4: 组合使用

```
搜索"美食推荐"相关的最新笔记，然后获取第一条笔记的详细内容
```

**预期结果**:
- Agent 先调用 `xiaohongshu_search_notes`
- 从结果中提取第一条笔记的 ID
- 再调用 `xiaohongshu_get_note` 获取详情

---

## 🔍 验证工具可用性

在 OpenCode 会话中，可以询问：

```
你有哪些小红书相关的工具？
```

**预期回答**: Agent 应该列出两个工具：
1. `xiaohongshu_search_notes` - 搜索笔记
2. `xiaohongshu_get_note` - 获取笔记详情

---

## ⚠️ 常见问题排查

### 问题 1: Agent 说 "没有小红书工具"

**原因**: MCP Server 未加载

**解决**:
```bash
# 1. 确认配置正确
cat ~/.config/opencode/opencode.json | grep xiaohongshu

# 2. 确认环境变量
echo $XIAOHONGSHU_API_KEY

# 3. 重启 OpenCode（必须）
```

---

### 问题 2: API 返回 "访问频繁"

**原因**: 速率限制（正常现象）

**解决**: 等待 5-10 秒后重试

---

### 问题 3: API 返回 "账号池异常"

**原因**: 服务商账号池补充中

**解决**: 等待 1-2 分钟后重试

---

### 问题 4: "XIAOHONGSHU_API_KEY not set"

**解决**:
```bash
# 重新加载环境变量
source ~/.bashrc

# 或手动设置（临时）
export XIAOHONGSHU_API_KEY='sk-95c2aa7f560fd2c9b9902b6a351b409dda2b84efb8b00b2b'
```

---

### 问题 5: "ModuleNotFoundError: xiaohongshu_mcp"

**原因**: PYTHONPATH 未正确设置

**解决**: 检查 `opencode.json` 中的 `environment.PYTHONPATH` 配置

---

## 📊 测试成功标准

✅ **原型测试通过**，如果满足以下条件：

1. Agent 能识别并调用 `xiaohongshu_search_notes` 工具
2. Agent 能识别并调用 `xiaohongshu_get_note` 工具
3. API 返回 `"success": true` 的 JSON 数据
4. Agent 能正确解析和展示搜索结果

---

## 🎉 测试成功后

如果测试通过，你可以：

1. **日常使用**: 直接在 OpenCode 中搜索小红书内容
2. **扩展功能**: 编辑 `~/.local/share/opencode/mcp-servers/xiaohongshu/xiaohongshu_mcp/server.py` 添加更多工具
3. **分享配置**: 将 MCP Server 分享给其他 OpenCode 用户

---

## 📝 反馈测试结果

测试完成后，请反馈：

1. ✅ 哪些测试通过了
2. ❌ 遇到了什么问题
3. 💡 需要添加什么功能

---

## 🔗 相关文件

- **MCP Server 代码**: `~/.local/share/opencode/mcp-servers/xiaohongshu/`
- **配置文件**: `~/.config/opencode/opencode.json`
- **完整文档**: `~/.local/share/opencode/mcp-servers/xiaohongshu/README.md`
- **API 文档**: https://rnote.dev/docs/guide

---

**祝测试顺利！🚀**
