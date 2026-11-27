# D-00 前置可行性验证 · 交付包

生成时间：2026-11-26 17:59　·　数据：官方附件（9 个文件 sha256 全匹配）

## 1 目录

```
deliverable/
├── code/           审计、自检、建模、矩阵、报告脚本
├── results/        审计 JSON、基线指标、池预测、矩阵元数据、运行日志
├── matrices/       qubo_q2.npz / qubo_q3.npz
├── reports/        任务 A 数据审计报告、前置可行性验证结论
├── data_sha256.txt 数据文件哈希（与官方清单一致）
└── README.md
```

## 2 结论摘要

- 数据审计：41 项，PASS 41，FAIL 0，PENDING 0 → **PASS**
- 反向自检：植入 6 类缺陷，6/6 被捕获（results/selftest_negative.txt）
- 基础代理（02 训练 / 03 验证，仅 A、B、X）：
  - 中位数基线 MAE 7.80
  - 岭回归 MAE 4.47，Low-10% MAE 5.51，Top-25 重合 0.16
  - 随机森林 MAE 4.21，Low-10% MAE 5.36，Top-25 重合 0.08
- V 分位数（02）：min 0.000400，1% 1.6129，5% 12.0412
  ；（03）：min 0.019600，1% 1.9878，5% 11.9541
- 真实代理矩阵：Q2 104 变量 / 2,704 候选，Q3 208 变量 / 8,112 候选，
  能量与缩放代价偏差 0e+00 / 0e+00
- 代理目标最优：Q2 = ['La', 'Ti']（V̂ 4.1466）；
  Q3 = ['La', 'Ti', 'O3']（V̂ 2.6164）

## 3 运行环境

| 环境 | 版本 | 用途 |
|---|---|---|
| Python（bundled） | 3.12.14 | 审计、文档生成 |
| numpy / pandas / python-docx | 2.3.5 / 3.0.1 / 1.2.0 | 同上 |
| Python（venv-mirna） | 3.12.14 | 需要 sklearn 的任务 |
| scikit-learn / scipy | 1.9.1 / 1.18.1 | 基线模型、矩阵构建 |

## 4 运行命令

```bash
# 1 数据审计（41 项）
python task_a/task_a_audit.py --data-dir task_a/data_real --out task_a/audit_result.json
python task_a/build_audit_report.py --json task_a/audit_result.json --out task_a/任务A_数据审计报告.docx

# 2 反向自检（植入 6 类缺陷）
python task_a/selftest_negative.py

# 3 基础代理模型（B1）
venv-mirna/Scripts/python.exe task_a/train_baseline.py

# 4 真实代理 -> QUBO 矩阵（B2 + D1 + 交付）
venv-mirna/Scripts/python.exe task_a/build_matrices.py

# 5 编码验证（16 / 256 状态 + 占位池）
python task_a/verify_qubo.py

# 6 结论文档
python task_a/build_verdict.py
```

## 5 已知边界

1. 19 条正例是否全在 04：本地只能验证 02/03 为 0，属推断而非观测。
2. 代理模型 Top-25 重合率仅 0.16（岭回归），说明“仅组成特征”的基线排序能力有限，正式建模需要更强特征或模型。
3. 未做 Kaiwu SDK、量化与真机测试，矩阵未考虑硬件系数精度。
4. A = B 候选按题面要求保留，未做任何删除。
