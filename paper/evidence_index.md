# 论文证据索引（L3）

**建立日期：** 2026-11-27；**V2更新：** 2026-11-28（Asia/Shanghai）
**适用工程：** 2026 APMCM Problem D 论文  
**依据：** `paper/reviews/sample_paper_structure_mapping.md`、最新版论文执行书、现有实验报告/数据/模型/代码、`handoff/Q123_v1/`、`handoff/q23_fix/`、`handoff/q23_supplement/` 及 `paper/reviews/experiment_update_audit_20261128.md`
**用途：** 把拟写主张绑定到可追溯证据；本文件不是实验结果，也不把计划任务视为已完成。

## 1. 状态定义

索引只使用以下四种证据状态：

| 状态 | 定义 | 写作规则 |
|---|---|---|
| **已完成** | 仓库内已有相互对应的报告、数表/模型/代码或验收记录，足以支持限定范围内的主张。 | 可写入方法或结果，但仍需保留证据路径和适用边界。 |
| **待复核** | 已有产物或总结，但仍需人工签收、独立核对、与正式模型对齐，或底层原始证据未完整进入本仓库。 | 只能写成初步/前置证据，不得写成最终验收结论。 |
| **待实验** | 任务、输入或原型已定义，但正式实验和验收产物尚未完成。 | 只写方法计划或任务 ID，不填写数值结果。 |
| **暂无证据** | 当前仓库没有支持该主张的任务回执、原始数据、报告或复算记录。 | 不得在正文、摘要或结论中提出该主张。 |

证据等级另按可追溯性登记：**A** 表示仓库内有原始 CSV/JSON、运行记录及复核脚本，可静态追溯；**B** 表示已有汇总或平台记录，但部分原始字段、计时边界或人工签收仍缺；**UNVERIFIED** 表示历史原始证据缺失或无法闭合。证据等级不替代双人签字。

O-08～O-15 按最新整合交付包和补充实验归档分别登记，不再统一视为待完成。必须区分 **Kaiwu SDK 1.4.3 CPU求解**、**Kaiwu 1.4.4仅映射复核**、**本地SA**、**历史17/30变量SPQC短名单任务** 与 **四个最终104变量SPQC任务**。正式两档104变量编码使用已知组内代理最小值，只是 oracle-assisted 精度映射实验；科学候选来自原始代理表枚举。四个SPQC任务只有3个任务各返回至少一个组内代理argmin，样本数为10/10/7/5，不能据此估计硬件成功率、稳定性或量子优势。

## 2. 章节证据覆盖总览

