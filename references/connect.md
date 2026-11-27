# 安装与连接

工具包需要 Python 3.11+，MCP/CLI 不需要额外 Python 包。RAGFlow 需单独部署、完成账号和模型配置；工具包不会凭空提供知识库或 API 额度。

1. Skill 安装/更新使用 [版本与更新](updates.md)，默认用户目录 `~/.agents/skills/yona-supplier-catalog`。旧目录保留备份但不留在技能搜索路径，避免同名副本。业务工具仍使用员工已有安装包；Skill 更新不覆盖 MCP 配置。
2. 管理员为客户提供其自己的 RAGFlow 账号和获准资料库。客户在自己账号的 API 设置生成 Key，写入上传根目录以外的私有文件；不要发送管理员 Key。
3. 按 `catalog-config.example.json` 填写真实地址、32 位数据集 ID、资料根目录、凭据文件与私有状态目录。远程必须用有效 HTTPS；仅同机 `localhost`/`127.0.0.1` 可用 HTTP。`write_enabled=false` 只开放查询；客户获准上传时设为 true。
4. 增补 Codex MCP 配置，路径换为实际绝对路径（示例不是已接通的地址）：

```toml
[mcp_servers.yona_catalog]
command = "python"
args = ["C:/YONA-Catalog-Tools/server.py", "--config", "C:/YONA-Private/catalog-config.json"]
```

确认能列出 `catalog_package_plan` 等工具，再使用 Skill。也可不通过 MCP，用相同工具的 CLI：

```powershell
python C:/YONA-Catalog-Tools/server.py --config C:/YONA-Private/catalog-config.json --tool catalog_package_plan --arguments '{"manifest":"SUPPLIER-001/20261125-v1/manifest.json"}'
```

RAGFlow 的 `permission=me` 适合个人私有资料；`team` 会扩大到团队维护权限，不能仅为“方便连接”而修改。客户/供应商隔离需要服务端账号和库权限一起验收；本机配置文件不是服务端多租户隔离的替代品。

RAGFlow 上传、开始解析、处理结束、实际检索命中和技术适配确认分别是不同状态。Embedding 是检索基础；LLM 用于服务端生成问答时另外配置。通过 Codex MCP 检索可由 Codex 解释片段，但不能宣称 RAGFlow 聊天机器人已上线。

公司服务器仅通过向日葵接入时，在公司远程桌面安装并进行回环访问测试。其他员工要在自己的电脑使用，需要公司批准的内网 HTTPS/VPN 或各自的本机部署；向日葵桌面控制本身不等于开放 RAGFlow API。先保持回环绑定，待网络入口落实后再配置反向代理。
