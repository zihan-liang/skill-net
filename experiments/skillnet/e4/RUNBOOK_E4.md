# SkillNet E4 模糊语言实验运行手册

E4 检验模型在用户只描述最少当前状态、高层目标和必要停止边界时，能否从同一份 46-Skill Catalogue 恢复 canonical GT01–GT21 的原子 Skill 路径。本目录只保存实验输入、语义审核和验证工具；实现与验证阶段不得启动正式模型实验。

## 冻结范围

- Experiment：`E4`
- Catalogue size：仅 `46`
- Configuration：`A`、`B`、`C`
- Tasks：canonical `GT01_SINGLE` 至 `GT21_NO_TOOL_PROC`，共 21 题
- 正式调用数：每个配置 21 个独立 child，共 63 次
- Prompt：A/B/C 共同读取 `experiments/skillnet/e4/prompts/`；配置不是 Prompt 变量
- Gold：直接使用 `SkillNet_Gold_Tasks_V4/02_Gold_Standard_21_V4.json`
- 输出 task ID：始终使用原始 `GTxx_*`，不得加 `E4-` 前缀
- Runtime：沿用 E0 的 Codex CLI、`gpt-5.6-sol`、`high` reasoning、prediction schema 与 artifact contract
- 禁止：size10、size30、父 Skill 展开、`--resume`、修复/补跑/替换模型答案

每题启动一个新的 `codex exec` 进程。Child 只看到当前一条 E4 中文任务、当前配置的唯一 Catalogue 和固定 JSON 输出契约；不会看到原 Prompt、Gold、semantic audit、其他题、其他 Catalogue、独立 relations 或历史结果。C 的关系只来自 C Catalogue 内嵌的 `relations`。

## Prompt 与关键语义清单

