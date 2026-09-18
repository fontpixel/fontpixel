# Oldschool PC Font Pack 权利依据复核 — 2026-09-17

本记录纠正把整包 CC BY-SA 声明直接等同于原始字形已获原厂开放授权的说法。此次核对授权依据，不据此宣称侵权，也不将本站的技术收录数量当成无争议版权的证明。

## 原作者实际声明

[官方 README 的 FAQ 与 Legal Stuff](https://int10h.org/oldschool-pc-fonts/readme/)说明：原始点阵来自旧电脑硬件、固件和相关软件；VileR 不主张原始点阵字符数据的权利，重制字体文件和扩展内容以 CC BY-SA 4.0 发布。作者对可分发性的论据是美国对字形设计的版权处理，并非 README 展示了每个原厂的授权书。Plus 版本含有作者新增的字形，不能把全部工作描述成仅仅转存文件。

## 能确认与不能推导的结论

[美国版权局 Circular 33](https://www.copyright.gov/circs/circ33.pdf)解释，字形设计及单纯的字形装饰变化通常不受版权保护；[Compendium §313.3(D)、§723](https://www.copyright.gov/comp3/docs/compendium.pdf)另行讨论具有足够原创表达的字体生成程序。因此作者的理由有相关制度依据，不能仅因原始字形不是他设计的就断言侵权。若某部分在适用法下不受版权保护，使用该部分本来就不需要版权许可。

[CC BY-SA 4.0 原文](https://creativecommons.org/licenses/by-sa/4.0/legalcode.en)将授权限定于许可人有权授予的权利，也明确区分无需许可的使用。格式转换、署名或附上 CC 文本不会自动替第三方授予权利。

目前核验的是作者对重制文件的开放许可，以及他针对美国法提出的原始点阵不受保护的依据；没有完成每个原始字形在其他适用法下的独立权利状态核查。因此，不能将整包写成“原厂已明确开源”或“肯定不存在任何版权问题”。另一方面，缺少逐项原厂授权书本身也不能直接推出“不自由”：作者对原始点阵的论据是无需版权许可，而不是代表原厂授予许可。收录判断需要同时考虑这一依据和下述发行版的正式接纳记录。

## 影响范围与当前状态

**最终决定为全部保留。** 用户在了解发行版收录及公开争论后，明确要求恢复 Oldschool PC 并继续保留其他字体。已将 131 个 `oldschool-*` 家族及 `ibm-bios`、`ibm-cga`、`ibm-cga-light`、`ibm-ega`、`ibm-mda`、`ibm-vga` 六个家族恢复到 `fonts/`，共 **137 个家族、328 个变体**；manifest 对应的临时排除项已删除，原导入规则恢复。恢复后目录为 **411 个家族、1,433 个变体**。

此前临时撤下的名单保留为 [历史操作记录](oldschool-pc-excluded-2026-09-17.json)，其中状态已标为 restored，不是当前排除清单。相邻收藏目录保留撤下前的 manifest 和索引快照，字体本身已移回正式来源目录。Galmuri、Chusung、Lyusung 及其他字体继续保留；[全库来源审查](font-provenance-review-2026-09-17.md) 保留实际来源证据，原来的撤下建议已取消。

## Linux 发行版收录及公开争论

- **Debian main**：正式收录 [fonts-pc](https://packages.debian.org/trixie/fonts-pc) 和 [fonts-pc-extra](https://packages.debian.org/trixie/fonts-pc-extra)，版本 1.0-2；[Debian Sources](https://sources.debian.org/src/fonts-pc/1.0-2/README.NFO/) 明确标记 area 为 main。直接检查官方二进制包得到 8 和 73 个 TTF，包含尺寸和拉伸变体；[完整文件清单](debian-fonts-pc-contents-2026-09-17.md)保存字体内嵌名称和包哈希。
- **Ubuntu**：[noble 的 fonts-pc](https://packages.ubuntu.com/noble/fonts/fonts-pc) 位于 universe，版本 1.0-2。
- **Nixpkgs**：[正式打包定义](https://github.com/NixOS/nixpkgs/blob/master/pkgs/by-name/ul/ultimate-oldschool-pc-font-pack/package.nix) 收录 2.2，标记 CC-BY-SA-4.0。
- **openSUSE Factory**：[正式项目包](https://build.opensuse.org/package/show/openSUSE%3AFactory/int10h-oldschoolpc-fonts) 收录 `int10h-oldschoolpc-fonts` 2.2。

发行版接纳是重要的正面证据，不能将该包简单称为“假开源”，也不能把维护者附上许可等同于已有逐个原厂授权文件。

**直接争论**：2026-04-28，OpenBSD ports（不是 Linux）讨论该包时，[Stuart Henderson](https://www.mail-archive.com/ports%40openbsd.org/msg140193.html) 质疑硬件提取字体能否重新赋予 CC BY-SA，并质疑允许包及源文件再分发的标记；[Anthony J. Bentley](https://www.mail-archive.com/ports%40openbsd.org/msg140198.html) 以美国法区分字形与字体程序作回应，未对美国以外法律表态。这些邮件证明存在分歧，不证明最终拒收或法律裁决。

**相关但不同的案件**：Debian 的 [2021 年 fonts-amiga 打包邮件](https://mail-archive.com/debian-bugs-dist%40lists.debian.org/msg1796528.html) 提到因权利疑问被拒收，并询问为何 fonts-pc 可以进入仓库。被拒收的是当时提交的 fonts-amiga，不是 fonts-pc；不能据此说 fonts-pc 曾被 Debian 判为不自由或移除。

此次检索未找到针对 Oldschool PC Font Pack 的诉讼或原厂下架要求的可靠记录。此结论限定于查到的公开资料，不表示可以证明从未发生。

## 恢复完成验证

411 个家族 / 1,433 个变体；恢复的 137 个家族 / 328 个变体与撤下前一致，1,513 个下载文件大小和 SHA-256 全部匹配。六种语言共 822 个恢复字体页面生成成功。正式 Astro 构建及 12 项浏览器测试通过，Astro/Svelte 检查零错误（保留既有 18 条 Svelte 警告）。Galmuri、Chusung、Lyusung 的变体未改动。
