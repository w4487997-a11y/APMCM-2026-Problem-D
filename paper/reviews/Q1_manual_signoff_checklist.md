# Q1 人工签收检查清单

适用基准 `b01a6ab6b87896c65ac8f4adf746ee4f393db3b6`，分支 `codex/latex-environment-audit`。签收对象为冻结 Q1 v1 模型及 V1.2 接口。下列人工检查的初始状态均为 **PENDING**。

## 已有机器验收

[V1 验收](../../handoff/v1/ACCEPTANCE.md)与 [V1.2 验收](../../handoff/v1_2/ACCEPTANCE.md)均已有本地程序通过记录。[V1.2 机器审计](../../audit/v12_acceptance.json)确认了输入和交付散列、训练角色与有序组隔离、公式与指标的独立复算、官方行序和 ID、保存模型全量推理及跨池分数一致性。[五池推理复核](../../handoff/Q123_v1/evidence/q1_verification.json)记录了各池从保存模型复算的最大预测差均为 0。V1.2 验收另有 14 项自动测试及补证重跑记录。 [复跑日志](../../audit/v12_replay.txt)

人工签收复用上面的证据，执行下列查阅、散列核对和文件对账即可，无需重新训练、选模或重复实验。论文引用的证据范围见[证据索引 §3–§5](../evidence_index.md)。

## 七项人工检查

| 检查范围 | 证据文件 | 实际检查方法 |
| --- | --- | --- |
| **01 数据隔离、官方数据哈希及 V 公式** | [官方题面](../../2026%20APMCM%20Problem%20D/2026%20APMCM%20Problem%20D.pdf) · [官方 SHA-256 清单](../../2026%20APMCM%20Problem%20D/date/sha256_public.json) · [初核结果](../../audit/init_results.json) · [数据契约](../../DATA_CONTRACT.md) · [V 实现](../../q1/violation.py) · [逐行标签审计](../../audit/q1_label_audit.json) | 核对官方附件的文件名和 SHA-256 与清单相符，参照初核 9/9 记录。对照题面与代码检查五项平方铰链的符号、0.5 eV 尺度及官方带隙 `gap` 列。从 02/03 的 15,225 条对账记录抽查边界和零带隙例，区分公式零罚值、严格不等式和舍入容差。核对 02/03/04 有序 `(A,B)` 互斥，保留 A=B，模型特征仅用 `A,B,X`，04 仅用于推理。 |
| **02 02 五折开发与 03 正式选模** | [02 五折清单](../../audit/phase1/folds_02.csv) · [开发报告](../../experiments/q1_ablation_v1/REPORT.md) · [冻结候选清单](../../experiments/q1_ablation_v1/frozen_shortlist.json) · [03 正式指标](../../handoff/v1/validation_metrics.csv) · [V1.2 选模说明](../../experiments/q1_v12/model_selection.md) | 按有序 `(A,B)` 检查每组只归入一个验证折。核对 02 的 12 个配置 × 5 折共 60 条指标。用 03 的四个冻结候选及预定筛选、MAE 门槛和并列规则复核 `hgb_gap_mix` 的选择。区分正式选模和冻结后补证，03 预算回放标为回顾性。 |
| **03 模型方案与训练角色** | [V1.2 清单](../../handoff/v1_2/manifest.json)的 `selected_spec`、`model_training` · [模型冻结记录](../../EXPERIMENT_LOG.md) · [Q1 权重](../../handoff/v1/models/q1_final.joblib) · [Q23 权重](../../handoff/v1/models/q23_final.joblib) | 将权重路径、`model_training` 与 CSV 内的 `model_version` 对照。两套产物沿用 `hgb_gap_mix`。确认 `q1_final_v1_hgb_gap_mix` 的拟合及预处理只用 02、用于 04，`q23_final_v1_hgb_gap_mix` 沿用冻结方案在 02+03 拟合、用于 07/08/11/12。03 正式评估对应 Q1 训练角色。 |
| **04 模型、预测 CSV 和哈希复现** | [V1 清单](../../handoff/v1/manifest.json) · [V1.2 清单](../../handoff/v1_2/manifest.json) · [源码包](../../handoff/v1_2/q1_source.bundle) · [V1 复跑记录](../../audit/replay_v1.txt) · [保存模型推理结果](../../handoff/Q123_v1/evidence/q1_verification.json) | 对 `handoff/v1/models/` 中的两份权重、V1.2 五份按池 CSV、合并 CSV 和源码包计算 SHA-256，对照清单的 `models`、`outputs`、`combined_output` 和 `source_snapshot`。可用 `git bundle list-heads handoff/v1_2/q1_source.bundle` 核对源码提交。对照 V1 和 V1.2 的官方六列及原尺度 `V_hat`，检查数值和行序一致。以存档复跑记录核查可复现性。 |
| **05 04 的 3,703 条预测及未知真值** | [官方 04 输入](../../2026%20APMCM%20Problem%20D/date/04_castelli_test_holdout.csv) · [04 冻结预测](../../handoff/v1_2/q1_holdout_predictions.csv) · [V1.2 清单](../../handoff/v1_2/manifest.json)的 `outputs["04"]` | 核对 3,703 条记录、唯一 ID、官方六列和原始行序。检查 `pool` 与 `source_pool` 均为字符串 `04`，模型版本属于 Q1 角色，`V_hat` 有限且非负。交付字段为组成、元数据或代理预测。04 的真实物性、真实 V 和盲测命中率仍未知。 |
| **06 Q2/Q3 下游读取和分数一致性** | [数据契约](../../DATA_CONTRACT.md) · [07](../../handoff/v1_2/q2_pool_predictions.csv) · [08](../../handoff/v1_2/q3_pool_predictions.csv) · [11](../../handoff/v1_2/q2_blind_predictions.csv) · [12](../../handoff/v1_2/q3_blind_predictions.csv) · [合并表](../../handoff/v1_2/candidate_predictions.csv) · [整合包入口](../../handoff/Q123_v1/README.md) | QUBO 负责人登记实际读取的文件、池号、版本和 SHA-256。把下游读入的候选表按 `(pool,id)` 对比官方六列及冻结的原尺度 `V_hat`。核对四池为 **2,704 / 8,112 / 529 / 1,587** 行，合并为 12,932 行，复合键唯一。池号按字符串保留前导零并检查 `pool=source_pool`。跨池共享 ID 的原始分数须一致。使用缩放或量化的下游入口以原始输入或原始字段对账，并单独登记派生代价。核对输入即可，无需求解。 |
| **07 04 平台字段人工核对** | [公开规范查阅记录](../../audit/submission_format_check.md) · [04 内部交付表](../../handoff/v1_2/q1_holdout_predictions.csv) | 由有权限的队员登录赛事平台，记录日期和实际页面。确认是否有 04 专用入口，并按页面或通知记录实际要求的文件类型、文件名、字段顺序、表头、ID 和行序。在证据栏登记页面、通知或回执，截图遮盖账号信息。无法核实的字段保持 `PENDING`。内部 CSV 的字段以数据契约为准，平台提交字段以实际页面核对为准。 |