| 论文章节 | 需要的数据、公式、结果与结论 | 当前主要证据 | 状态 | 当前可写边界 |
|---|---|---|---|---|
| 01 Introduction | 官方问题背景、三问关系、有限预算筛选价值、贡献边界 | `2026 APMCM Problem D/2026 APMCM Problem D.pdf`；结构映射；执行书；V2审计报告 | 已完成 | O-10、O-14和最终104变量真机已有结果；贡献仍须保留代理真值、硬件小样本和成本NA边界。 |
| 02 Problem Formulation | 五项违背度公式、严格达标口径、有序 A/B、Q2/Q3 决策变量、独热约束 | `DATA_CONTRACT.md`；`audit/phase1/REPORT.md`；`q1/violation.py`；`handoff/Q123_v1/README.md`；整合包 `paper/PAPER_EVIDENCE.md` | 已完成 | V 公式可写；正式采用每个 X 组一张 104 位 QUBO，并以原尺度分数组间比较。须说明这与执行书早期 208 位联合编码计划的差异。 |
| 03 Data and Audit | 02/03/04/07/08/11/12 行数、集合关系、哈希、标签复算、舍入误差、盲测边界 | 数据审计；`handoff/q23_supplement/O14/` | 已完成 | 11/12含529个稀疏A/B组合；八组盲池矩阵与本地SA已完成，但没有物理标签。 |
| 04 Q1 Surrogate | 模型结构、五折开发、03 选模、低尾/Top-K、划分敏感性、有限预算价值、04 预测边界 | `experiments/q1_ablation_v1/`；`experiments/q1_v12/`；`experiments/q1_random_search_03/`；`handoff/v1/`；`handoff/v1_2/` | 已完成（技术）/ 待复核（人工签收） | `V<5`是项目操作性低尾阈值；03参与选模，预算回放是回顾性结果而非独立验证；04只能报告代理预测。 |
| 05 Q2 Fixed-X QUBO | `q23_final` 的 07 分数、104 变量、矩阵/映射/offset、枚举基准、本地 SDK 求解结果 | `handoff/Q123_v1/README.md`；`handoff/Q123_v1/paper/q23_experiment_table.csv`；`handoff/Q123_v1/evidence/sdk_verification.json`；整合 ZIP 内正式运行目录 | 已完成 | 可写固定 NO2 的 Q2 正式整数模型和 CPU 本地 SDK 结果；不得称为真实硬件结果。 |
| 06 Q3 Groupwise QUBO | 分组主线、208位浮点对照、107位投影、盲池与真机 | `handoff/Q123_v1/`；`handoff/q23_fix/`；`handoff/q23_supplement/O10,O13,O14/` | 已完成（限定范围） | 107位投影改变最优且不适配8位；主结果仍为三张104位分组矩阵。 |
| 07 Hardware and Precision | QUBO→Ising、offset、8位、排序/预算、SDK与SPQC | `handoff/q23_fix/`；`handoff/q23_supplement/O10,O11,O13/` | 已完成（有限证据/NA） | O-11新复核已定位计数器缺陷，历史0/300原始日志仍UNVERIFIED；四个正式任务中3个返回组内代理argmin。`probe4_01`详情NA。 |
| 08 Results and Discussion | 三问结果、盲池、四层误差、13类负例、R1--R4和成本 | `handoff/q23_supplement/O14,O15/`；`q23_fix` | 已完成（现有证据范围）/ 待人工签收 | 四层误差不相加；178.131869 s有CSV依据，162.556 s及SDK短计时原件仍UNVERIFIED。 |
| 09 Conclusion | 分别回答三问、适用范围、候选筛选建议、局限 | 全部V2证据及审计报告 | 已完成（待终审） | 不声称物理最优、硬件稳定性或量子优势。 |

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
| FORM-02 | 05, 06 | Q2/Q3 分组 104 位独热映射、整数代价、罚值、offset 与组间比较 | `handoff/Q123_v1/README.md`；`handoff/q23_fix/scripts/stage2_quant_partition.py`；整合 ZIP 内矩阵及运行摘要 | O-08, O-09 | 已完成（映射范围） | 两档代价依赖已知组内代理最小值；`np.rint`下差值小于0.01及精确0.01均映射为0，唯一零档要求第二名差值严格大于0.01。lambda=2、offset=4。该QUBO不构成独立winner发现。 |

## 4. Q1 代理模型证据

### 4.1 实验、模型与结果

