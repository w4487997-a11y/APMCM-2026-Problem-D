# 论文证据索引（L3）

**建立日期：** 2026-11-27（Asia/Shanghai）  
**适用工程：** 2026 APMCM Problem D 论文  
**依据：** `paper/reviews/sample_paper_structure_mapping.md`、最新版论文执行书、现有实验报告/数据/模型/代码、`handoff/Q123_v1/` 整合交付包  
**用途：** 把拟写主张绑定到可追溯证据；本文件不是实验结果，也不把计划任务视为已完成。

## 1. 状态定义

索引只使用以下四种证据状态：

| 状态 | 定义 | 写作规则 |
|---|---|---|
| **已完成** | 仓库内已有相互对应的报告、数表/模型/代码或验收记录，足以支持限定范围内的主张。 | 可写入方法或结果，但仍需保留证据路径和适用边界。 |
| **待复核** | 已有产物或总结，但仍需人工签收、独立核对、与正式模型对齐，或底层原始证据未完整进入本仓库。 | 只能写成初步/前置证据，不得写成最终验收结论。 |
| **待实验** | 任务、输入或原型已定义，但正式实验和验收产物尚未完成。 | 只写方法计划或任务 ID，不填写数值结果。 |
| **暂无证据** | 当前仓库没有支持该主张的任务回执、原始数据、报告或复算记录。 | 不得在正文、摘要或结论中提出该主张。 |

O-08～O-15 按最新整合交付包和历史实验归档分别登记，不再统一视为待完成。尤其要区分 **CPU 上的 Kaiwu SDK 1.4.3 本地求解**、**历史17/30变量SPQC短名单任务** 与 **最终104变量SPQC任务**：前两者已有不同层级的证据，后者仍无任务回执。

## 2. 章节证据覆盖总览

| 论文章节 | 需要的数据、公式、结果与结论 | 当前主要证据 | 状态 | 当前可写边界 |
|---|---|---|---|---|
| 01 Introduction | 官方问题背景、三问关系、有限预算筛选价值、贡献边界 | `2026 APMCM Problem D/2026 APMCM Problem D.pdf`；`paper/reviews/sample_paper_structure_mapping.md`；`APMCM_D_论文写作项目执行书_V1.2.md` | 已完成 | 可写问题背景与证据链设计；贡献必须区分已完成的Q1/Q2/Q3证据与仍待补的107位、盲池、最终104变量真机及成本项。 |
| 02 Problem Formulation | 五项违背度公式、严格达标口径、有序 A/B、Q2/Q3 决策变量、独热约束 | `DATA_CONTRACT.md`；`audit/phase1/REPORT.md`；`q1/violation.py`；`handoff/Q123_v1/README.md`；整合包 `paper/PAPER_EVIDENCE.md` | 已完成 | V 公式可写；正式采用每个 X 组一张 104 位 QUBO，并以原尺度分数组间比较。须说明这与执行书早期 208 位联合编码计划的差异。 |
| 03 Data and Audit | 02/03/04/07/08/11/12 行数、集合关系、哈希、标签复算、舍入误差、盲测边界 | `DATA_CONTRACT.md`；`audit/precheck_index.md`；`audit/phase1/REPORT.md`；`audit/phase1/results.json`；`audit/label_checks.csv` | 已完成 | 可写完整数据审计；人工独立签收另列为待复核。 |
| 04 Q1 Surrogate | 模型结构、五折开发、03 选模、低尾/Top-K、稳定性、有限预算价值、04 预测边界 | `experiments/q1_ablation_v1/`；`experiments/q1_v12/`；`experiments/q1_random_search_03/`；`handoff/v1/`；`handoff/v1_2/` | 已完成（技术）/ 待复核（人工签收） | Q1 方法和 02/03 结果可正式写；04 只能报告代理预测，不能报告未知真值误差或命中率。 |
| 05 Q2 Fixed-X QUBO | `q23_final` 的 07 分数、104 变量、矩阵/映射/offset、枚举基准、本地 SDK 求解结果 | `handoff/Q123_v1/README.md`；`handoff/Q123_v1/paper/q23_experiment_table.csv`；`handoff/Q123_v1/evidence/sdk_verification.json`；整合 ZIP 内正式运行目录 | 已完成 | 可写固定 NO2 的 Q2 正式整数模型和 CPU 本地 SDK 结果；不得称为真实硬件结果。 |
| 06 Q3 Joint QUBO | `q23_final` 的 08 分数、三张 104 位分组 QUBO、208 位浮点对照、映射/offset、枚举基准、本地 SDK 求解 | `handoff/Q123_v1/`；`handoff/Q2Q3_论文与图表.zip`；`handoff/q23_fix/results/stage1_sdk_ising.json` | 已完成（分组主线与208位浮点对照）/ 未完成（107 位对照） | 主结果仍为三组独立求解和原尺度组间比较；208 位模型只作为精确浮点/直接量化对照，不能替代104位主模型。 |
| 07 Hardware and Precision | QUBO→Ising、offset 修正、8 位适配、直接量化/惩罚/预算对照、Kaiwu 本地与历史短名单真机 | `handoff/Q123_v1/evidence/sdk_verification.json`；`handoff/q23_fix/`；`handoff/Q2Q3_论文与图表.zip`；`Kaiwu_Precheck_Phase1_Summary.md` | 已完成（CPU 本地与精度对照）/ 部分完成（真机） | 正式矩阵为 max\|h\|=102、max\|J\|=1；另有17/30变量SPQC-550历史任务。最终104变量矩阵无真机回执，不能声称最终模型硬件验收或量子优势。 |
| 08 Results and Discussion | Q1/Q2/Q3统一结果、有限预算价值、稳定性、采样质量、四层误差和成本边界 | Q1 报告；`handoff/Q123_v1/paper/q23_experiment_table.csv`；`handoff/q23_fix/results/`；历史真机ZIP | 已完成（现有证据范围）/ 部分完成（O-15） | 已形成四层分列分析、负例/回归和本地/历史短名单成本表述；107位、盲池、最终104变量真机及完整实扣账单仍为NA。 |
| 09 Conclusion | 分别回答三问、适用范围、候选筛选建议、局限 | Q1 完整证据；Q2/Q3 整合交付包 | 待复核 | 可形成基于冻结代理与 CPU 本地 SDK 的三问结论；最终结论必须明确未完成的真机、盲池和成本边界。 |

