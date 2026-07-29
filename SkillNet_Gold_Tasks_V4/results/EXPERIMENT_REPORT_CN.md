# SkillNet A/B/C 实验报告（Run 01）

## 实验设置

- 日期：2026-07-28 至 2026-07-29（Asia/Shanghai）
- 模型：`gpt-5.6-sol`
- 推理强度：`medium`
- Codex CLI：`0.146.0-alpha.3.1`
- 每组任务：21
- 正式预测：63（A/B/C 各 21）
- 并发：每组最多 3 个独立进程
- 隔离：每题使用独立 ephemeral 会话和临时只读候选工作区
- 共同输入：相同 46 个原子 Skills、相同题目、相同输出 schema
- A：46 个扁平 Skills，无部门分组，无 Graph
- B：46 个 Skills + 部门分组，无 Graph
- C：46 个 Skills + advisory `skill_relations.json`

Graph 只提供候选关系。Codex 仍需根据任务语义、Skill description、当前状态和阻塞条件自主选择路线；runner 不计算或强制执行路径。

## 总体结果

| 配置 | Functional Success | Clean Success | Skill F1 | Department F1 | Order Accuracy | Final Status | Route Choice | Constraint Violation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 52.38% | 47.62% | 87.68% | 97.14% | 91.10% | 95.24% | 52.38% | 52.38% |
| B | 52.38% | 52.38% | 88.11% | 98.10% | 92.64% | 90.48% | 66.67% | 47.62% |
| C | **57.14%** | **57.14%** | **89.36%** | **100.00%** | **99.05%** | 80.95% | **71.43%** | **42.86%** |

## 观察

1. C 的 Functional Success 为 12/21，A 和 B 均为 11/21。C 相比两组净增加 1 个成功任务（4.76 个百分点）。
2. C 在五个单部门目标题上达到 5/5；A 为 3/5，B 为 4/5。C 在 `GT03_PROC_GOAL` 上超过 A/B，并在 `GT04_TECH_GOAL`、`GT15_CROSS_SUPPLIER_CONTRACT_PO` 上与 B 同样成功。
3. 三组在跨部门题上的精确成功率均为 3/9。C 的跨部门 Skill F1 更高（98.25%），但更多任务被错误标记为 `blocked`，因此跨部门 final-status 准确率只有 55.56%。
4. 三组 no-tool 题均为 3/3，说明加入分组或 Graph 没有诱导 Codex 在明确不需要企业 Skill 时强行调用 Skill。
5. 三组特殊约束题仍是主要弱点。B/C 在供应商失败和无效发票场景中继续调用了冲突后的 Skill；三组在 build-or-buy 题中都重复调用了已完成的 `technology-requirement`。
6. C 将缺失必需 Skill 从 A 的 5 次、B 的 4 次降到 1 次，将顺序错误从 5/4 次降到 1 次；与此同时，C 的错误 final status 增加到 4 次。

## 运行异常与处理

最初的 smoke 测试发现 Codex Structured Outputs 不支持 `uniqueItems` 和开放键对象。修复后，A/B/C smoke 均一次生成有效英文 Skill 路线。

正式运行的 `C/GT07_CROSS_CUSTOM_TECH_SUPPLIER` 已生成有效预测，但 runner 在序列化 `TimeoutExpired` 的字节日志时崩溃，导致该题原始日志和 C manifest 未写入。该缺陷通过失败测试复现后修复。为避免在看到预测后重采样产生选择偏差，实验保留原 GT07 预测且不伪造缺失日志，因此正式包包含 63 个预测和 62 个原始日志。

故障发生后曾根据当时仍存在的临时目录误判 GT20 为故障题，并使用完全相同的模型、参数和候选工作区重跑 GT20。重跑前后的所有评分字段相同（均正确选择 no-tool），仅解释文字不同，因此不改变任何汇总指标。最后对 21 个 C 预测执行无模型 resume 校验并重建 manifest。

## 解释限制

- 每个配置只有一次 21 题运行，样本量不足以声称统计显著。
- 结果说明 advisory Graph 在本次样本中改善了 Skill 覆盖和顺序，但也可能让模型更容易推断额外阻塞或流程状态。
- 下一步应使用多个随机重复 run，并报告均值、方差、置信区间以及调用延迟/上下文开销。

原始预测位于 `predictions/{A,B,C}/run_01/`，逐题评分位于 `results/{A,B,C}_run_01/`，聚合文件位于 `results/summary/`。
