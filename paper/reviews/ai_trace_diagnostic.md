# APMCM论文V2语言与表达诊断

> 本报告依照 `AI痕迹检测提示词_V5.0_执行要点.md` 执行。它只诊断英文论文的准确性、可读性、具体性和表达模式，不判断作者身份，不输出AI生成概率，也不以规避检测为目标。

## 1. 总体评估

论文的英文准确度和技术具体性总体较高：多数结论带有样本数、版本、候选池和证据边界，几乎没有空泛的“significant improvement”式陈述。最明显的问题不是“像不像AI”，而是全文采用了高度一致的防御性写法：反复出现“not a... / does not... / rather than... / no claim...”，并频繁使用 `evidence`, `formal`, `accepted`, `archived` 等项目管理词。这种写法保护了科学边界，但造成摘要、结果和结论重复，削弱主论点。

定向统计仅作为编辑线索，不作为检测阈值：论文源文件中 `evidence` 约26次，`not a` 23次，`rather than` 16次，`therefore` 22次，`This/These`句首或短语合计超过50次。是否修改取决于句子是否提供新信息，而不是词频本身。

语言整改必须在科学P0/P1完成后进行，不能为了风格改变数据、公式、结论或证据状态。

## 2. 十维度诊断

| 维度 | 状态 | 主要观察 | 建议 |
|---|---|---|---|
| 1. 英文词汇 | ISSUE | `evidence-audited`, `formal`, `accepted`, `archived`, `traceable`密集，部分句子更像项目报告而非论文。 | 首次定义后改用具体名词，如“the 104-variable matrix”或“the SDK 1.4.3 run”。 |
| 2. 句式 | ISSUE | 长句常同时承载结果、限制、对照和结论；多处使用分号式并列。 | 按“result—boundary—interpretation”拆句。 |
| 3. 段落 | ISSUE | 许多段落以“This/These/The formal...”开头，以“not physical/quantum...”收尾，节奏机械。 | 合并重复边界，只在最相关章节保留。 |
| 4. 逻辑 | ISSUE | 大部分因果边界良好；第3章“not causal, but it explains why”仍自相矛盾，O-14“reduced hits”也偏因果。 | 改为“is consistent with”或“was associated with”。 |
| 5. 作者推理与表达 | PASS/ISSUE | 104/208/107取舍有真实证据；但O-10为何失真、两档编码为何只能作后验映射没有用最直接的推理展开。 | 说明缺失交互、全局loss和低尾目标冲突；把枚举与映射分开。 |
| 6. 数据表述 | ISSUE | 数字高度可追溯，但代理分保留15--16位，而正文误差多为4--6位；“3/4 hit”可能被误读为成功率。 | 表中按证据精度保留，正文统一合理有效位；任务命中附返回数。 |
| 7. 图表 | ISSUE | Caption准确，唯一图片可追溯；全稿只有一张图，Q1、O-10/O-11趋势缺少视觉表达。 | 页数允许时优先复用已有真实Q1图或一张编码对照图，不新增装饰图。 |
| 8. 结构 | ISSUE | 九章逻辑完整，但第5--9章多次重新解释相同证据边界；第6章标题与groupwise主模型不符。 | 把共同边界集中到第2/8章，章节只保留局部限制；更名第6章。 |
| 9. 引用 | ISSUE | 核心引用位置基本合理；引用较少且reference audit过时，部分来源阅读状态仅摘要/技术节。 | 建立claim-to-source审计，限定摘要级文献的使用范围。 |
| 10. 整体表达 | ISSUE | 可信、克制、具体，但信息密度过高，主贡献被大量限定句包围。 | 先写一句可支持的主结论，再给一条关键限制；其余证据边界移至专门小节。 |

## 3. 具体问题清单