## 3. 数据、公式与审计证据

| 证据 ID | 对应章节 | 内容/拟支持主张 | 仓库相对路径 | 实验/任务 ID | 状态 | 限制或待办 |
|---|---|---|---|---|---|---|
| DATA-01 | 02, 03 | 官方五项平方铰链违背度、严格条件和数据池用途 | `2026 APMCM Problem D/2026 APMCM Problem D.pdf`；`2026 APMCM Problem D/date/README_数据集说明.md` | O-05 | 已完成 | 官方 PDF 与 README 的带隙边界文字口径需按数据契约分别表述。 |
| DATA-02 | 02, 03 | 统一 V 公式、A/B 有序、A=B 合法、输入白名单和各池行数 | `DATA_CONTRACT.md` | O-04, O-05 | 已完成 | 04 真值不可见；`pool` 必须按字符串保留前导零。 |
| DATA-03 | 03 | 9 项官方哈希、8 份 CSV 结构、集合关系和 18,928 完整组合 | `audit/init_results.json`；`audit/data_audit.json`；`audit/precheck_index.md` | I001, I002, O-04 | 已完成 | 人工复核人尚未登记。 |
| DATA-04 | 02, 03 | 15,225 条公开标签复算、舍入区间、V=0/严格达标口径 | `audit/q1_label_audit.json`；`audit/label_checks.csv`；`audit/phase1/REPORT.md` | P101, Q501, O-05 | 已完成 | 19 条 V=0 和 15 条严格达标为官方汇总，不能推断其盲测身份。 |
| DATA-05 | 03, 04 | 按有序 `(A,B)` 的分组规则、五折清单及各折低尾统计 | `audit/phase1/folds_02.csv`；`audit/phase1/results.json` | P101 | 已完成 | 五折用于 02 开发；03 是正式选择面板，不是独立盲测。 |
| DATA-06 | 03 | 低尾 ECDF、带隙分布、有序对划分图及底层数表 | `audit/phase1/figures/`；`audit/phase1/stats_by_x.csv` | P101, O-16 | 已完成 | 论文采用时统一英文标注和图号。 |
| FORM-01 | 02 | V 公式实现与边界测试 | `q1/violation.py`；`tests/test_q1_data.py`；`tests/test_phase1_artifacts.py` | O-05 | 已完成 | 正文公式应与实现保持同一阈值和单位。 |
| FORM-02 | 05, 06 | 正式 Q2/Q3 分组 104 位独热 QUBO、整数代价、罚值、offset 与组间比较 | `handoff/Q123_v1/README.md`；整合 ZIP 内 `paper/PAPER_EVIDENCE.md`、四张正式矩阵及运行摘要 | O-08, O-09 | 已完成 | 每个 X 组分别使用 A/B 各 52 位；代价按 0.02 截断和归一取整至 {0,4}，独热罚值为 2、offset=4。执行书原 208 位计划未作为本次实际主线。 |

