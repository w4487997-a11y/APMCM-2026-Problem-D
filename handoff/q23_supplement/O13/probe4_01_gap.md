# probe4_01 凭证缺口说明（O-13 / P0-06）

## 结论

`probe4_01` 属于**台账有记录、原始回执缺失**的历史任务，标 `UNVERIFIED`。论文正文只写
“7 次优化任务共扣 7 次额度”，**不单列该探针**。

## 已知信息（有间接证据）

| 项 | 值 | 证据 |
|---|---|---|
| 任务名 | `probe4_01_01` | 平台任务列表截图 `O13/evidence/credits_after_2026-11-28.png` |
| 上传文件名 | `probe_upper.csv` | 同上 |
| 状态 | 已完成 | 同上 |
| 设备 | SPQC-550 | 同上 |
| 额度 | 1 次（总 7 次之一） | `O13/results/credits_ledger.csv`；31 → 24 = 7 次 |

## 缺失字段（无法从本仓库恢复）

- 任务 ID
- 上传矩阵原文及 SHA-256（本地也未找到 `probe_upper.csv`；仅 sdk 依赖里同名 `probe.py`，无关）
- 原始返回（样本向量、quboValue/能量）
- 创建时间、结束时间、单次演化时长
- 平台任务详情页截图（列表截图只含任务名/文件名/状态/设备）

## 已查范围

1. `O13/receipts/`：6 份导出（4 个 104 变量任务 + 2 个历史短名单），无 probe；
2. `O13/results/`：`o13_results.json`、`o13_summary.csv`、`samples_*.csv`、`credits_*`，均无 probe；
3. `O13/evidence/`：12 张截图，仅任务列表行可见 probe；
4. 工作区 `q23_fix/`、`q23_supplement/`、`task_a/`：未找到 `probe_upper.csv` 或 probe 结果日志；
5. GitHub 仓库历史：`handoff/q23_supplement/` 与 `handoff/q23_fix/` 均无 probe 原始回执。

## 补交方式（需平台操作）

1. 在平台历史任务中找到 `probe4_01_01`，进入详情页；
2. 导出或截图：任务 ID、创建/结束时间、单次演化时长、输出解向量（含 quboValue）；
3. 若平台仍保留上传文件，一并下载 `probe_upper.csv` 并计算 SHA-256；
4. 放入 `O13/receipts/probe4_01.log`（或 `.png` 到 `O13/evidence/`），
   更新 `receipt_template.csv` 的对应行与 `o13_manifest.json`。

## 若另做探针

必须**新任务 ID、新额度记录**，不得与本次 7 次混记；在 `credits_ledger.csv` 新增一行，
并注明“补做探针”。
