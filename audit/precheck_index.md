# Q1 V1.2 原始资料与核验索引

2026-11-27，北京时间。官方 PDF 和附件 README 保留于原始目录。两份文档的哈希、章节、9 个官方公开哈希的实际匹配结果及数据审计合并记录可追溯。[数据审计](data_audit.json)

| 依据 | 要点 | 本地证据 |
| --- | --- | --- |
| [官方题面](../2026%20APMCM%20Problem%20D/2026%20APMCM%20Problem%20D.pdf) 第 2–5 页 | 五项平方铰链、严格目标、有限候选和 02/03/04 分工 | [公式测试](../tests/test_q1_data.py) · [舍入核验](phase1/REPORT.md) |
| [官方 README](../2026%20APMCM%20Problem%20D/date/README_数据集说明.md) 第 2 节 | 官方汇总 19 条 V=0，带隙条件含等号，其余三条件写严格符号 | [逐行标签对账](label_checks.csv) · [三种口径的单项和联合统计](q1_label_audit.json) |
| 官方 README 第 4、5 节 | 预测表 6 列。全库按有序对分组，官方记载 19 个正例对先被锁定到 04 | [初核结果](init_results.json) · [输入白名单及模式](features_schema.json) |
| 官方 README 第 7 节和 [公开哈希](../2026%20APMCM%20Problem%20D/date/sha256_public.json) | 切分哈希和六位小数精度，最大实测复算偏差约 1.02e-5 | [新审计记录](q1_label_audit.json) |
| [D-00 前置交付](../deliverable/README.md) | 41 项数据检查、历史直接基线和浮点联调预测 | [重跑记录 I001](../EXPERIMENT_LOG.md) · [V1.2 临时模型与两池](../experiments/q1_v12/baseline_v0/manifest.json) |

本地核验了 02、03 的实际标签和各池公开组成关系。19 条零违背、15 条严格达标，以及分 X 的计数来自官方汇总。具体盲测身份和真值未推断。建模只使用合法成分字段，划分哈希仅用于说明官方设计。