## 4. Q1 代理模型证据

### 4.1 实验、模型与结果

| 证据 ID | 对应章节 | 内容/拟支持主张 | 仓库相对路径 | 实验/任务 ID | 状态 | 限制或待办 |
|---|---|---|---|---|---|---|
| Q1-01 | 03, 04 | 中位数、Ridge、随机森林的组成基线及五折结果 | `experiments/baseline_v1/REPORT.md`；`experiments/baseline_v1/results.json`；`experiments/baseline_v1/fold_metrics.csv` | B101, Q1-02 | 已完成 | 基线只用于方法对照，不替代最终模型。 |
| Q1-02 | 04 | 12 个配置的五折消融、直接/间接模型、带隙处理及低尾评价 | `experiments/q1_ablation_v1/REPORT.md`；`experiments/q1_ablation_v1/model_comparison.csv`；`experiments/q1_ablation_v1/paired_ablation.csv` | Q301, Q1-03～Q1-06 | 已完成 | 02 五折用于开发；须与 03 正式选择结果分开报告。 |
| Q1-03 | 04 | 冻结候选、选模规则和最终 `hgb_gap_mix` | `experiments/q1_ablation_v1/frozen_shortlist.json`；`handoff/v1/validation_metrics.csv`；`experiments/q1_v12/model_selection.md` | Q401 | 已完成 | 03 已参与选择，不能把其后新增对照当作独立择优。 |
| Q1-04 | 04, 08 | 03 上 MAE、RMSE、Spearman、低尾 MAE、Top-K 和物性误差 | `experiments/q1_ablation_v1/REPORT.md`；`handoff/v1/validation_predictions.csv`；`handoff/v1/validation_physics.csv` | Q401 | 已完成 | 03 没有 V=0 样本，结果不证明严格可行候选召回。 |
| Q1-05 | 04, 08 | 冻结后物性/带隙补证、阈值误差、五罚项分解和稳定性 | `experiments/q1_v12/REPORT.md`；`experiments/q1_v12/model_comparison.csv`；`experiments/q1_v12/stability.csv`；`experiments/q1_v12/stability_summary.csv` | Q501 | 已完成 | 属冻结后补证，不改变冻结模型和已发布分数。 |
| Q1-06 | 04, 08 | 有限预算下代理筛选相对随机抽查的价值 | `experiments/q1_random_search_03/REPORT.md`；`experiments/q1_random_search_03/comparison.csv` | Q502 | 已完成 | 是 03 上的回顾性预算对照；不能外推为未知材料的命中概率。 |
| Q1-07 | 04 | `q1_final` 模型文件、04 全量预测和模型/数据哈希 | `handoff/v1/models/q1_final.joblib`；`handoff/v1_2/q1_holdout_predictions.csv`；`handoff/v1_2/manifest.json` | Q401, Q501, O-07 | 已完成 | 04 无真值，只能给出代理排序和候选清单。 |
| Q1-08 | 04, 05, 06 | `q23_final` 模型文件及 07/08/11/12 原始尺度评分 | `handoff/v1/models/q23_final.joblib`；`handoff/v1_2/q2_pool_predictions.csv`；`handoff/v1_2/q3_pool_predictions.csv`；`handoff/v1_2/q2_blind_predictions.csv`；`handoff/v1_2/q3_blind_predictions.csv` | Q401, Q501, O-07 | 已完成 | 这是 Q2/Q3 的评分输入，不是 QUBO 求解结果。 |
| Q1-09 | 04, 08 | Q1 图表及底层数表 | `experiments/q1_ablation_v1/figures/`；`experiments/q1_v12/figures/`；相邻 CSV/JSON | Q301, Q501, O-16 | 已完成 | 排版前只需统一英文标题、图例和论文变量记号。 |
| Q1-10 | 04, Appendix | 公式、训练、推理、指标和交付代码 | `q1/violation.py`；`q1/metrics.py`；`q1/surrogates.py`；`q1/experiments.py`；`q1/delivery.py`；`q1/v12_handoff.py` | Q301, Q401, Q501 | 已完成 | 源码快照 commit 记录于 `handoff/v1_2/manifest.json`。 |
| Q1-11 | 04, Appendix | 本地机器验收、预测复现和交接签收 | `handoff/v1/ACCEPTANCE.md`；`handoff/v1_2/ACCEPTANCE.md`；`audit/final_v1.json`；`audit/v12_acceptance.json` | Q401, Q501, O-06 | 待复核 | 机器审计 PASS；队员独立签收、QUBO 负责人签收和 04 平台字段仍待登记。 |