| 证据 ID | 对应章节 | 内容/拟支持主张 | 仓库相对路径 | 实验/任务 ID | 状态 | 限制或待办 |
|---|---|---|---|---|---|---|
| Q1-01 | 03, 04 | 中位数、Ridge、随机森林的组成基线及五折结果 | `experiments/baseline_v1/REPORT.md`；`experiments/baseline_v1/results.json`；`experiments/baseline_v1/fold_metrics.csv` | B101, Q1-02 | 已完成 | 基线只用于方法对照，不替代最终模型。 |
| Q1-02 | 04 | 12 个配置的五折消融、直接/间接模型、带隙处理及低尾评价 | `experiments/q1_ablation_v1/REPORT.md`；`experiments/q1_ablation_v1/model_comparison.csv`；`experiments/q1_ablation_v1/paired_ablation.csv` | Q301, Q1-03～Q1-06 | 已完成 | 02 五折用于开发；须与 03 正式选择结果分开报告。 |
| Q1-03 | 04 | 冻结候选、选模规则和最终 `hgb_gap_mix` | `experiments/q1_ablation_v1/frozen_shortlist.json`；`handoff/v1/validation_metrics.csv`；`experiments/q1_v12/model_selection.md` | Q401 | 已完成 | 03 已参与选择，不能把其后新增对照当作独立择优。 |
| Q1-04 | 04, 08 | 03 上 MAE、RMSE、Spearman、低尾 MAE、Top-K 和物性误差 | `experiments/q1_ablation_v1/REPORT.md`；`handoff/v1/validation_predictions.csv`；`handoff/v1/validation_physics.csv` | Q401 | 已完成 | 03 没有 V=0 样本，结果不证明严格可行候选召回。 |
| Q1-05 | 04, 08 | 冻结后物性/带隙补证、阈值误差、五罚项分解和稳定性 | `experiments/q1_v12/REPORT.md`；`experiments/q1_v12/model_comparison.csv`；`experiments/q1_v12/stability.csv`；`experiments/q1_v12/stability_summary.csv` | Q501 | 已完成 | 属冻结后补证，不改变冻结模型和已发布分数。 |
| Q1-06 | 04, 08 | 有限预算下代理筛选相对随机抽查的价值 | `experiments/q1_random_search_03/REPORT.md`；`experiments/q1_random_search_03/comparison.csv` | Q502 | 已完成（回顾性） | 03参与正式选模；23/50与随机期望0.8818不是独立外部验证，不能外推为未知材料命中概率。 |
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
| Q23-04 | 05, 06 | 四张104位整数矩阵、独热约束、offset、映射与枚举核查 | `handoff/Q123_v1/Q123_v1_integrated.zip` 内 `q23/runs/sdk_v1_frozen_30x10/matrices/`、运行 summary/verification；`handoff/Q123_v1/README.md` | O-08, O-09 | 已完成（oracle-assisted映射） | 原始代理表枚举先确定数值argmin；两档矩阵只核查该argmin的8位映射和采样。Q3采用三张分组矩阵。 |
| Q23-05 | 05, 06, 07, 08 | Kaiwu SDK 1.4.3 CPU 本地 8 位适配、四组各 300 条样本、解码与能量复算 | `handoff/Q123_v1/evidence/sdk_verification.json`；`handoff/Q123_v1/paper/q23_experiment_table.csv`；整合 ZIP 内原始 samples/summary | O-11, O-12 | 已完成 | 仅为 CPU 本地 SDK 求解；不得写成 SPQC 真机执行或量子优势。 |
| Q23-06 | 05, 06, 08 | Q2 返回 Y–Ti–NO2，Q3 组间最优为 Na–Nb–O3；均与合法枚举最优一致 | 同 Q23-05 | O-09, O-12 | 已完成 | 结论限定于冻结代理目标和量化模型；不是未知物理真值。 |
| Q2-01 | 05 | 07 全池 2,704 条 `q23_final` 分数及正式 104 变量矩阵 | `handoff/v1_2/q2_pool_predictions.csv`；`handoff/Q123_v1/Q123_v1_integrated.zip` | O-07, O-08 | 已完成 | 固定 X=NO2；正式结果采用分组整数模型。 |
| Q2-02 | 05, 08 | 11盲池529个稀疏组合的浮点/整数专属矩阵与本地SA | `handoff/q23_supplement/O14/` | O-07, O-14 | 已完成 | 300/300合法；25/30与16/30命中；本地SA且无物理标签。 |
| Q3-01 | 06 | 08 全池 8,112 条 `q23_final` 分数及 O3/NO2/FO2 三张 104 位矩阵 | `handoff/v1_2/q3_pool_predictions.csv`；`handoff/Q123_v1/Q123_v1_integrated.zip` | O-07, O-08 | 已完成 | 实际路线为按 X 分组建模后用原尺度分数比较，不是单张 208 位矩阵。 |
| Q3-02 | 06, 08 | 12盲池三组各529个稀疏组合、六张专属矩阵与本地SA | `handoff/q23_supplement/O14/` | O-07, O-14 | 已完成 | 仅为本地SA代理优化；README时间旧值与CSV/JSON冲突，以原始数表为准。 |
| Q3-03 | 06, 07, 08 | 107变量二阶投影对照 | `handoff/q23_supplement/O10/` | O-10 | 已完成（负面对照） | 投影最优Rb--Ta--O3，不同于原始Na--Nb--O3；Top-5重合0，8位不适配。 |

