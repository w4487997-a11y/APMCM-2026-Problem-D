# 2026 APMCM D 题队内协作仓库

Q1 模型 v1 已冻结，V1.2 包含预测交接、补充实验和验收记录。最终模型从组成预测四项物性，并对零带隙与正带隙的罚值作概率混合。03 验证的 MAE 为 2.4715，RMSE 为 4.5827，Spearman 为 0.9383，Top-25 和 Top-50 重合分别为 8/25 和 20/50。模型选用依据与冻结后的补充实验见[选模记录](experiments/q1_v12/model_selection.md)。

## Q2 和 Q3 从这里开始

1. 阅读 [V1.2 执行书](APMCM_D_final_execution_V1.2.md)的第 07–10 节和[数据契约](DATA_CONTRACT.md)。默认用 Q2 的 07 全池和 Q3 的 08 全池。两份 CSV 中的 `V_hat` 已用 02+03 拟合的 `q23_final` 打分，可直接用于编码，无需重训 Q1。
2. 对照[统一清单](handoff/manifest.json)核验输入名、行数、模型版本和 SHA-256。按字符串读取 `pool`，保留有序 A/B 和合法的 A=B。使用汇总表时按 `pool` 过滤，以 `(pool,id)` 作为键。
3. 建议在各自的分支开发 QUBO 和 Kaiwu 求解入口，留存矩阵约定、解码映射、原始样本和运行配置。将缩放或量化后的代价单独保存。全池 07/08 是正式主线，11/12 可另做盲池对照。`deliverable/` 中矩阵对应旧基线，可用于核对能量和接口。

## 项目结构

| 路径 | 内容 |
| --- | --- |
| [`2026 APMCM Problem D/`](2026%20APMCM%20Problem%20D/) | 官方英文题面、原始 CSV、数据说明和公开哈希，按原始目录保存。04 含成分与 ID。 |
| [`q1/`](q1/)、[`tests/`](tests/) | 目标违背度、训练、推理、验证、交接导出与测试。 |
| [`handoff/v1/`](handoff/v1/)、[`handoff/v1_2/`](handoff/v1_2/) | 冻结模型、原始发布与 V1.2 按池预测。 |
| [`experiments/`](experiments/)、[`audit/`](audit/) | 实验配置、预测、指标、图表、复跑记录、独立程序审计及审计脚本。 |
| [`deliverable/`](deliverable/)、[Kaiwu 前置总结](Kaiwu_Precheck_Phase1_Summary.md) | 前置数据审计、基线、QUBO 矩阵、能量校验和 SDK 可行性记录。 |
| [项目进度](PROJECT_STATUS.md)、[决策](DECISIONS.md)、[实验日志](EXPERIMENT_LOG.md)、[协作规范](AGENTS.md) | 选模过程、进度、已知限制和队内复核要求。 |

仓库用于队内协作。官方附件和冻结产物按原始字节保存，Git 禁用自动换行转换以便跨平台核验 SHA-256。Kaiwu 凭据在各自机器上配置，队内共享前置日志前先检查凭据和账号信息。

## 交付文件

| 用途 | 文件 |
| --- | --- |
| Q1 盲测 3,703 条 | [V1.2 的 04 预测](handoff/v1_2/q1_holdout_predictions.csv) |
| Q2/Q3 的四池 12,932 条 | [候选汇总](handoff/v1_2/candidate_predictions.csv) · [Q2 全池](handoff/v1_2/q2_pool_predictions.csv) · [Q3 全池](handoff/v1_2/q3_pool_predictions.csv) · [Q2 盲池](handoff/v1_2/q2_blind_predictions.csv) · [Q3 盲池](handoff/v1_2/q3_blind_predictions.csv) |
| 最终模型与预处理 | [Q1，02 拟合](handoff/v1/models/q1_final.joblib) · [Q2/Q3，02+03 拟合](handoff/v1/models/q23_final.joblib) · [V1.2 统一清单](handoff/manifest.json) |
| 实验与论文材料 | [原英文研究报告](experiments/q1_ablation_v1/REPORT.md) · [V1.2 英文补证、图表](experiments/q1_v12/REPORT.md) · [03 完整指标](experiments/q1_v12/model_comparison.csv) · [03 预测](experiments/q1_v12/validation_predictions_03.csv) |
| 稳定性与质量 | [新增稳定性](experiments/q1_v12/stability.csv) · [数据审计索引](audit/precheck_index.md) · [V1.2 验收](handoff/v1_2/ACCEPTANCE.md) · [私有 Git 源码快照](handoff/v1_2/q1_source.bundle) |