### 4.2 Q1 当前可支持的核心结论

以下结论有仓库证据，可在保持限制条件的前提下写入论文：

1. 仅使用组成特征 A/B/X 的冻结 `hgb_gap_mix` 在 03 上取得 MAE 2.4715、RMSE 4.5827、Spearman 0.9383，Top-25/Top-50 命中数为 8/20。
2. 五折和 03 结果显示，整体误差与低尾筛选质量可能给出不同的方法排序，因此不能只用总体 MAE 选择筛选模型。
3. 02/03 中没有 V=0 或严格达标样本，04 真值不可见；Q1 只能主张代理排序和低违背度富集能力，不能主张已发现真实达标材料。
4. 在 03 的有限预算回放中，代理筛选优于同池随机抽查的期望；该结论限定于现有验证池和给定预算。
5. `q1_final` 与 `q23_final` 的训练角色、模型文件、预测表和哈希已经分离，Q1 验证结果不能直接冒充 Q2/Q3 的最终优化结果。

## 5. Q2/Q3 数学、矩阵与求解证据

| 证据 ID | 对应章节 | 内容/拟支持主张 | 仓库相对路径 | 实验/任务 ID | 状态 | 限制或待办 |
|---|---|---|---|---|---|---|
| Q23-01 | 05, 06 | Q2/Q3 正式评分输入及池级最小值、近优间隔、行数和哈希 | `handoff/v1_2/manifest.json`；四份按池预测 CSV；整合 ZIP 内冻结推理复核 | Q401, Q501, O-07 | 已完成 | 支持代价输入和候选域描述；求解质量另由 Q23-04～Q23-06 支持。 |
| Q23-02 | 05, 06 | Q2/Q3 独热编码的矩阵生成原型 | `deliverable/code/build_matrices.py`；`deliverable/results/matrix_build.json`；`deliverable/matrices/qubo_q2.npz`；`deliverable/matrices/qubo_q3.npz` | H001, D-00 | 待复核 | 产物使用 `Ridge(alpha=1.0)` 前置代理，不是 `q23_final`；不得作为正式矩阵或正式最优材料证据。 |
| Q23-03 | 05, 06 | 小规模全状态枚举、公式/矩阵能量一致性、合法候选逐条核对原型 | `deliverable/code/verify_qubo.py`；`deliverable/results/qubo_verify.json` | H001, D-00 | 待复核 | 可借鉴验收方法；正式矩阵仍需重新执行索引、offset、解码和独立能量审计。 |
| Q23-04 | 05, 06 | 四张正式 104 位整数矩阵、独热约束、offset、映射与枚举 oracle | `handoff/Q123_v1/Q123_v1_integrated.zip` 内 `q23/runs/sdk_v1_frozen_30x10/matrices/`、运行 summary/verification；`handoff/Q123_v1/README.md` | O-08, O-09 | 已完成 | Q3 采用 O3/NO2/FO2 三张分组矩阵，不是早期计划的一张 208 位矩阵。 |
| Q23-05 | 05, 06, 07, 08 | Kaiwu SDK 1.4.3 CPU 本地 8 位适配、四组各 300 条样本、解码与能量复算 | `handoff/Q123_v1/evidence/sdk_verification.json`；`handoff/Q123_v1/paper/q23_experiment_table.csv`；整合 ZIP 内原始 samples/summary | O-11, O-12 | 已完成 | 仅为 CPU 本地 SDK 求解；不得写成 SPQC 真机执行或量子优势。 |
| Q23-06 | 05, 06, 08 | Q2 返回 Y–Ti–NO2，Q3 组间最优为 Na–Nb–O3；均与合法枚举最优一致 | 同 Q23-05 | O-09, O-12 | 已完成 | 结论限定于冻结代理目标和量化模型；不是未知物理真值。 |
| Q2-01 | 05 | 07 全池 2,704 条 `q23_final` 分数及正式 104 变量矩阵 | `handoff/v1_2/q2_pool_predictions.csv`；`handoff/Q123_v1/Q123_v1_integrated.zip` | O-07, O-08 | 已完成 | 固定 X=NO2；正式结果采用分组整数模型。 |
| Q2-02 | 05 | 11 盲池 529 条 `q23_final` 分数 | `handoff/v1_2/q2_blind_predictions.csv` | O-07, O-14 | 已完成（输入） | 尚无盲池专属矩阵和独立求解。 |
| Q3-01 | 06 | 08 全池 8,112 条 `q23_final` 分数及 O3/NO2/FO2 三张 104 位矩阵 | `handoff/v1_2/q3_pool_predictions.csv`；`handoff/Q123_v1/Q123_v1_integrated.zip` | O-07, O-08 | 已完成 | 实际路线为按 X 分组建模后用原尺度分数比较，不是单张 208 位矩阵。 |
| Q3-02 | 06 | 12 盲池 1,587 条 `q23_final` 分数 | `handoff/v1_2/q3_blind_predictions.csv` | O-07, O-14 | 已完成（输入） | 尚无盲池专属矩阵和独立求解。 |
| Q3-03 | 06, 08 | 107 变量二阶投影对照 | 当前无代码、拟合或对照产物；规范见执行书 §1.5 | O-10 | 未完成（可选） | 若继续，应拟合、推导新罚值界并与104位分组主线和208位浮点对照在同一边界比较；不阻塞初稿。 |