| Task | E4 中文 Prompt | 保留的关键语义 | 泄漏审核 |
|---|---|---|---|
| GT01 | 候选供应商名单已经整理好，这次只判断他们能不能获得本次采购的准入，询价、打分和定标都先不做。 | 已有候选名单；仅核验准入；停止于询价前 | PASS：无 Skill ID、正式流程名或步骤序列 |
| GT02 | 本月获批款项都已付清但尚未入账，管理层下周一要看到本月财务报表。 | 已付款、未入账；目标为月度报表 | PASS：未提示入账与报表顺序 |
| GT03 | 采购内容和预算均已确定，目前还没有候选方；请选出一家资质、价格和综合表现都合适的供应商，谈判、签约和下单暂不处理。 | 需求预算完成、无候选方；终点为选商；排除后续 | PASS：未枚举选商链路 |
| GT04 | 新功能需求已整理完成，请把它推进到具备开工条件的详细实施安排，实际开发先不要开始。 | 技术需求完成；终点为开发就绪计划；禁止实际开发 | PASS：未复述技术规划阶段 |
| GT05 | 潜在客户已在跟进，但需求、预算和交付预期都还不清楚；请判断是否值得继续，并在值得时拿出可供客户讨论的初步方案和价格，正式谈判与签约先不开始。 | 已有线索与信息缺口；条件性商机推进；止于谈判前 | PASS：未列商务流程名与顺序 |
| GT06 | 用人需求和招聘经费都已批准，但职位还没对外发布；请从市场获得申请并整理出可进入面试的候选名单，先不要约面或发录用通知。 | 岗位和预算已批、职位未发；终点为 shortlist；停止于约面前 | PASS：未列招聘中间步骤 |
| GT07 | 新客户只有一条跟进线索，想要一套必须配外部设备的定制技术方案，需求、规格、预算和供应来源都未确定；请把项目推进到方向明确且已有可用供货方，客户和供应商都先不签约，也先不下单。 | 客户线索起点；必须外采设备；四类信息缺口；止于可用供应商 | PASS：无部门清单或跨域 Skill 路径 |
| GT08 | 技术设备的订单已下，供应商称已送达并开了发票，目前只是采购侧开始跟进，设备还没经过技术人员确认；请在条件齐备后完成付款并入账。 | PO 完成、交付/发票已报告、尚未技术确认；technical acceptance route | PASS：未直接写验收 Skill 或后续顺序 |
| GT09 | 外购咨询服务已交付并收到发票，但业务负责人还未按约确认成果；若服务符合约定，请办妥付款并入账。 | 外购业务服务、尚未业务确认；business acceptance route | PASS：未直接写业务验收 Skill |
| GT10 | 新员工已接受录用，办公电脑也已下单，但电脑尚未送达，也未由技术人员确认可用；请在入职日前把办公条件准备好并完成员工资料归档。 | Offer accepted、PO 完成；技术设备交付/确认未完成；入职与员工记录终点 | PASS：未列交付验收与 HR 路径 |
| GT11 | 技术团队的招聘名额已批准且岗位标准明确，但经费还没确认；若预算允许，请完成招聘并向最终人选发出录用通知，入职先不办。 | 岗位已批准、标准明确、预算未定；终点为 Offer；停止于入职前 | PASS：未枚举预算与招聘链路 |
| GT12 | 只有一条潜在客户线索，项目交付明确依赖外部咨询服务，客户需求还没确认，预算和供应方也没有结论；请在确认值得做后把外部服务推进到可以正式下单。 | 客户线索起点；外部服务必需；需求/预算/供应方未定；终点为 PO | PASS：未透露 14-Skill 中间路径 |
| GT13 | 这个已识别的技术需求确定由内部团队开发，现有员工的技能和项目经历可查；请据此确认能否做成并形成可执行的人员任务分工，先不要开工。 | 技术需求完成；internal development；员工能力数据必需；止于开发前 | PASS：外采不再是合理路线，未列技术步骤 |
| GT14 | 采购物品已验收通过并收到发票，财务还没核对；请把款项处理并入账，同时将这次履约表现记入该供应商的后续评价。 | 交付已通过、发票未核；付款入账与供应商绩效双终点 | PASS：未泄漏付款后的偏序关系 |
| GT15 | 预算和供应商都定了，把这次采购推进到可以正式下单，先不用管交付。 | 预算与选商完成；终点为 PO；停止于交付前 | PASS：采用确认的合格示例，无中间步骤 |
| GT16 | 这次采购只有一家候选方，资质结论是不合格，业务负责人仍催着立即定下并出合同；请按规则处理并说明最终状态。 | 唯一候选方资质不合格；选商/合同请求必须阻断 | PASS：仅保留失败触发与冲突请求 |
| GT17 | 货物已验收通过，但发票被判定无效或与合同、订单对不上，供应商仍催着立刻付款；请按规则处理并说明最终状态。 | 交付通过；发票 invalid/mismatch；付款和入账必须阻断 | PASS：仅保留失败触发与冲突请求 |
| GT18 | 这个已识别的技术需求已经决定由内部团队完成，不得改走外部服务采购；请推进到内部成果完成测试把关为止。 | technical requirement completed；build/buy 互斥选 internal；终点为技术测试验收 | PASS：未列内部技术 Skill 链 |
| GT19 | 讲个轻松点的笑话吧。 | 普通闲聊，no-tool | PASS：无企业操作意图 |
| GT20 | 用大白话解释一下“预算检查”是什么意思，不要读取、分析或改动任何公司预算数据。 | 仅概念解释；排除公司数据操作，no-tool | PASS：关键词不是调用指令 |
| GT21 | 讲个采购部门的笑话就行，别真的替公司办采购。 | 仅玩笑；排除采购操作，no-tool | PASS：部门词不是企业流程请求 |

详细逐题人工记录位于 `E4_semantic_audit.json`。该记录覆盖 current state、high-level goal、stop boundary、unique route、blocked、mutex、acceptance route、no-tool、process-name leakage 和 ordered-step leakage。自动 validator 明确记录 `automatic_semantic_equivalence_proven: false`；人工审核不能由正则检查替代。

## Prompt 验证

在任何 fixture 或正式运行前执行：

```bash
PYTHONDONTWRITEBYTECODE=1 experiments/skillnet/.venv/bin/python \
  experiments/skillnet/e4/validate_e4_prompts.py
```