Q1 和 Q2/Q3 的模型结构相同，训练范围及版本标识各自独立。候选汇总表按 `pool` 选择分析范围，`source_pool` 为相同的兼容列，联合键为 `(pool,id)`。官方原始数据留在 `2026 APMCM Problem D/date`。[数据契约](DATA_CONTRACT.md)

## 复现 Q1

在项目根目录打开 PowerShell。测试过的环境为 Windows、Python 3.10.11 和 [固定依赖](requirements-baseline.txt)。已有 `.venv-q1` 时可从运行命令开始。

```powershell
uv venv --python 3.10 .venv-q1
uv pip install --python .venv-q1/Scripts/python.exe -r requirements-baseline.txt
$env:LOKY_MAX_CPU_COUNT = '1'
$q1Python = '.\.venv-q1\Scripts\python.exe'
& $q1Python -B -m unittest discover -s tests -v
New-Item -ItemType Directory -Force .local | Out-Null
& $q1Python -B -m audit.v12_acceptance --out .local/v12_acceptance.json
```

验收命令核对官方数据哈希、训练池隔离、已保存模型的逐行推理、预测表、补充指标和源码快照。未安装 `uv` 时，可以使用 Python 3.10 的 `py -3.10 -m venv .venv-q1`，并用 `.venv-q1\Scripts\python.exe -m pip install -r requirements-baseline.txt` 安装同一组依赖。

如需从训练开始复跑，选择新的输出目录。消融使用已随仓库提供的三种基线折外预测，前两条命令单独验证这份历史基线可复算。基线记录的输入哈希与 02 和分折哈希必须一致。

```powershell
& $q1Python -B -m q1.baselines --out-dir experiments/replay_baseline
& $q1Python -B -m audit.baseline_check --replay-dir experiments/replay_baseline
& $q1Python -B -m q1.experiments --out-dir experiments/replay_ablation
& $q1Python -B -m q1.delivery --cv-dir experiments/replay_ablation --out-dir handoff/replay_v1
& $q1Python -B -m audit.final_check --cv experiments/replay_ablation --release handoff/replay_v1
```

独立打分可使用任意官方格式成分 CSV。模型文件用 joblib 保存，加载本项目可信产物。

```powershell
& $q1Python -B -m q1.predict --model handoff/v1/models/q1_final.joblib --input '2026 APMCM Problem D/date/04_castelli_test_holdout.csv' --source-pool 04 --output handoff/replayed_04.csv
```

Python 接口为 `joblib.load(path)['model'].predict(composition)`，其中 `composition` 的三列为 A、B、X。图表使用 Matplotlib 3.10.3 与 NumPy 2.2.6 运行 `python -B -m audit.plot_phase1` 和 `python -B -m audit.plot_final`，输出 300 dpi PNG 和 SVG。

## V1.2 补证复现

```powershell
& $q1Python -B -m q1.v12_supplement --out-dir experiments/replay_q1_v12
& $q1Python -B -m q1.v12_handoff --out-dir handoff/replay_v1_2 --manifest handoff/replay_v1_2_manifest.json
```

`audit.v12_labels` 从 02、03 重建公开标签核对表。需要重画图时，可在虚拟环境额外安装 `matplotlib==3.10.3`，再运行 `python -B -m audit.plot_v12` 等绘图命令。Git 源码快照可通过 `git clone -c core.autocrlf=false -b q1-v1-2 handoff/v1_2/q1_source.bundle <new_directory>` 查看。快照包含源码、测试和固定依赖。

队员 B 的独立复核和下游签收仍待登记。04 交接 CSV 为队内格式，官方提交字段以竞赛平台为准。[V1.2 验收](handoff/v1_2/ACCEPTANCE.md) · [04 格式核对](audit/submission_format_check.md)