## 6. O-08～O-15 任务证据矩阵

| 任务 ID | 对应章节 | 任务状态 | 当前证据状态 | 已有输入/前置证据 | 完成后必须登记的证据 |
|---|---|---|---|---|---|
| **O-08** | 05, 06 | 已完成 | 已完成 | `handoff/Q123_v1/Q123_v1_integrated.zip` 内四张正式 104 位矩阵、运行快照、哈希与生成/复现入口 | 论文中说明 Q3 从早期 208 位计划调整为三张 104 位分组模型及其理由。 |
| **O-09** | 05, 06 | 已完成 | 已完成 | 整合包内枚举、映射、解码、量化能量逐样本复算；`handoff/Q123_v1/evidence/sdk_verification.json` | 写作时保持 offset、整数能量与原尺度 `V_hat` 的层次分离。 |
| **O-10** | 06--08 | 已完成 | 已完成（负面对照） | 107变量投影、8112候选、300样本、投影/原始双最优及8位范围见`O10/` | 高Spearman不保低尾最优；不得写成主模型。 |
| **O-11** | 07, 08 | 已完成（新复核） | A；历史0/300日志UNVERIFIED | `handoff/q23_supplement/O11/reconciliation/o11_reconciliation.json`及三份逐样本CSV；`O11/README.md` | 同一批300样本的新复核证明旧计数器把绝对列索引再次减去`n_left`：正确为8合法/8命中，旧计数器为0/0；显式30批种子为10合法、10命中、9/30批命中。新复核不得冒充缺失的历史运行。 |
| **O-12** | 07, 08 | 已完成 | 已完成 | Kaiwu SDK 1.4.3 CPU四组各300样本；1.4.4仅做映射复核 | 两版本用途不得混写。 |
| **O-13** | 05--08, Appendix | 已完成（有限样本） | A（四个正式任务）；B（额度）；`probe4_01` UNVERIFIED | `handoff/q23_supplement/O13/results/o13_results.json`、`receipt_template.csv`、`evidence/`、`results/credits_ledger.csv`、`probe4_01_gap.md` | 四个正式SPQC-550任务中3/4返回至少一个组内代理argmin，不是硬件成功率。七次额度账目与正式任务证据分开登记；`probe4_01`不得形成正式实验结论。 |
| **O-14** | 03, 05, 06, 08, Appendix | 已完成（本地SA） | A | `handoff/q23_supplement/O14/results/o14_results.json`、`o14_runs.csv`、`timings.csv`及八份samples CSV | 八组529组合均300/300合法，38.533--48.536 s；Q2为Y--Ti--NO2，Q3三组为Ca--Sn--O3、Y--Ti--NO2、Rb--Ti--FO2，最终Ca--Sn--O3。使用盲池内部完整分数范围缩放，不得称完全oracle-free；不是SDK或真机。 |
| **O-15** | 07, 08 | 部分完成 | A（本地SA/映射）；B（SDK完整流程）；短计时及旧总时UNVERIFIED | `handoff/q23_supplement/O15/local_sa_timing.csv`、`error_attribution.csv`、`resource_cost.csv`、`timings.csv`；`handoff/q23_fix/results/stage1_sdk_ising.json` | O15-R01--R04合计178.131869 s；162.556 s保留历史但来源缺失。正式SDK完整流程20.81--20.96 s/组；0.48--0.69 s仅为补充报告中的`opt.solve()`口径，原始CSV/代码未归档。浮点映射残差采用实际非零值。 |

