# 首次基线运行记录

2026-11-27。五折的 15 次拟合和预测均已完成，三个 CSV 已写出。导出 JSON 配置时，OneHotEncoder 的 dtype 参数仍为 Python 类型，触发 `TypeError: Object of type type is not JSON serializable`。

修复后将 dtype 以类型名保存，并改为先在临时目录写完四项产物再发布。首次运行的 CSV 保留用于复算对照。重跑的 11,256 行折外预测与首次 CSV 逐字节一致。[正式基线报告](../baseline_v1/REPORT.md)
