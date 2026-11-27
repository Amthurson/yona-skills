# 版本、更新与GitLab交付

版本记录在 `skill-release.json`。本仓库根目录是一个 `yona-supplier-catalog` Skill，不包含项目程序、企业地址或凭据。

用户说“更新YONA Skill到最新稳定版”时，使用当前目录的 `scripts/update.ps1`，不要另装同名副本。更新需干净的Git工作副本，默认只快进到 `origin/main`；本地修改或分叉会停止保留。

```powershell
powershell -NoProfile -File <Skill目录>/scripts/update.ps1
```

旧员工包为复制安装、没有`.git`时，先用本目录 `scripts/install.ps1 -Destination <当前Skill绝对目录>` 转为受管理副本。先克隆校验，再将旧目录备份到Skill搜索目录外，不覆盖其他Skills或MCP配置。不用清空目录或`git reset --hard`代替更新。

回读版本及Git commit后报告来源和变化。Codex会检测Skill文件更新；未出现时新开一轮或重启。之后重新读取本任务参考。更新本身不导入商品、不升级服务器、不调用付费模型、不修改账号或权限。

回退到已发布标签使用 `-Version 0.2.0`（标签`v0.2.0`）；不传版本恢复最新稳定渠道。

## 维护者

在单独工作副本修改规范、参考和模板，更新manifest与frontmatter中相同的版本，运行校验和更新回归，再合并到`main`、创建不覆盖的版本标签。客户端会检查`main`提交与声明版本的标签一致；未发布的修改不会替换客户当前版本。客户目录不是维护源，不自动推回资料或定制内容。

## GitLab

交付后迁移仓库历史与标签到用户指定GitLab仓库，并在该仓库更新manifest的`repository`。客户切换：

```powershell
powershell -NoProfile -File <Skill目录>/scripts/update.ps1 -Origin <客户GitLab仓库地址>
```

只接受用户或交付配置提供的地址。脚本先获取并验证目标属于本Skill，再切换origin。私有GitLab认证使用客户自己的Git凭据管理器，不复制GitHub令牌。不知道地址或权限时，只交付迁移方法，不声称迁移完成。