## 7. Kaiwu、硬件精度和成本证据

| 证据 ID | 对应章节 | 内容/拟支持主张 | 仓库相对路径 | 实验/任务 ID | 状态 | 限制或待办 |
|---|---|---|---|---|---|---|
| HW-01 | 07 | Kaiwu 1.4.3 环境、人工小模型、QUBO→Ising 约定和本地链路前置总结 | `Kaiwu_Precheck_Phase1_Summary.md` | H002, D-01 | 待复核 | 原始 SDK 证据包未进入本仓库；只能作为前置总结引用。 |
| HW-02 | 07, 08 | 人工 104/208 变量模型的直接 int8 量化排序/可行性失败风险 | `Kaiwu_Precheck_Phase1_Summary.md` §6–7 | H002, D-01 | 待复核 | 使用人工代价，不是正式 `q23_final` 矩阵；可支持风险动机，不能支持正式模型结论。 |
| HW-03 | 07 | 最终104变量SPQC-550任务、回执、矩阵SHA与返回 | `handoff/q23_supplement/O13/results/o13_results.json`；`receipt_template.csv`；`receipts/`；`evidence/` | O-13 | 已完成（A，有限样本） | 四任务中3个各至少返回一个代理argmin；只支持任务级事实，不支持硬件稳定性或成功率。七次额度另见账目，`probe4_01`另记UNVERIFIED。 |
| HW-04 | 07, 08 | 正式矩阵 8 位适配、Kaiwu SDK CPU 本地求解、解码与能量复算 | `handoff/Q123_v1/evidence/sdk_verification.json`；`handoff/Q123_v1/paper/q23_experiment_table.csv`；整合 ZIP 内运行目录 | O-11, O-12 | 已完成 | 本地 SDK 结果不是 SPQC 真机结果。 |
| HW-05 | 07, 08, Appendix | 历史 SPQC-550 短名单求解 | `handoff/Q2Q3_论文与图表.zip` 内 `q2_int_01.log`、`q3_int_01.log`、解码脚本与矩阵 | O-13 | 已完成（历史短名单） | Q2为17变量、Q3为30变量；不是最终104变量模型。Q3只支持O3组结论，不支持唯一A/B。 |
| HW-06 | 07, 08 | 四层误差与成本边界 | `handoff/q23_supplement/O15/error_attribution.csv`、`timings.csv`、`local_sa_timing.csv`、`resource_cost.csv` | O-15 | 部分完成（A/B分层） | 178.131869 s有CSV依据；162.556 s与0.48--0.69 s原始包未归档。正式SDK完整流程为20.81--20.96 s/组；queue/exec/货币成本仍NA。 |
| HW-07 | 06, 07 | 208变量联合浮点对照、offset修正、直接8位失败 | `handoff/q23_fix/results/stage1_sdk_ising.json`；`stage2_quant_partition.json` | O-09, O-11 | 已完成（对照） | 合法态能量精确，但直接8位量化不保最优/可行性；不作为最终主模型。 |
| HW-08 | 06--08 | 107变量投影、双口径量化与K×λ扫描 | `handoff/q23_supplement/O10/`；`O11/reconciliation/` | O-10, O-11 | 已完成（A；历史日志除外） | 投影改变最优；最低档包含最优不等于唯一保持。新复核解释0/300计数器缺陷，历史原始日志仍UNVERIFIED。 |
| HW-09 | 03, 05, 06, 08 | 盲池八组本地SA | `handoff/q23_supplement/O14/results/o14_results.json`、`o14_runs.csv` | O-14 | 已完成（A） | 每组529稀疏组合、300/300合法；内部全分数范围缩放；不是SDK/真机且无物理标签。 |

