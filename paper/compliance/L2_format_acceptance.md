# L2 Official Format Acceptance

**检查日期：** 2026-11-27（Asia/Shanghai）  
**检查范围：** L2 官方格式验收；不涉及论文正文写作、实验、AI 痕迹检测或 16 维度审查  
**分支 / 提交：** `codex/latex-environment-audit` / `15d288a4f10082ebbbbc5d2f792ca46746b4c051`  
**验收对象：** `paper/build/main.pdf`  
**PDF SHA-256：** `aa1807eb5a774b07cdd08cec74afeaf5d45ef146052e738cf7bd850044a0e998`  
**结论：** **L2 格式工程有条件通过；当前文件不是可提交终稿。** 官方模板机制、页面结构、字体、页眉页码、引用机制和编译环境均可供后续写作使用；真实队号、最终文件名、结果占位符和终稿页数仍是发布前硬性阻塞项。

## 1. 验收依据与复用证据

最新版 `APMCM_D_论文写作项目执行书_V1.2.md` 的 L2 要求为：

1. 正文不超过 25 页，附录单独统计且不限页数。
2. 检查 Summary Sheet、目录、正文页码、页眉、字体字号、引用编号和参考文献。
3. 检查正文/图表中的中文、模板示例文字、空标题、占位符和未引用图表。
4. 检查提交文件名是否使用真实队号。
5. 硬性规则必须通过；无法自动确认的项目标为 `MANUAL REVIEW`。

本轮优先复用以下已有证据，没有重新编译或重建 L1：

- `paper/compliance/official_template_acceptance.md`
- `paper/compliance/latex_environment_report.md`
- `paper/compliance/template_manifest.json`
- `paper/compliance/official_rules_checklist.md`
- `paper/compliance/page_count_check.md`
- `paper/compliance/reference_audit.md`
- `paper/compliance/final_pdf_checklist.md`
- 已验收且哈希未变化的 `paper/build/main.pdf`
- 既有九页 PDF 的逐页视觉检查结果

本轮只补做了当前文件的哈希、PDF 元数据/嵌入字体、文本残留和源文件中的定向静态检查；没有进行全仓库扫描。

## 2. 官方模板与编译环境

| 检查项 | 状态 | 证据与说明 |
|---|---|---|
| 官方模板原件保护 | PASS | `official_template/` 中四个核心 TeX 原件哈希与 manifest 一致。 |
| class 工作副本 | PASS | `paper/apmcmthesis.cls` 与官方原件 SHA-256 均为 `22bb5c34ee56760d2cd6af3286083e05084ea5bddf78160d8e7a4ef9b7220f26`。 |
| config 工作副本 | PASS | `paper/apmcmthesis.cfg` 与官方原件 SHA-256 均为 `5977897c04bcdcf0e34dbd7958ddbf636cd9d2413f2250a126e8b0bbd5fc882a`。 |
| 官方页面和字号配置 | PASS | 未修改的 class 使用 `\LoadClass[a4paper,12pt]{article}`，符合官方通常 11 或 12 pt 的要求。 |
| 必要编译环境 | PASS（复用） | TeX Live 2026、pdfTeX 1.40.29、Latexmk 4.89 已通过 L1 环境验收；当前 PDF 由 pdfTeX 1.40.29 生成。 |
| 构建结果 | PASS（复用） | 现有 PDF 已无 Fatal Error；其哈希与既有完整视觉验收对象一致，因此本轮未重复编译。 |

官方原始 `main.tex` 缺少 ZIP 中未提供的示例图片 `cat` 和 `gongzhonghao`，这一点已在官方模板验收报告中定位为示例资源缺失，并非 class/config、字体或宏包故障。正式工程未引用这些资源，也未修改官方 class/config。

## 3. PDF 页面结构与版式验收

当前 PDF 共 9 个 A4 物理页，页面尺寸为 `595.276 × 841.890 pt`。