## 6. O-08～O-15 任务证据矩阵

| 任务 ID | 对应章节 | 任务状态 | 当前证据状态 | 已有输入/前置证据 | 完成后必须登记的证据 |
|---|---|---|---|---|---|
| **O-08** | 05, 06 | 已完成 | 已完成 | `handoff/Q123_v1/Q123_v1_integrated.zip` 内四张正式 104 位矩阵、运行快照、哈希与生成/复现入口 | 论文中说明 Q3 从早期 208 位计划调整为三张 104 位分组模型及其理由。 |
| **O-09** | 05, 06 | 已完成 | 已完成 | 整合包内枚举、映射、解码、量化能量逐样本复算；`handoff/Q123_v1/evidence/sdk_verification.json` | 写作时保持 offset、整数能量与原尺度 `V_hat` 的层次分离。 |
| **O-10** | 06, 08 | 未完成（可选） | 未完成 | 只有执行书中的 107 变量方案；未发现代码、实际拟合或对照结果 | 若队员另有未同步成果应补交；否则不阻塞初稿，未来补投影拟合、罚值界和同边界指标。 |
| **O-11** | 07, 08 | 已完成（当前路线） | 已完成 | 正式104位矩阵 max\|h\|=102、max\|J\|=1、最低合法/非法差2；208位/104位直接8位量化、cap=0.4/λ=1.02、K/λ/预算扫描及哈希见历史ZIP与`q23_fix` | 已覆盖当前主模型的精度适配和主要对照；不代表所有位宽、嵌入或服务端变换均已测试。 |
| **O-12** | 07, 08 | 已完成 | 已完成 | Kaiwu SDK 1.4.3 CPU 本地运行，30 个种子、每种子最多 10 条、四组各 300 条原始样本和独立复算 | 明确标注 CPU 本地 SDK；不得替代 O-13 的真机证据。 |
| **O-13** | 07, 08 | 部分完成 | 历史短名单已完成 / 最终104变量未完成 | `q2_int_01`：SPQC-550、17变量；`q3_int_01`：SPQC-550、30变量；归档日志在历史ZIP。后续全尺寸网页预览为NOT_SUBMITTED | 若要验收最终模型，仍需104变量矩阵任务ID、矩阵哈希、原始返回和资源记录；历史短名单不得冒充最终矩阵。 |
| **O-14** | 05, 06, Appendix | 未完成（可选） | 未完成 | 11/12 的 `q23_final` 评分输入已完成，但无专属矩阵和独立求解 | 若纳入最终结论，补盲池专属矩阵、缩放参数、独立求解和复算；不得由全池结果事后过滤替代。当前不阻塞初稿。 |
| **O-15** | 07, 08 | 部分完成 | 部分完成 | 第8章已分列四层误差；本地SDK/SA时间、合法率、命中率及历史短名单任务时间/额度已登记；负例与回归测试已补 | 仍缺最终104变量真机耗时、完整阶段拆分、货币或资源实扣凭证及可比端到端成本；缺项为NA。 |

