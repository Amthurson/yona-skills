# 资料包格式 v1

建议目录：`SUPPLIER-001/20261125-v1/`。MCP 配置的 `package_root` 指向供应商资料工作的专用父目录。

```text
SUPPLIER-001/20261125-v1/
  manifest.json
  products.csv
  originals/catalog.pdf
  images/SKU-001.jpg
  web-evidence.csv       # 有网上补充信息时再加
```

所有 manifest 路径和 CSV 文件引用都相对于 `package_root`，使用 `/`。必须显式列出产品行引用的原件和图片。拒绝绝对路径、`..`、符号链接、目录联接和重复文件；每包 1–100 文件，每文件最多 20 MiB，合计最多 100 MiB。大目录分批，不截断或丢页。

```json
{
  "version": 1,
  "supplier_id": "SUPPLIER-001",
  "package_id": "20261125-v1",
  "files": [
    {"path": "SUPPLIER-001/20261125-v1/originals/catalog.pdf", "kind": "catalog"},
    {"path": "SUPPLIER-001/20261125-v1/products.csv", "kind": "products"},
    {"path": "SUPPLIER-001/20261125-v1/images/SKU-001.jpg", "kind": "image"}
  ]
}
```

从 `assets/products-template.csv` 复制表头，UTF-8 保存。各列均为文字，不在 Excel 中把 OE 转为数值或科学记数。必填 `supplier_sku`、`name`、`source_file`、`source_page`、`status`。`status` 为 `supplier_provided` 或 `pending_review`。其他列无可靠资料时留空。`source_file` 与 `main_image_path` 必须指向 manifest 中的文件；主图可以留空。源页示例：`p12` 或 `目录表:行23`。

网上补充单独使用 `assets/web-evidence-template.csv`，manifest 的 kind 为 `web_evidence`。必须保留 SKU、字段、值、来源链接、访问日期（YYYY-MM-DD）、短引文，状态固定为 `pending_review`。不要把补充表内容倒写成商家原始声明。

支持原件 PDF、XLS/XLSX、CSV、TXT、Markdown、DOCX 和 PNG/JPEG；格式被接受并不保证服务器已配置对应 OCR/解析模型。视频及 ZIP 不直接入库，先拆为明确资料，保留原件另行归档。