| 项目 | 状态 | 当前证据 | 后续要求 |
|---|---|---|---|
| A4 页面 | PASS | 9 页均由同一 A4 页面配置生成；PDF 元数据为 A4。 | 保持官方 class。 |
| Summary Sheet | PASS | 位于物理第 1 页，官方摘要页机制正常。 | 写作阶段替换 L1 工程摘要，但不改变页面机制。 |
| 目录 | PASS | 从物理第 2 页开始，当前因九章骨架延续至物理第 3 页。 | 官方要求是目录从第二页开始，并未要求目录只能有一页；完整初稿后应控制目录长度。 |
| 正文起始 | PASS | 正文位于目录之后，从物理第 4 页开始。 | 不在目录前插入其他页面。 |
| 正文页码 | PASS | 正文重新从 `Page 1 of 6` 编号，连续至 `Page 6 of 6`。 | 完整初稿后重新核对总页数。 |
| 页眉内容 | FORMAT PASS / RELEASE BLOCKER | 页眉仅含 `Team # TEAM-NUMBER-PLACEHOLDER` 和 `Page n of N`，未出现姓名或学校。 | 必须用核实后的真实队号替换占位符；当前长占位符在 Summary Sheet 换行。 |
| 正文页数 | CURRENT PASS / MANUAL REVIEW | 当前结构稿正文编号共 6 页，低于 25 页。 | 完整正文、参考文献和图表冻结后重新统计；当前数字不能作为终稿页数证明。 |
| 附录页数 | MANUAL REVIEW | 当前附录骨架与参考文献同处最后一个正文编号页，尚不能形成有意义的终稿独立统计。 | 完整初稿后记录正文终止页和附录起始页，按官方“正文不超过 25 页、附录不限页”复核。 |
| 数学公式 | PASS（复用） | QUBO 等式和数学符号已在既有逐页视觉检查中正常显示。 | 写作后抽查新增公式。 |
| 图表版式 | PASS（机制） | 表 1 和图 1 均正常显示、带标题和标签。 | 图 1 是明确的 L1 占位图，发布前必须替换或删除。 |

## 4. 字体、语言、引用与参考文献

| 项目 | 状态 | 结果 |
|---|---|---|
| 英文字体 | PASS | PDF 嵌入 `TeXGyreTermesX-Regular`、`TeXGyreTermesX-Bold`；官方 PDFLaTeX 分支的 `newtxtext` 正常工作。 |
| 数学字体 | PASS | PDF 嵌入 `NewTXMI`、`txsys`、`txmiaX`、`txexs`；`newtxmath` 正常工作。 |
| 字体字号 | PASS（模板级） | 官方 class 为 12 pt，现有页面可读性已通过视觉检查。新增内容仍须继承模板，不应局部缩小以挤压页数。 |
| 英文正文 | PASS（当前骨架） | 对当前 PDF 提取文本及 `paper/main.tex`、章节、附录和参考文献源文件进行定向检查，未发现汉字。 |
| 引用编号 | PASS（机制） | 正文引用以方括号编号 `[1]` 显示。 |
| 参考文献 | PASS（机制） / MANUAL REVIEW（终稿） | 当前参考文献列表可生成且与正文引用相连。完整初稿后仍需逐条核对文献类型、页码、访问日期和引用顺序。 |

本轮没有执行文献真实性复核；该工作不属于当前 L2 格式范围。

## 5. 残留项与静态检查

定向检查范围仅包括 `paper/main.tex`、`paper/sections/`、`paper/appendix/appendix.tex`、`paper/references.bib`、现有 PDF 和现有构建日志。

