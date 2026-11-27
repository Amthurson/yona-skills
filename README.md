# YONA Skills

统一维护供应商、商品完整属性、图片、SKU和搜索验收的Codex操作规范。仓库根目录是一个`yona-supplier-catalog` Skill；使用者通过自己的企业MCP操作，仓库不含业务服务、客户目录或账号。

## 客户安装

首次对Codex说：

> 从 https://github.com/Amthurson/yona-skills 安装YONA供应商产品Skill。保留其他Skills与MCP配置；已有同名旧版时先备份并改成可更新的Git副本。

有Git和PowerShell时，也可在任意工作目录执行：

```powershell
git clone https://github.com/Amthurson/yona-skills.git yona-skills-source
powershell -NoProfile -File .\yona-skills-source\scripts\install.ps1
```

默认安装到当前用户的`~/.agents/skills/yona-supplier-catalog`。旧目录会先备份到该用户的`AppData/Local/YONA/SkillManager`，不与其他Skills混放，不修改MCP登录或系统证书。

## 客户日常使用

> 更新YONA Skill到最新稳定版，告诉我版本和commit。然后按此Skill处理我指定目录的商品，完整保留属性、来源、供应商和SKU，回读入库结果并验证前端搜索。

已装Git版可直接运行：

```powershell
powershell -NoProfile -File "$env:USERPROFILE\.agents\skills\yona-supplier-catalog\scripts\update.ps1"
```

更新前要求Skill工作副本没有本地修改；正常更新只快进。回退标签使用`-Version 0.3.0`。Codex检测Skill变化后使用新规范；未刷新时新开一轮或重启。商品是否已入库、是否已同步到巴西，仍以实际MCP和前端查询回执为准。

旧业务服务也可使用完整属性规范：将源属性保存在规格文本中；独立属性字段只用于已验证支持的服务器。更新Skill不会自动完成服务器升级、RAGFlow接入或历史商品补录。

## 维护与发布

在维护者的工作副本优化`SKILL.md`、`references`、`assets`，同步修改manifest与frontmatter版本。发布前执行：

```powershell
python scripts/validate.py
python -m unittest discover -s tests -v
```

仓库在Windows CI中自动执行这些检查。通过后合并到稳定分支`main`，创建对应`v<版本>`标签。客户端校验标签指向该提交，尚未打标签的修改不会替换客户当前版本。客户只拉取更新，不自动把资料或本地定制推回。商品工作文件保存在单独目录，不能提交到这个公开仓库。

## 迁移到客户GitLab

将Git历史与版本标签迁到客户指定仓库，在GitLab更新manifest中的`repository`。客户运行同一个更新脚本并传`-Origin <客户GitLab仓库地址>`即可切换。脚本先检查目标Skill身份；认证使用客户自己的Git凭据，不迁移账号令牌。详见[更新约定](references/updates.md)。

本仓库仅提供通用规范、合成模板、更新脚本和离线测试，不放客户真实商品、图片、服务器地址、配置或凭据。

官网发布规范见 [官网发布与验收](references/publication.md)。新发布工具需要配套公司服务及员工 MCP 客户端；更新 Skill 本身不升级服务器或开通发布权限。