## 7. Kaiwu、硬件精度和成本证据

| 证据 ID | 对应章节 | 内容/拟支持主张 | 仓库相对路径 | 实验/任务 ID | 状态 | 限制或待办 |
|---|---|---|---|---|---|---|
| HW-01 | 07 | Kaiwu 1.4.3 环境、人工小模型、QUBO→Ising 约定和本地链路前置总结 | `Kaiwu_Precheck_Phase1_Summary.md` | H002, D-01 | 待复核 | 原始 SDK 证据包未进入本仓库；只能作为前置总结引用。 |
| HW-02 | 07, 08 | 人工 104/208 变量模型的直接 int8 量化排序/可行性失败风险 | `Kaiwu_Precheck_Phase1_Summary.md` §6–7 | H002, D-01 | 待复核 | 使用人工代价，不是正式 `q23_final` 矩阵；可支持风险动机，不能支持正式模型结论。 |
| HW-03 | 07 | 网页矩阵校验、SPQC-550 配置预览和资源可见性 | `Kaiwu_Precheck_Phase1_Summary.md` §8 | H002, O-13 | 待复核 | 未最终提交，没有任务回执、返回或实际扣减记录。 |
| HW-04 | 07, 08 | 正式矩阵 8 位适配、Kaiwu SDK CPU 本地求解、解码与能量复算 | `handoff/Q123_v1/evidence/sdk_verification.json`；`handoff/Q123_v1/paper/q23_experiment_table.csv`；整合 ZIP 内运行目录 | O-11, O-12 | 已完成 | 本地 SDK 结果不是 SPQC 真机结果。 |
| HW-05 | 07, 08, Appendix | 历史 SPQC-550 短名单求解 | `handoff/Q2Q3_论文与图表.zip` 内 `q2_int_01.log`、`q3_int_01.log`、解码脚本与矩阵 | O-13 | 已完成（历史短名单） | Q2为17变量、Q3为30变量；不是最终104变量模型。Q3只支持O3组结论，不支持唯一A/B。 |
| HW-06 | 07, 08 | 四层误差与成本边界 | 第8章四层误差表；`q23_experiment_table.csv`；历史ZIP真机时间/额度 | O-15 | 部分完成 | 本地与历史短名单数据已登记；最终矩阵硬件、实扣账单和可比端到端成本为NA。 |
| HW-07 | 06, 07 | 208变量联合浮点对照、offset修正、直接8位失败 | `handoff/q23_fix/results/stage1_sdk_ising.json`；`stage2_quant_partition.json` | O-09, O-11 | 已完成（对照） | 合法态能量精确，但直接8位量化不保最优/可行性；不作为最终主模型。 |

## 8. 结果、图表与结论的证据规则

### 8.1 当前可进入论文的结果

- 02/03 数据审计、标签复算、低尾分布和数据划分事实。
- Q1 的冻结模型、五折开发、03 正式选择结果、冻结后补证、稳定性和随机预算对照。
- 04、07、08、11、12 的代理评分文件、模型版本、行数、哈希和候选排序；其中 04/盲池不得附加未知真值结论。
- Q2/Q3 的分组 104 位独热公式、正式矩阵、枚举 oracle、CPU 本地 SDK 样本质量及返回候选；须明确冻结代理目标和非真机边界。
- D-01 暴露的量化风险可作为研究动机或局限，必须标注为人工前置实验和总结级证据。