| 检查项 | 状态 | 结果 |
|---|---|---|
| 中文正文/图表文字 | PASS | 当前源文件和 PDF 提取文本均无汉字。 |
| 官方模板示例文字/图片引用 | PASS | 未发现 `cat`、`gongzhonghao`、`Keywords1` 等官方示例残留。 |
| 空标题 | PASS | 未发现空的 `section`、`subsection` 或 `subsubsection`。 |
| 未引用图表 | PASS（当前骨架） | 表 1 与图 1 均在正文中通过标签引用。 |
| 队号占位符 | OPEN — HARD BLOCKER | `TEAM-NUMBER-PLACEHOLDER` 仍位于 Summary Sheet 和全部页眉。 |
| 结果占位符 | OPEN — EXPECTED | Q2、Q3、硬件精度和误差审计位置仍含与 O-08 至 O-15 对应的 `[TO BE COMPLETED]`。这符合 L1 真实性要求，但不得进入最终提交 PDF。 |
| L1 占位图 | OPEN — EXPECTED | 图 1 明确声明不代表实验结果；发布前必须由有证据的图替换，或连同引用一起删除。 |
| L1 工程摘要文字 | OPEN — EXPECTED | Summary Sheet 当前说明文档是 L1 scaffold，并非竞赛论文最终摘要；正文写作阶段必须基于真实结果重写。 |
| 编译错误 | PASS | 现有日志没有 Fatal Error、LaTeX Error、未定义引用/引文或 Overfull box。 |
| `headheight` 警告 | NON-BLOCKING | 官方 class 的 `fancyhdr` 报告 `\headheight=12pt` 略小；既有九页视觉检查未发现页眉裁切或重叠。禁止为消除警告修改官方 class，后续只需在内容变化后观察页眉。 |
| Underfull box | NON-BLOCKING | 与长占位队号相关；替换真实队号后自然复核，不为此修改版式。 |

## 6. 文件命名验收

官方提交规范要求论文 PDF 命名为 `#***.pdf`，其中 `#` 是题号、`***` 是队号；D 题最终文件应采用 `D<真实队号>.pdf` 的形式。当前构建产物为 `paper/build/main.pdf`，且真实队号尚未提供。

**状态：OPEN — HARD RELEASE BLOCKER。**

这不影响继续在统一构建路径中写作，但在最终发布前必须同时确认：

1. Summary Sheet 中的队号；
2. 所有正文页眉中的队号；
3. 最终论文 PDF 文件名；
4. Control Sheet 和支持材料文件名（若提交）；
5. 上述位置使用完全相同、经负责人核实的真实队号。

本轮没有猜测队号，也没有重命名文件。

## 7. L2 验收结论

### 7.1 已通过、可直接支撑后续写作的部分

- 官方 `apmcmthesis` class/config 完整且未被修改。
- PDFLaTeX 环境和构建入口可用，无需修复或切换引擎。
- A4、12 pt、Summary Sheet、第二页目录、正文起始、页眉页码机制均正确。
- 官方 PDFLaTeX 字体与数学字体正常嵌入。
- 英文、公式、图表、编号引用和参考文献机制正常。
- 当前正文没有中文、官方示例残留、空标题或未引用图表。

### 7.2 当前问题

1. **真实队号未填，最终文件名不合规。** 这是当前唯一需要用户信息才能关闭的硬性发布阻塞项。
2. **当前仍是 L1 骨架。** 工程摘要、任务占位符和占位图必须在相应真实证据完成后替换，不能作为最终论文内容。
3. **终稿页数尚不可验收。** 当前 6 页正文仅证明格式机制正常；正文不超过 25 页和附录独立统计必须在完整初稿冻结后重查。
4. **目录当前占两页。** 它仍满足“第二页开始目录”，不是当前错误；完整初稿后应结合章节层级和页数再检查可读性。
5. **官方 class 的 `headheight` 警告继续保留。** 现有页面无视觉缺陷，不应修改官方 class/config 来消警告。

### 7.3 判定

- **L2 格式工程：CONDITIONAL PASS。** 可以在现有 L1 工程上进入后续证据映射和写作准备，无需重建模板或调整编译环境。
- **最终提交合规：NOT READY。** 真实队号/文件名、真实正文替换、最终页数和终稿参考文献仍未完成。
- **官方模板原件：未修改。**
- **Git：未提交、未推送、未合并。**

## 8. 下一步建议

下一批最需要执行的一项任务是：**建立 L3 证据索引，将每个拟写主张绑定到现有数据、脚本、图表和任务 ID；暂不撰写正文。**

在进入最终发布检查前，负责人还需提供并确认真实队号。终稿形成后再执行一次单次、集中式格式复核，重点关闭文件名、占位符、正文 25 页限制、附录起始页、引用格式和新增图表引用；无需在每个写作小批次反复编译。