Validator 必须输出 GT01–GT21 的逐题表，21 项全部为 `PASS`，并以退出码 0 结束。它验证恰好 21 题、canonical task IDs、1–2 句中文、Skill/department ID 泄漏、实验化语言、箭头/编号/显式顺序、部门清单、正式中文 Skill 名顺序、Prompt/Gold/manifest hash、semantic contract hash、A/B/C 同源同 hash 和完整人工审核。

## Fixture-only 验证

Fixture 只能写入临时 `--state-root`。不得将 fixture 结果放入正式 `runs/E4` 或 `results/E4`，也不得在实现阶段使用 `--execute`。

```bash
PYTHONDONTWRITEBYTECODE=1 experiments/skillnet/.venv/bin/python \
  -m unittest experiments.skillnet.tests.test_e4_experiment -v
```

专项测试会用 21 个静态 response 验证完整 runner/verifier artifact contract，并验证 E4 verifier 直接使用 canonical 21-task Gold。

## 正式运行门禁

每个正式配置开始前检查：

1. 已切换到经用户批准的正式运行提交，工作树为空；
2. E4 validator 为 21/21 PASS；
3. 两套完整 unittest 均为绿色；
4. runtime 与 E0 冻结值一致；
5. canonical Gold、evaluator、prediction schema、size46 Catalogues、relations、Skills、E0 artifacts 和 E1 files 的 hash 无漂移；
6. 对应 `runs/E4/<configuration>/size_46/<run_id>` 与 `results/E4/...` 均不存在；
7. 同一 task 只允许一个 fresh child，不使用 `--resume`，不补跑或替换失败结果。

## 三个正式配置命令

下面命令留给后续经用户批准的正式运行对话。本次实现对话不得执行。

```bash
experiments/skillnet/.venv/bin/python experiments/skillnet/run_condition.py \
  --experiment E4 --configuration A --size 46 --run-id run_01 --execute

experiments/skillnet/.venv/bin/python experiments/skillnet/run_condition.py \
  --experiment E4 --configuration B --size 46 --run-id run_01 --execute

experiments/skillnet/.venv/bin/python experiments/skillnet/run_condition.py \
  --experiment E4 --configuration C --size 46 --run-id run_01 --execute
```

每个配置在 21 个 raw responses 均保存后单独验证：

```bash
experiments/skillnet/.venv/bin/python experiments/skillnet/verify_condition.py \
  --experiment E4 --configuration A --size 46 --run-id run_01

experiments/skillnet/.venv/bin/python experiments/skillnet/verify_condition.py \
  --experiment E4 --configuration B --size 46 --run-id run_01

experiments/skillnet/.venv/bin/python experiments/skillnet/verify_condition.py \
  --experiment E4 --configuration C --size 46 --run-id run_01
```

Invalid JSON 仍保留在 `raw_response.txt`，schema audit 记为 invalid，确定性 evaluator 按原规则评价；不得修复模型字段或另外生成替代 prediction。

## 输出与 E0 robustness comparison

正式运行与评价分别写入：

```text
experiments/skillnet/runs/E4/<A|B|C>/size_46/<run_id>/
experiments/skillnet/results/E4/<A|B|C>/size_46/<run_id>/
```

E4 verifier 除原 artifact contract 外，在每个配置 result root 写入 `e0_robustness_comparison.json`。固定 baseline 为：

- A：`E0/A/size_46/run_02`
- B：`E0/B/size_46/run_02`，明确禁止 patched non-formal 结果
- C：`E0/C/size_46/run_04`，明确排除权限失败的 `run_02`

比较包含 functional/clean success、Skill P/R/F1、department P/R/F1、required-order、final-status、route-choice、no-tool、blocked-flow、constraint violation rate、21 题成功状态变化和全部 failure tag 增减。`robustness_drop` 的正值统一表示 E4 比 E0 更差；constraint violation rate 因为 lower-is-better，方向已反转。报告只描述单次运行观察，不声称统计显著性。
