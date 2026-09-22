# 文档索引

日常开发、构建、添加字体和部署命令见[项目 README](../README.md)。

| 位置 | 用途 |
| --- | --- |
| [specs/catalogue-rating.md](specs/catalogue-rating.md) | 现行 Auto 评分公式、手动调整和 Google Fonts 加分 |
| [import-report.md](import-report.md) | 导入器的统计与人工收录记录；保留固定路径及 `opf:manual` 标记 |
| [audits/](audits/) | 字体来源、许可、转换与部署审计，按记录日期保留 |
| [research/gb18030-2022-levels.md](research/gb18030-2022-levels.md) | GB 18030 字表构造依据，生成器仍引用它 |
| [archive/](archive/) | 初始设计及旧接口约定，仅供历史参考 |

## 审计入口

- Google Fonts：[早期覆盖检查](audits/google-fonts-coverage-audit.md)、[完整导入](audits/google-fonts-import-audit-2026-09-17.md)、[Jacquard / Jersey / Handjet](audits/google-fonts-jacquard-jersey-handjet-audit-2026-09-17.md)、[Bitcount 合并与 Prop Single](audits/bitcount-family-audit-2026-09-17.md)。
- 导入修复：[DotGothic16 与减分字体核对](audits/dotgothic16-import-audit-2026-09-18.md)、[kbitx 解码](audits/kbitx-decoder-audit-2026-09-17.md)、[默认字号、Frogatto、Chunky Sans、Poxiao](audits/font-preview-and-import-fixes-2026-09-18.md)。
- 收录与标签：[itch.io FOSS 点阵字体](audits/itch-foss-font-import-audit-2026-09-18.md)、[扩充批次及三款补充导入](audits/style-expansion-audit-2026-09-17.md)、[Vibes](audits/vibes-audit-2026-09-17.md)、[CJK 关系图与扇尾胄黑](audits/cjk-map-and-shanweizhouhei-2026-09-17.md)。
- 来源与许可：[来源复核](audits/font-provenance-review-2026-09-17.md)、[Oldschool PC](audits/oldschool-pc-license-review-2026-09-17.md)、[Debian 包清单](audits/debian-fonts-pc-contents-2026-09-17.md)。
- 部署：[Cloudflare Pages 容量与预览迁移记录](audits/hosting-audit-2026-09-17.md)。

## 保留与更新原则

审计中的家族数、测试数和部署容量是当时的快照；当前行为以代码、项目 README
和 `specs/` 为准。审计目录里的 JSON 保存来源哈希、字符映射、像素指纹及许可
依据，部分还由 Python 和浏览器测试直接读取，不是可随意删除的临时输出。

同一问题的后续修正优先更新原说明；只有独立的来源或验证证据才新增审计。
普通 UI 调整、一次性测试日志和已完成的任务清单无需另建文档。
重复补充说明合并到所属主题；过时设计放进 `archive/`，不作为当前操作指令。