## 8. 结果、图表与结论的证据规则

### 8.1 当前可进入论文的结果

- 02/03 数据审计、标签复算、低尾分布和数据划分事实。
- Q1 的冻结模型、五折开发、03 正式选择结果、冻结后补证、稳定性和随机预算对照。
- 04、07、08、11、12 的代理评分文件、模型版本、行数、哈希和候选排序；其中 04/盲池不得附加未知真值结论。
- Q2/Q3 的分组 104 位独热公式、正式矩阵、枚举 oracle、CPU 本地 SDK 样本质量及返回候选；须明确冻结代理目标和非真机边界。
- O-10投影失真、O-11量化双口径、O-13四个最终真机任务、O-14盲池本地SA和O-15分层误差；均须保留审计限定。

### 8.2 当前禁止写成结果的内容

- 将 `deliverable/matrices/qubo_q2.npz` 或 `qubo_q3.npz` 称为 `q23_final` 正式矩阵。
- 将前置 Ridge 矩阵中的 La/Ti 等候选称为最终 Q2/Q3 最优解。
- 将 07/08 的最小 `V_hat` 直接称为真实物理最优或 SPQC 真机求解结果；可在限定口径下称为 CPU 本地 Kaiwu SDK 返回结果。
- 将O-14本地SA称为SDK或SPQC结果，或把无标签盲池写成物理验证。
- 将107变量投影称为保持原始最优；其投影最优实际为Rb--Ta--O3。
- 将最低能级包含原始最优等同于唯一候选保持，或隐去两层编码的oracle-assisted限制。
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
| 精度、误差和成本图 | `O10/`、`O11/reconciliation/`、`O13/`、`O15/error_attribution.csv`、`local_sa_timing.csv`、`resource_cost.csv` | 已完成（A/B；历史缺口UNVERIFIED） | 采用原始CSV/JSON；不把四层误差相加。0.48--0.69秒只登记为未归档原件的`opt.solve()`补充口径，不作完整SDK耗时。 |

## 9. 写作就绪度与下一步

| 优先级 | 章节 | 就绪度 | 原因 |
|---|---|---|---|
| 1 | **04 Q1 Surrogate Modeling and Low-Tail Screening** | 高 | 方法、模型、数表、图、代码、哈希、稳定性和局限均已形成完整链条。 |
| 2 | 03 Data and Audit | 高 | 数据事实和审计证据完整，可为 Q1/Q2/Q3 提供统一口径。 |
| 3 | 02 Problem Formulation | 高 | V 公式与正式分组 QUBO 均有证据；需解释实际 104 位分组路线与早期 208 位计划的差异。 |
| 4 | 01 Introduction | 中 | 可写背景与问题链，但最终贡献列表应等 Q2/Q3 完成后冻结。 |
| 5 | 05–06 Q2/Q3 | 高（现有证据范围） | 正式矩阵、CPU SDK、107位对照、盲池和最终真机均有证据；物理标签仍缺。 |
| 6 | 07–08 Hardware/Results | 高（历史缺口需保留） | 新O-11对账、O-14运行表和O-15本地SA计时已有证据；历史0/300日志、162.556 s来源、SDK短计时原件及完整成本仍需标记。 |
| 7 | 09 Conclusion / Abstract | 高（待终审） | 已更新为V2边界，不声称物理最优、稳定性或量子优势。 |

V2正文已整合O-10～O-15现有成果并完成第四阶段科学定位整改。内容冻结后只需按正式构建流程核查页数、交叉引用和版面；已由新原始表闭合的数值与历史缺失记录须分开，历史0/300日志、`probe4_01`、162.556 s来源和SDK短计时原件继续保持UNVERIFIED，缺失字段保持NA。
