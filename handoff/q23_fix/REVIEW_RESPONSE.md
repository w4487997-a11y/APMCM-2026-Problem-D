# 复审意见回复（三条逐项）

复审结论：有条件通过；Q3 求解问题已由复审方在 1.4.3 授权环境解决（4,800 样本，三组 104 位模型覆盖全部 8,112 候选，O3 28/30、NO2 23/30、Q2 23/30 种子命中）。本轮按复审要求补三件事。

---

## 一、接通复跑入口

### 1.1 字段不匹配已修

旧包的 `sdk_ising_q2.npz` 用 `qubo_offset / legal_left / legal_right`，求解脚本读 `offset / left_idx / right_idx`，直接传会 `KeyError: 'offset'`（复审复现的正是这条）。

修复：`scripts/common.py` 新增 `load_matrix()`，接受 `qubo|Q`、`offset|qubo_offset|constant`、`left_idx|legal_left`、`right_idx|legal_right` 等别名；`stage6_sdk_solve.py` 改用它。验证：旧 Q2 矩阵现在可以正常读入，只在缺 license 处停下（`logs/sdk_license_block.log` 为证）。

### 1.2 Q2 的 NO2 路径

```bash
python scripts/stage7_entry.py --problem q2 --iters 300 --alpha 0.99
```

- 从预测表现场重建 104 位模型（A 独热 + B 独热，NO2 固定），不依赖任何旧 npz；
- 求解后逐样本独立解码，回查原尺度 V̂；
- 本机（本地退火后端）实测：**合法 300/300，最佳 V̂ = 1.491928 = 全池枚举最优**，至少命中一次的种子 6/30（20.0%），样本命中 8/300（2.7%）。

### 1.3 Q3 三组求解 + 原尺度比较

```bash
python scripts/stage7_entry.py --problem q3 --iters 300 --alpha 0.99
```

三组各 104 位，分别求解后按**原尺度 V̂** 比较组间最优，结论自动输出：

| 组 | 变量 | 合法样本 | 样本命中 | 种子命中 | 组内最优 |
|---|---|---|---|---|---|
| O3 | 104 | 300/300 | 24/300 (8.0%) | **18/30 (60.0%)** | Na–Nb–O3 0.540023 |
| NO2 | 104 | 300/300 | 20/300 (6.7%) | **18/30 (60.0%)** | Y–Ti–NO2 1.491928 |
| FO2 | 104 | 300/300 | 27/300 (9.0%) | **15/30 (50.0%)** | Na–Ti–FO2 0.878526 |

组间比较：**O3 0.540023 < FO2 0.878526 < NO2 1.491928 → Na–Nb–O3**（与浮点全池枚举一致）。

`scripts/stage7_entry.py --problem all` 一条命令跑完 Q2 + Q3 并写统一表 `results/entry_*_table.csv`。

---

## 二、候选校验接入生成流程

`stage7_entry.validate_strict()` 在建矩阵**之前**强制对齐官方池：

| 检查项 | 依据 |
|---|---|
| 行数 = 官方池行数 | `task_a/data_real/07_*.csv`、`08_*.csv`（含 sha256） |
| ID 集合完全一致 | 缺行、池外 ID 都会被点名列出 |
| 每个 ID 的 (A,B,X) 与官方一致 | 错误组成直接拒绝 |
| `pool` 字段 = 对应池标签 | 错误来源池拒绝 |
| 重复 ID、非有限分数、负分、版本混用、常量表 | 均拒绝 |

负例测试（`scripts/stage8_negative_validation.py`，结果 `results/stage8_negative_validation.json`）：
**Q2、Q3 各 9 类注入缺陷全部被拒绝**，其中包含复审点名的三类：

| 注入 | Q2 | Q3 |
|---|---|---|
| 池外 ID | 拒绝（缺失官方候选 1 个 / 池外 id 1 个） | 拒绝 |
| 错误组成 | 拒绝（id 7 组成与官方不一致） | 拒绝（id 1 组成与官方不一致） |
| 错误来源池 | 拒绝（来源池字段不符 {07,08}） | 拒绝 |

**换模型时的做法**：最终 Q1 的 02+03 重训预测到位后，直接
`python scripts/stage7_entry.py --problem all --pred <新表.csv>`，
入口先校验再重建矩阵、求解、出比较表，不需要改代码或手工改字段。

---

## 三、更新论文证据

### 3.1 两套证据必须分开写

| 来源 | 环境 | 样本量 | 用途 |
|---|---|---|---|
| **Kaiwu SDK（复审方环境）** | 1.4.3 授权本地 CPU | 4,800 | 论文中的“SDK 求解结果” |
| **本地退火（本工作）** | 自写 SA，非 SDK | 1,200 | 只用于编码/预算敏感性分析，不能称作 SDK 结果 |

本机仍无 license，故本轮**没有新的 SDK 或真机结果**；表中 SDK 数字归复审方环境。

### 3.2 两个口径分列

复审指出“42%~79%”是样本命中率，应同时给种子口径。现统一为：

| 模型（本地退火 it=300, α=0.99） | 合法样本比例 | 样本命中率 | 至少命中一次的种子比例 |
|---|---|---|---|
| Q2 NO2 | 300/300 = 100% | 8/300 = 2.7% | 6/30 = 20.0% |
| Q3 O3 | 300/300 = 100% | 24/300 = 8.0% | 18/30 = 60.0% |
| Q3 NO2 | 300/300 = 100% | 20/300 = 6.7% | 18/30 = 60.0% |
| Q3 FO2 | 300/300 = 100% | 27/300 = 9.0% | 15/30 = 50.0% |

复审方 Kaiwu 结果按种子口径记录：O3 28/30、NO2 23/30、Q2 23/30；三者返回的最优分别为
Na–Nb–O3 0.540023、Y–Ti–NO2 1.491928、Y–Ti–NO2 1.491928（与枚举一致）。

### 3.3 仍不能写入论文的

- 新方案的真机结果：无；
- 加速比：无（本地 CPU 退火，且 2,704/8,112 全枚举成本远低于任何调度开销）；
- 全池 Q3 8 位直解：仍不可用（并列 21/24 + 非法反超反例，见 `stage2`）。

---

## 四、复现清单

```bash
python scripts/stage1_sdk_ising.py           # SDK 建模 + Ising 转换（真实 SDK）
python scripts/stage2_quant_partition.py     # 量化并列数、反例、三组分区模型
python scripts/stage3_hitrate_fix.py         # 命中率根因与预算扫描（本地）
python scripts/stage4_summarize_sdk_samples.py
python scripts/stage5_intake.py
python scripts/stage7_entry.py --problem all --iters 300 --alpha 0.99   # 正式入口
python scripts/stage8_negative_validation.py  # 9 类负例
python scripts/stage6_sdk_solve.py --npz <matrix.npz> ...  # 需 license
```

所有矩阵、输入表与结果文件哈希见 `MANIFEST.json`。