## 队员签收记录

由队员依据实际核对填写，日期使用北京时间。证据位置可填写提交号、文件路径、哈希、对账输出或平台凭证。发现差异时登记未解决事项及负责人。独立复核人由未编写被核查核心模块的队员担任。

| 检查项 | 填写角色 | 核对人 | 日期 | 检查结果 | 未解决事项 | 证据位置 |
| --- | --- | --- | --- | --- | --- | --- |
| 01 数据、哈希及 V 公式 | 独立复核人 |  |  | PENDING |  |  |
| 02 五折与 03 选模 | 独立复核人 |  |  | PENDING |  |  |
| 03 模型训练角色 | 独立复核人 |  |  | PENDING |  |  |
| 04 模型与预测复现 | 独立复核人 |  |  | PENDING |  |  |
| 05 04 冻结预测及边界 | 独立复核人 |  |  | PENDING |  |  |
| 06 下游读取与对账 | QUBO 下游负责人 |  |  | PENDING |  |  |
| 07 04 平台字段 | 具备平台权限的队员 |  |  | PENDING |  |  |

| 签收角色 | 姓名／签收 | 日期 | 检查结果 | 未解决事项 | 证据位置 |
| --- | --- | --- | --- | --- | --- |
| Q1 交付负责人（确认版本并提供证据） |  |  | PENDING |  |  |
| 独立复核人（确认 01–05 的实际检查结果） |  |  | PENDING |  |  |
| QUBO 下游负责人（确认 06 及数据契约） |  |  | PENDING |  |  |

## 与 V1 和 V1.2 验收栏的对应

| 原验收记录 | 本清单对应记录 | 队员填写内容 |
| --- | --- | --- |
| [V1 验收](../../handoff/v1/ACCEPTANCE.md)「人工及外部事项」 | 角色签收表和 01–07 | 该文件只有 `PENDING` 汇总行。核对后由队伍登记相关角色的姓名、日期、结果及证据引用，已有机器验收记录保留。 |
| [V1.2 验收 §B](../../handoff/v1_2/ACCEPTANCE.md#b-队员复核记录)「数据隔离、03 指标与公式」 | 01–05，独立复核人 | 核对后填写「复核人、日期与证据位置」，并登记遗留事项。 |
| V1.2 验收 §B「按池读取和分数复核」 | 06，QUBO 下游负责人 | 对账实际消费文件后填写签收及相应输入证据。 |
| V1.2 验收 §B「04 的官方提交字段和路径」 | 07，实际登录核对的队员 | 登记实际页面、字段和路径。未核实项写明查阅范围及待确认内容。 |

填写顺序为 Q1 交付负责人确认版本并交证据，独立复核人完成 01–05，QUBO 负责人完成 06，具备权限的队员完成 07。最后由队伍按上表把实际结果及证据位置登记到原验收栏。
