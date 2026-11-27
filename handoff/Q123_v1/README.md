# APMCM 2026 D 题 Q1–Q3 整合交付

本包固定使用原版 **hgb_gap_mix v1** 和 **V1.2** 数据接口。整合版已经用两套锁定权重核对 16,635 条预测，并用 Kaiwu SDK 1.4.3 对 07、08 全池实际完成 8 位适配及本地求解。每次运行的输入、矩阵、原始样本和汇总均独立留档。

## 论文手入口

- [完整技术包](Q123_v1_integrated.zip) 含原版权重、官方数据、代码、一键复现、运行证据、合稿说明和逐文件清单。解压后先读根目录 README.md，再读 paper/PAPER_EVIDENCE.md。
- [Q1 验证表](paper/q1_validation.csv) · [04 冻结预测表](../v1_2/q1_holdout_predictions.csv) · [Q1 五池推理复核](evidence/q1_verification.json)
- [Q2/Q3 论文用实验表和本地成本](paper/q23_experiment_table.csv) · [对照图 PNG](paper/q23_run_comparison.png) · [对照图 SVG](paper/q23_run_comparison.svg) · [SDK 独立验证](evidence/sdk_verification.json)

| 问题 | 论文主结果 |
| --- | --- |
| Q1 | 02 拟合，03 验证与选模，04 生成 3,703 条预测。03 上 MAE 为 2.47154，RMSE 为 4.58269，Spearman 为 0.93826。 |
| Q2 | 02+03 重训的原代理评分，NO2 全池 2,704 个候选。实际 SDK 返回 Y–Ti–NO2，V̂ = 1.491928，与枚举一致。 |
| Q3 | O3、NO2、FO2 各 2,704 个候选，每组一个 104 位 QUBO，覆盖全部 8,112 个候选。组间按返回的合法候选原尺度分数比较，实际最优为 Na–Nb–O3，V̂ = 0.540023。 |

Q2 和 Q3 的上述材料是在冻结代理目标下取得的最优。论文应把系数范围、矩阵规模、每组采样预算、本地 SDK 求解时间以及合法样本比例、种子命中频率分别说明。技术包里的正式结果来自 **CPU 上的本地 SDK 求解**。先前归档的设备短名单任务可作为独立历史对照。正式英文合稿和官方提交格式由论文手处理。

完整 ZIP 的 SHA-256 为 `5a1bae82dfb05935dcd879b9830a44fee162b68bd7fa2b19d0946d35a89157b6`。