| ID | 位置与短摘录 | 类型 | 严重度 | 原因 | 修改方向（示例仅供第四阶段） |
|---|---|---|---|---|---|
| L-01 | 摘要37--48，连续描述encoding、SPQC、blind、projection、四层误差 | 长句/信息堆叠 | 中 | 一个段落承担四层结论，读者难抓主结果。 | 拆为“mapping result”“hardware observation”“evidence boundary”三句。 |
| L-02 | 第1章49：“Every stage has an independent check.” | 绝对措辞 | 中 | Q1人工签收、冲突计时和probe凭证仍未闭合。 | `Each reported stage has an archived check within the scope stated below.` |
| L-03 | 第3章41：“This association is not causal, but it explains why...” | 逻辑冲突 | 中 | “not causal”与“explains why”语义相抵。 | `This association is consistent with the observed low-tail difficulty.` |
| L-04 | 第4章136，单句塞入fold结果、MAE和screening | 句长 | 轻 | 结果句过密，比较对象不够突出。 | 先报selected model，再单独与direct HGB比较。 |
| L-05 | 第5章125--153三段连续重复proxy/physical/hardware边界 | 冗余 | 中 | 局限正确但重复，掩盖Q2主结论。 | 第一段保留proxy边界，SPQC段只保留小样本/非稳定性。 |
| L-06 | 第6章标题“Joint-State QUBO” | 术语准确性 | 中 | 最终主模型是三张groupwise 104变量矩阵。 | 改为 `Q3: Groupwise QUBO over Joint Candidate States` 或更短标题。 |
| L-07 | 第6章163--164：“integerization reduced optimum-seed hits” | 因果强度 | 中 | 单次随机对照不足以证明因果。 | `The recorded integer runs had fewer optimum-hit seeds...` |
| L-08 | 第7章114--136，Three controls段落 | 结构 | 轻 | 三个控制很重要但只有文字，数字密集。 | 使用一张紧凑LaTeX对照表，减少重复解释。 |
| L-09 | 第7章175：“verify that the archived matrices were executable” | 范围措辞 | 中 | 四个返回任务只能证明这些提交产生了返回，不能证明普遍可执行性。 | `show that these four archived submissions produced platform returns.` |
| L-10 | 第8章88--104成本段 | 信息层次 | 中 | ms、s、创建时差、演化、额度和NA混在两段。 | 按local preparation / SDK solve / SPQC platform分三段或一表。 |
| L-11 | 第8章90：“supersede stale README figures” | 证据措辞 | 严重 | 团队尚未确认README来源；与附录“unresolved conflict”强度不一致。 | `are used provisionally; the README provenance remains unresolved.` |
| L-12 | 第8章96：“latest verified local-SA record” | 修饰词 | 中 | 数值本身可读，但run版本未对齐；“verified”易被理解为已解决冲突。 | `a later archived record reports 178.14 s...` |
| L-13 | 第9章重复摘要中的全部主要数字 | 结构冗余 | 轻 | 结论复述过多，贡献与未来工作被压缩。 | 保留每问一个核心结果，重点总结证据能支持什么。 |
| L-14 | 全文 `V_hat`、`V_hat_23`和化学式排版 | 术语/符号 | 轻 | 综合章节简化符号后，Q1与Q23模型可能混淆。 | 统一符号并在首次出现时定义；表格化学式使用一致格式。 |

## 4. 章节逻辑和重复关系

### 可保留的重复

- 摘要：一句话说明所有winner均为代理分数。
- 第2章：建立SDK--CPU、mapping audit、SPQC三类证据标签。
- 第8章：集中讨论四层误差与不能相加。
- 第9章：用一句总边界结束全文。

### 建议删除或合并的重复

- 第5、6、7章分别重复“not physical feasibility / not quantum advantage”。保留与该章独有证据直接相关的限制即可。
- 第6、7、8章重复说明CPU SDK不是SPQC；第2章已定义，后文可用短标签。
- 第7、8、9章重复列出相同硬件小样本限制；正文保留一次详细说明，结论只给结论。
- `formal`, `accepted`, `archived`不应替代矩阵版本、运行版本和证据路径。

## 5. 引用与作者判断

论文不是因为引用少就必然有“AI痕迹”；真正问题是部分背景引文与本项目实现之间距离较大。例如Ward 2016讨论材料成分描述符，而本项目只用有序A/B/X类别，正文应把它称为背景比较而不是已采用方法。Chen 2024和Ohno 2026的仓库阅读状态不是完整全文，避免写出超出已读范围的具体结论。

作者判断最自然的部分是：拒绝用03 post-freeze结果重新选模、拒绝合并冲突计时、拒绝声称量子优势。应保留这些具体取舍。无需通过口语、设问、故意语法错误或不规则段落来“降低AI痕迹”。

## 6. 修改原则

1. 先修科学P0，再处理结构P1，最后处理语言P2。
2. 每删一条边界句，确认同一限制在摘要/方法边界/讨论中至少保留一处。
3. 不用同义词机械替换高频词；只有当句子没有新增信息或对象不明确时才改。
4. 数字、公式、任务ID、矩阵SHA和实验状态不得因语言润色改变。
5. AI工具使用按官方规则和真实过程披露，不作虚假未使用声明。

## 7. 统一整改清单

### P0

- 先处理oracle-assisted编码、03回顾性预算、代理winner不确定性、映射残差口径、四类冲突和缺失probe凭证。
- 语言层最紧急的是L-11：不能用“supersede”消除仍未解决的证据冲突。

### P1

- 补O-10失真机制、盲池mask、104/107/208对齐比较和最终104映射证据。
- 将SPQC与O-14差异写成描述性观察；更新引用审计和复现清单。
- 调整第6章标题，优化图表与章节分工。

### P2

- 合并重复否定式边界，减少项目管理式抽象词，拆分高密度长句。
- 统一 `V_hat` / `V_hat_23`、化学式、有效位和solver标签。
- 内容冻结后再做一次排版构建；不通过缩字号或边距压缩篇幅。
