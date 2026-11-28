# 芋道产品、供应商与 SKU

首版为员工维护供应商档案。供应商档案不是厂家登录账号。MCP 与芋道表单调用同一业务 API，使用当前员工账号的权限；没有绕过权限的管理员密钥。

用户反馈“只有厂家、没有商品/SKU”、续作之前失败的录入、或模型回报与后台不符时，先执行[入库回读与断点处理](reconcile.md)，再决定补哪一步。不能把上轮文字总结或创建返回的一个 ID 当作本轮验证。

## 连接

已运行公司生成的员工安装包时，直接使用已配置的 `yona_enterprise` MCP；安装包自带独立 Python、企业 CA 和本人私有会话，无需再按下文手工新建配置或安装 Python。会话过期可在员工包目录重新运行 `setup-employee.ps1`，只以本人芋道账号重新登录，其他 MCP 配置保留。首次使用仍需在实际 Codex 新会话中确认工具可见。

安装工具包需要 Python 3.11+。复制 `enterprise-config.example.json` 到私有配置目录，设置真实 `base_url`、实际租户 ID、`session_file` 绝对路径。服务器本机使用安装器实际打印的 loopback 入口，不猜测 8081 的绑定。员工电脑使用公司提供的 HTTPS 入口和公有 CA 文件，配置 `ca_file` 绝对路径；证书链及服务地址必须验证，不关闭 TLS 校验。默认只读，用户授权维护时设 `write_enabled=true`。

在本机终端手动运行 `python <工具包绝对路径>/enterprise.py --config <私有配置绝对路径> --login`，输入自己的芋道账号和密码。密码不保存，临时会话写入限权文件；不要把密码/会话写入 Skill、资料包、飞书、截图或命令参数。登录遇到验证码或账号限制时遵循正常登录流程，不能绕过。会话过期后重新登录。

Codex MCP 配置增补独立入口，保留其他 MCP：

```toml
[mcp_servers.yona_enterprise]
command = "python"
args = ["C:/YONA-Catalog-Tools/enterprise.py", "--config", "C:/YONA-Private/enterprise-config.json"]
```

## 维护流程

1. 先 `enterprise_supplier_search` 和 `enterprise_product_search` 查重，再读具体记录。不要仅因名称、OE 相同就合并厂家或产品。
   厂家关联产品按页读取，用厂家 ID 与精确供方 SKU 定位已有关系；不要只查第一页。每批将来源文件 SHA、页/行号、稳定请求键和返回 ID/版本写入本机私有回执，重试先回读同批回执及服务器状态。已有 SKU 指向产品时维护该产品，不随目录修订重复建商品。
2. 新供应商使用 `enterprise_supplier_create`，profile 字段为 `name,categories,website,publicContact,privateContact,publicationEvidence`；未知值用空字符串。它只创建内部草稿。超时后先搜索核对是否创建成功，不盲目再建。
3. 新产品先 `enterprise_candidate_stage`，以稳定 `request_key` 标识这一请求，并附原始来源位置。字段包含 `name,category,supplierSku,brand,model,specification,attributes,oeNumbers,vehicleFitment,unit,aliases,historicalHandler`，报价字段按资料原样保留。商品属性按 [完整属性与搜索验收](product-quality.md) 保留。先验证服务器兼容性：基线服务放入 `specification`（2000字符），确认支持后才用独立 `attributes`（4000字符）。每行保留原属性名和值，不能只抄标题而遗漏属性表。区分商家声明与已核实事实，共用链接的属性不能自动视为指定SKU已确认，需原样标注适用范围和待核实项。OE、SKU、型号必须文本。有主图时，先 `enterprise_candidate_image_upload`，传候选 ID、当前 `version`、图片相对路径及来源；上传返回的新 `version` 用于后续确认。用 `enterprise_candidate_list` 回读主图和版本，按用户已授权范围校对并 `enterprise_candidate_confirm`，新产品会同时继承主图。候选保存不代表入库；确认重试不会重复创建。`existing_product_id` 仅用于同一产品的新增报价，候选图片保留在本次候选，不覆盖已有产品的主图。
4. 已入库产品用 `enterprise_product_edit_snapshot` 读取当前字段与版本，再 `enterprise_product_save` 提交完整产品字段、当前版本、修改来源。该工具替换产品事实；保留原值中不需修改的字段，不可发送报价、联系方式等字段来覆盖历史。冲突时重读合并；不以旧版本覆盖别人改动。用 `enterprise_product_changes` 核对前后值和来源。
5. 用 `enterprise_supplier_sku_save` 建立产品→厂家→厂家 SKU 关联。每个产品可有多家厂家；同一家厂家的同一 SKU 只能指向一个产品。SKU 保留大小写和前导零。第一次不用 `link_id`；修改时先读 `enterprise_product_suppliers`，传 `link_id` 与当前 `version`。来源记录页码、行号或商家链接。
6. `enterprise_supplier_products` 反查该员工有权查看的关联产品，再用产品详情核对字段。解除错误关联使用具体 link ID 与版本；不删除产品或供应商档案。
7. 更新供应商先读 `enterprise_supplier_detail`，再用当前版本提交完整 profile。编辑已公开的资料会回到草稿；供应商档案工具不公开发布厂家档案、不修改访问权限。商品官网上架、更新和撤回按 [官网发布与验收](publication.md) 使用独立工具，需要用户明确的公开操作指令。
8. 已入库产品换主图用 `enterprise_product_image_upload`。两种图片工具都传 `image_root` 内的相对路径，仅支持 PNG/JPEG、最大 5MB。本地厂家目录图片用真实 `source_locator`（文件名、页码、厂家说明等）；网上原图可传 `source_page_url` 和 `source_image_url` 两个真实 HTTPS 地址。不能编造链接满足来源校验。图片必须对应当前产品/厂家 SKU，不用相似商品图。`image_root` 与会话目录分开；上传后回读图片 SHA、产品详情和列表。未配置图片目录时两种上传工具均隐藏。

图片上传或确认发生超时，先回读该候选及版本、状态和主图，或读取已返回的产品 ID，再决定是否重试。确认已成功后不能通过重新创建候选“补传图片”。SKU 关联失败时读取该产品已有的关联后补齐，不能再创建一条产品。普通网页来源图片仍使用原副本格式；包含本地目录来源的图片需要支持 schema 3 的接收端，不能对旧接收端假报同步成功。

RAGFlow 提取的车型/技术信息只能在有对应来源、逐项核对后作为事实提交。网上补充仍按 `web-evidence.csv` 保存为待核实；不能以检索命中替代适配确认。保存成功后回读，再报告产品 ID、供应商 ID、SKU、版本和来源，不在交付记录中包含凭据。