### 8.2 当前禁止写成结果的内容

- 将 `deliverable/matrices/qubo_q2.npz` 或 `qubo_q3.npz` 称为 `q23_final` 正式矩阵。
- 将前置 Ridge 矩阵中的 La/Ti 等候选称为最终 Q2/Q3 最优解。
- 将 07/08 的最小 `V_hat` 直接称为真实物理最优或 SPQC 真机求解结果；可在限定口径下称为 CPU 本地 Kaiwu SDK 返回结果。
- 将 11/12 从全池筛出的候选称为独立盲池优化结果。
- 报告 107 变量投影的拟合、量化或求解数字。
- 把已完成的 8 位适配和 Kaiwu CPU 本地闭环等同于真实 SPQC 硬件验收。
- 合并代理误差、映射误差、量化误差和采样误差为一个未经定义的总误差。
- 声称量子优势、硬件全局基态或真实成本已经得到验证。

### 8.3 图表证据要求

| 拟用图表 | 当前底层证据 | 状态 | 写作前动作 |
|---|---|---|---|
| 数据低尾/带隙分布 | `audit/phase1/figures/` + `results.json`/`stats_by_x.csv` | 已完成 | 统一英文标注，不改变数值口径。 |
| Q1 模型/消融对比 | `experiments/q1_ablation_v1/figures/` + 对应 CSV | 已完成 | 区分五折开发与 03 正式选择。 |
| 五罚项、物性和 PR 图 | `experiments/q1_v12/figures/` + 对应 CSV/JSON | 已完成 | 标注为冻结后补证。 |
| 有限预算筛选价值 | `experiments/q1_random_search_03/comparison.csv` | 已完成 | 可据数表生成英文图；不得扩展到未知盲测命中率。 |
| Q2/Q3 矩阵、能量和求解图 | `handoff/Q123_v1/paper/q23_experiment_table.csv` + `q23_run_comparison.png/.svg` + 整合包原始样本 | 已完成 | 图中 attempt 的 SDK 种子与本地 SA 链组口径必须分别说明。 |
| 精度、误差和成本图 | 已有 8 位适配、本地时间和样本统计；无统一 `error_attribution`/真机 `resource_cost` | 待复核 | 可写现有本地证据；完整成本与真机缺项等待 O-15/O-13。 |

## 9. 写作就绪度与下一步

| 优先级 | 章节 | 就绪度 | 原因 |
|---|---|---|---|
| 1 | **04 Q1 Surrogate Modeling and Low-Tail Screening** | 高 | 方法、模型、数表、图、代码、哈希、稳定性和局限均已形成完整链条。 |
| 2 | 03 Data and Audit | 高 | 数据事实和审计证据完整，可为 Q1/Q2/Q3 提供统一口径。 |
| 3 | 02 Problem Formulation | 高 | V 公式与正式分组 QUBO 均有证据；需解释实际 104 位分组路线与早期 208 位计划的差异。 |
| 4 | 01 Introduction | 中 | 可写背景与问题链，但最终贡献列表应等 Q2/Q3 完成后冻结。 |
| 5 | 05–06 Q2/Q3 | 中高 | 正式矩阵、枚举和 CPU 本地 SDK 结果完整；107 位对照与盲池独立求解未完成。 |
| 6 | 07–08 Hardware/Results | 高（现有证据范围） | 8位适配、精度对照、本地样本质量、历史短名单真机和四层误差已写入；最终104变量真机和完整实扣成本明确为NA。 |
| 7 | 09 Conclusion / Abstract | 高 | 可据已冻结三问结果定稿，并保留107位、盲池、最终真机和成本限制。 |

若下一阶段只开始一个章节，优先选择 **第 4 章 Q1 Surrogate Modeling and Low-Tail Screening**。写作时应直接引用本索引 Q1-01～Q1-11，并把 04 真值未知、03 已用于选模和人工签收待完成写入局限，不提前引入 Q2/Q3 的未完成结果。
