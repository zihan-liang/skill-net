# SkillNet Gold Tasks V4（21条，不含父Workflow）

> 本文件含Gold答案，只供团队审核和评估器使用，不可提供给被测试Codex。

## 评价规则说明

- `canonical_sequence`只是一个可行示例，不做完整序列相等比较。
- `hard_order_constraints`是本任务必须满足的强制偏序。
- 冲突、互斥和阻断直接写在每道题的`task_constraints`、`forbidden_skills`、`expected_blocked_by`和`expected_route_choice`中。
- 本版本不使用relations.json，也不计算Graph Validity Rate。

## GT01_SINGLE — 供应商资质核验
- 类别：single_skill
- 难度：easy
- Prompt：采购团队已经整理出一份候选供应商名单。现在只需要判断这些供应商是否具备参与本次采购的基本资质，不需要询价、评分或选择供应商。请给出应调用的 Skill。
- 必要部门：Procurement Agent
- 必要Skills：供应商资质检查
- 可选Skills：无
- 禁止Skills：无
- 初始状态：{"供应商搜索": {"status": "completed", "result": "success"}}
- 预期最终状态：completed
- 预期阻断来源：无
- 预期路线选择：{}
- 示例序列：供应商资质检查
- 强制偏序：
  - 无
- 任务级约束：[]
- Gold解释：这是唯一保留的单 Skill 基础检查；当前目标只涉及供应商资质核验。

## GT02_FIN_GOAL — 月末报表准备
- 类别：single_department_goal
- 难度：medium
- Prompt：本月所有已批准款项都已经支付，但还没有进入账务系统。管理层下周一需要查看本月财务报表。请规划财务部门接下来需要完成的工作。
- 必要部门：Finance Agent
- 必要Skills：账务处理、财务报表生成
- 可选Skills：无
- 禁止Skills：无
- 初始状态：{"付款审批": {"status": "completed", "result": "approved"}}
- 预期最终状态：completed
- 预期阻断来源：无
- 预期路线选择：{}
- 示例序列：账务处理 → 财务报表生成
- 强制偏序：
  - 账务处理 → 财务报表生成
- 任务级约束：[]
- Gold解释：付款完成后，应先完成账务处理，再生成财务报表。

## GT03_PROC_GOAL — 确定合格供应商
- 类别：single_department_goal
- 难度：medium
- Prompt：采购需求和预算已经确认。公司目前没有候选供应商，希望最终选出一家资质、价格和综合表现都合适的供应商；本任务暂时不需要谈判、签合同或生成采购订单。请规划采购部门需要调用的 Skills。
- 必要部门：Procurement Agent
- 必要Skills：供应商搜索、供应商资质检查、询价单生成、报价比较、供应商评分、供应商选择
- 可选Skills：供应商绩效评价
- 禁止Skills：商务谈判、合同生成、采购订单生成
- 初始状态：{"采购需求识别": {"status": "completed", "result": "success"}, "预算检查": {"status": "completed", "result": "approved"}}
- 预期最终状态：completed
- 预期阻断来源：无
- 预期路线选择：{}
- 示例序列：供应商搜索 → 供应商资质检查 → 询价单生成 → 报价比较 → 供应商评分 → 供应商选择
- 强制偏序：
  - 供应商搜索 → 供应商资质检查
  - 供应商资质检查 → 询价单生成
  - 询价单生成 → 报价比较
  - 报价比较 → 供应商评分
  - 供应商评分 → 供应商选择
- 任务级约束：[]
- Gold解释：任务目标截止于供应商选择，后续谈判、合同和订单均不应调用。

## GT04_TECH_GOAL — 形成可进入开发的方案
- 类别：single_department_goal
- 难度：medium
- Prompt：一个新功能的技术需求已经整理完成。公司希望判断它是否可行，并形成一份足以进入开发阶段的详细实施方案；本任务暂时不要真正开始开发。请规划技术部门需要调用的 Skills。
- 必要部门：Technology Agent
- 必要Skills：可行性评估、技术规格确认、技术方案设计、任务拆解
- 可选Skills：无
- 禁止Skills：开发或实施、技术测试验收、系统上线
- 初始状态：{"技术需求识别": {"status": "completed", "result": "success"}}
- 预期最终状态：completed
- 预期阻断来源：无
- 预期路线选择：{}
- 示例序列：可行性评估 → 技术规格确认 → 技术方案设计 → 任务拆解
- 强制偏序：
  - 可行性评估 → 技术规格确认
  - 技术规格确认 → 技术方案设计
  - 技术方案设计 → 任务拆解
- 任务级约束：[]
- Gold解释：目标是形成可执行方案并完成任务拆解，但不进入开发。

## GT05_BUS_GOAL — 判断商机并形成初步报价
- 类别：single_department_goal
- 难度：medium
- Prompt：一名潜在客户已经进入跟进名单，但需求、预算和交付预期仍不清楚。公司的目标是判断这个机会是否值得继续，并在值得推进时形成初步方案和报价；暂时不要进入正式谈判或签合同。
- 必要部门：Business Agent
- 必要Skills：客户需求沟通、商机评估、方案与报价
- 可选Skills：无
- 禁止Skills：商务谈判、合同签署
- 初始状态：{"客户线索管理": {"status": "completed", "result": "success"}}
- 预期最终状态：completed
- 预期阻断来源：无
- 预期路线选择：{}
- 示例序列：客户需求沟通 → 商机评估 → 方案与报价
- 强制偏序：
  - 客户需求沟通 → 商机评估
  - 商机评估 → 方案与报价
- 任务级约束：[]
- Gold解释：从已存在的客户线索出发，推进到方案与报价即停止。

## GT06_HR_GOAL — 形成面试候选人名单
- 类别：single_department_goal
- 难度：medium
- Prompt：一个岗位需求已经获得批准，招聘预算也已经通过，但职位尚未发布。公司希望从市场上收集申请并形成可以进入面试的候选人名单；本任务暂时不要安排面试或生成 Offer。
- 必要部门：HR Agent
- 必要Skills：JD生成、招聘发布、简历筛选
- 可选Skills：无
- 禁止Skills：面试安排、Offer生成、入职管理
- 初始状态：{"岗位需求": {"status": "completed", "result": "approved"}, "预算检查": {"status": "completed", "result": "recruitment_approved"}}
- 预期最终状态：completed
- 预期阻断来源：无
- 预期路线选择：{}
- 示例序列：JD生成 → 招聘发布 → 简历筛选
- 强制偏序：
  - JD生成 → 招聘发布
  - 招聘发布 → 简历筛选
- 任务级约束：[]
- Gold解释：预算和岗位需求已完成，从JD生成推进到简历筛选。

## GT07_CROSS_CUSTOM_TECH_SUPPLIER — 客户定制项目的供应商选择
- 类别：cross_department_goal
- 难度：hard
- Prompt：一名新客户希望公司交付一套定制技术解决方案，其中必须采购外部设备。目前只有客户线索，客户需求、技术规格、预算和供应商都尚未确认。公司的目标是在不签客户合同、不签供应合同、也不生成采购订单的前提下，确认项目方向并选出可用供应商。
- 必要部门：Business Agent、Technology Agent、Finance Agent、Procurement Agent
- 必要Skills：客户需求沟通、商机评估、方案与报价、技术需求识别、可行性评估、技术规格确认、采购需求识别、预算检查、供应商搜索、供应商资质检查、询价单生成、报价比较、供应商评分、供应商选择
- 可选Skills：无
- 禁止Skills：商务谈判、合同签署、合同生成、采购订单生成
- 初始状态：{"客户线索管理": {"status": "completed", "result": "success"}}
- 预期最终状态：completed
- 预期阻断来源：无
- 预期路线选择：{}
- 示例序列：客户需求沟通 → 商机评估 → 方案与报价 → 技术需求识别 → 可行性评估 → 技术规格确认 → 采购需求识别 → 预算检查 → 供应商搜索 → 供应商资质检查 → 询价单生成 → 报价比较 → 供应商评分 → 供应商选择
- 强制偏序：
  - 客户需求沟通 → 商机评估
  - 商机评估 → 方案与报价
  - 技术需求识别 → 可行性评估
  - 可行性评估 → 技术规格确认
  - 方案与报价 → 采购需求识别
  - 技术规格确认 → 采购需求识别
  - 采购需求识别 → 预算检查
  - 预算检查 → 供应商搜索
  - 供应商搜索 → 供应商资质检查
  - 供应商资质检查 → 询价单生成
  - 询价单生成 → 报价比较
  - 报价比较 → 供应商评分
  - 供应商评分 → 供应商选择
- 任务级约束：[]
- Gold解释：任务从客户机会出发，同时完成技术定义和外部采购准备，最终停在供应商选择。
- 评分备注：客户需求沟通对技术需求识别是增强关系，不强制唯一相邻顺序；但二者都属于本任务必要信息。

## GT08_CROSS_TECH_DELIVERY_PAYMENT — 技术设备交付后的付款与入账
- 类别：cross_department_goal
- 难度：hard
- Prompt：一套技术设备的采购订单已经生成，供应商报告设备已经送达并提交了发票。采购团队已经开始跟踪交付，但技术部门尚未验收。公司的最终目标是在所有必要条件满足后完成付款和入账。
- 必要部门：Procurement Agent、Technology Agent、Finance Agent
- 必要Skills：交付跟踪、技术测试验收、交付验收、发票核验、付款审批、账务处理
- 可选Skills：供应商绩效评价
- 禁止Skills：业务验收
- 初始状态：{"采购订单生成": {"status": "completed", "result": "success"}}
- 预期最终状态：completed
- 预期阻断来源：无
- 预期路线选择：{"acceptance_route": "technical_acceptance"}
- 示例序列：交付跟踪 → 技术测试验收 → 交付验收 → 发票核验 → 付款审批 → 账务处理
- 强制偏序：
  - 交付跟踪 → 技术测试验收
  - 技术测试验收 → 交付验收
  - 交付验收 → 发票核验
  - 发票核验 → 付款审批
  - 付款审批 → 账务处理
- 任务级约束：[{"type": "mutex_route", "decision_id": "acceptance_route", "expected_choice": "technical_acceptance", "forbidden_route_skills": ["业务验收"]}]
- Gold解释：技术产品必须经过技术测试验收和采购侧交付验收，之后才能进入财务付款。

## GT09_CROSS_BUS_SERVICE_PAYMENT — 业务服务验收后的付款
- 类别：cross_department_goal
- 难度：hard
- Prompt：公司采购的一项外部咨询服务已经完成交付，供应商也提交了发票。业务团队尚未正式确认交付成果。公司的目标是在服务符合约定的情况下完成付款和入账，本任务采用业务验收路线。
- 必要部门：Procurement Agent、Business Agent、Finance Agent
- 必要Skills：交付跟踪、业务验收、交付验收、发票核验、付款审批、账务处理
- 可选Skills：无
- 禁止Skills：技术测试验收
- 初始状态：{"采购订单生成": {"status": "completed", "result": "success"}}
- 预期最终状态：completed
- 预期阻断来源：无
- 预期路线选择：{"acceptance_route": "business_acceptance"}
- 示例序列：交付跟踪 → 业务验收 → 交付验收 → 发票核验 → 付款审批 → 账务处理
- 强制偏序：
  - 交付跟踪 → 业务验收
  - 业务验收 → 交付验收
  - 交付验收 → 发票核验
  - 发票核验 → 付款审批
  - 付款审批 → 账务处理
- 任务级约束：[{"type": "mutex_route", "decision_id": "acceptance_route", "expected_choice": "business_acceptance", "forbidden_route_skills": ["技术测试验收"]}]
- Gold解释：业务服务只采用业务验收主路线，不应同时选择技术测试验收。

## GT10_CROSS_ONBOARDING_EQUIPMENT — 新员工设备到位后的入职
- 类别：cross_department_goal
- 难度：hard
- Prompt：一名新员工已经接受 Offer，办公电脑的采购订单也已经生成。设备尚未完成交付和验收，员工也还没有正式办理入职。公司的目标是在入职日前让员工具备正常工作的条件，并完成员工信息归档。
- 必要部门：Procurement Agent、Technology Agent、HR Agent
- 必要Skills：交付跟踪、技术测试验收、交付验收、入职管理、员工数据库
- 可选Skills：无
- 禁止Skills：业务验收
- 初始状态：{"Offer生成": {"status": "completed", "result": "accepted"}, "采购订单生成": {"status": "completed", "result": "success"}}
- 预期最终状态：completed
- 预期阻断来源：无
- 预期路线选择：{"acceptance_route": "technical_acceptance"}
- 示例序列：交付跟踪 → 技术测试验收 → 交付验收 → 入职管理 → 员工数据库
- 强制偏序：
  - 交付跟踪 → 技术测试验收
  - 技术测试验收 → 交付验收
  - 交付验收 → 入职管理
  - 入职管理 → 员工数据库
- 任务级约束：[{"type": "mutex_route", "decision_id": "acceptance_route", "expected_choice": "technical_acceptance", "forbidden_route_skills": ["业务验收"]}]
- Gold解释：设备属于技术产品，先完成交付和技术验收，再办理入职并更新员工数据库。

## GT11_CROSS_RECRUIT_BUDGET_OFFER — 招聘预算确认后完成 Offer
- 类别：cross_department_goal
- 难度：hard
- Prompt：技术团队提出的岗位需求已经获得审批，岗位标准也已明确，但招聘预算尚未确认。公司希望在预算允许的情况下完成招聘并向最终候选人发出 Offer；暂时不办理入职。
- 必要部门：HR Agent、Finance Agent
- 必要Skills：预算检查、JD生成、招聘发布、简历筛选、面试安排、Offer生成
- 可选Skills：无
- 禁止Skills：入职管理
- 初始状态：{"岗位需求": {"status": "completed", "result": "approved"}}
- 预期最终状态：completed
- 预期阻断来源：无
- 预期路线选择：{}
- 示例序列：预算检查 → JD生成 → 招聘发布 → 简历筛选 → 面试安排 → Offer生成
- 强制偏序：
  - 预算检查 → JD生成
  - JD生成 → 招聘发布
  - 招聘发布 → 简历筛选
  - 简历筛选 → 面试安排
  - 面试安排 → Offer生成
- 任务级约束：[]
- Gold解释：岗位需求已完成且已审批，因此输出应从预算检查开始；预算通过后继续JD、发布、筛选、面试和Offer。

## GT12_CROSS_BUSINESS_TO_PO — 依赖外部服务的客户项目采购订单
- 类别：cross_department_goal
- 难度：hard
- Prompt：一个潜在客户线索已经进入跟进名单，该项目的交付需要购买外部业务服务。目前客户需求尚未充分确认，也没有供应商和预算结论。公司的目标是在确认商机可行后，为所需外部服务选出供应商、完成谈判和供应合同，并生成采购订单。
- 必要部门：Business Agent、Finance Agent、Procurement Agent
- 必要Skills：客户需求沟通、商机评估、方案与报价、采购需求识别、预算检查、供应商搜索、供应商资质检查、询价单生成、报价比较、供应商评分、供应商选择、商务谈判、合同生成、采购订单生成
- 可选Skills：供应商绩效评价
- 禁止Skills：无
- 初始状态：{"客户线索管理": {"status": "completed", "result": "success"}}
- 预期最终状态：completed
- 预期阻断来源：无
- 预期路线选择：{}
- 示例序列：客户需求沟通 → 商机评估 → 方案与报价 → 采购需求识别 → 预算检查 → 供应商搜索 → 供应商资质检查 → 询价单生成 → 报价比较 → 供应商评分 → 供应商选择 → 商务谈判 → 合同生成 → 采购订单生成
- 强制偏序：
  - 客户需求沟通 → 商机评估
  - 商机评估 → 方案与报价
  - 方案与报价 → 采购需求识别
  - 采购需求识别 → 预算检查
  - 预算检查 → 供应商搜索
  - 供应商搜索 → 供应商资质检查
  - 供应商资质检查 → 询价单生成
  - 询价单生成 → 报价比较
  - 报价比较 → 供应商评分
  - 供应商评分 → 供应商选择
  - 方案与报价 → 商务谈判
  - 供应商选择 → 商务谈判
  - 商务谈判 → 合同生成
  - 合同生成 → 采购订单生成
- 任务级约束：[]
- Gold解释：客户方案触发外部采购，供应商选择和方案信息共同支持谈判、合同和采购订单。

## GT13_CROSS_INTERNAL_DEV_STAFF_DATA — 利用员工能力数据完成技术任务拆解
- 类别：cross_department_goal
- 难度：hard
- Prompt：公司已经决定对一个技术需求采用内部开发。技术需求已识别，现有员工技能和项目经验数据可用。公司希望先确认可行性，并利用员工能力信息形成可执行的技术任务分工；本任务暂时不要开始开发。
- 必要部门：Technology Agent、HR Agent
- 必要Skills：可行性评估、技术规格确认、技术方案设计、员工数据库、任务拆解
- 可选Skills：无
- 禁止Skills：开发或实施、采购需求识别
- 初始状态：{"技术需求识别": {"status": "completed", "result": "success"}}
- 预期最终状态：completed
- 预期阻断来源：无
- 预期路线选择：{"build_or_buy": "internal_development"}
- 示例序列：可行性评估 → 技术规格确认 → 技术方案设计 → 员工数据库 → 任务拆解
- 强制偏序：
  - 可行性评估 → 技术规格确认
  - 技术规格确认 → 技术方案设计
  - 技术方案设计 → 任务拆解
  - 员工数据库 → 任务拆解（任务明确要求）
- 任务级约束：[{"type": "mutex_route", "decision_id": "build_or_buy", "expected_choice": "internal_development", "forbidden_route_skills": ["采购需求识别"]}]
- Gold解释：员工数据库通常只是增强任务拆解，但本任务明确要求利用员工能力信息，因此将其作为任务必要输入。
- 评分备注：员工数据库→任务拆解来自增强关系；本题因用户明确要求使用员工能力数据，将其升级为任务级必要条件。

## GT14_CROSS_PAYMENT_PERFORMANCE — 付款入账并更新供应商绩效
- 类别：cross_department_goal
- 难度：medium
- Prompt：一批采购物品已经完成交付验收，供应商提交了发票，但财务尚未核验。公司希望完成付款和入账，同时把本次履约表现纳入供应商评价。
- 必要部门：Finance Agent、Procurement Agent
- 必要Skills：发票核验、付款审批、账务处理、供应商绩效评价
- 可选Skills：无
- 禁止Skills：无
- 初始状态：{"交付验收": {"status": "completed", "result": "passed"}}
- 预期最终状态：completed
- 预期阻断来源：无
- 预期路线选择：{}
- 示例序列：发票核验 → 付款审批 → 账务处理 → 供应商绩效评价
- 强制偏序：
  - 发票核验 → 付款审批
  - 付款审批 → 账务处理
  - 付款审批 → 供应商绩效评价
- 任务级约束：[]
- Gold解释：付款审批后既可进入账务处理，也可更新供应商绩效，二者不必规定唯一先后。

## GT15_CROSS_SUPPLIER_CONTRACT_PO — 完成供应商合同和采购订单
- 类别：cross_department_goal
- 难度：medium
- Prompt：预算已经通过，供应商也已经完成评分并被正式选中。公司的目标是完成与供应商的商务谈判、形成供应合同并生成采购订单；本任务暂时不需要跟踪交付。
- 必要部门：Procurement Agent、Business Agent
- 必要Skills：商务谈判、合同生成、采购订单生成
- 可选Skills：无
- 禁止Skills：交付跟踪
- 初始状态：{"预算检查": {"status": "completed", "result": "approved"}, "供应商选择": {"status": "completed", "result": "success"}}
- 预期最终状态：completed
- 预期阻断来源：无
- 预期路线选择：{}
- 示例序列：商务谈判 → 合同生成 → 采购订单生成
- 强制偏序：
  - 商务谈判 → 合同生成
  - 合同生成 → 采购订单生成
- 任务级约束：[]
- Gold解释：供应商选择完成后进入商务谈判，再形成采购合同和采购订单。

## GT16_SPECIAL_SUPPLIER_FAIL — 不合格供应商要求继续签约
- 类别：special_constraint
- 难度：hard
- Prompt：某次采购只有一家候选供应商。资质检查结果显示该供应商不合格，但业务负责人仍要求立即确定该供应商并生成合同。请判断系统应如何处理，并给出最终状态。
- 必要部门：Procurement Agent
- 必要Skills：无
- 可选Skills：无
- 禁止Skills：供应商选择、合同生成
- 初始状态：{"供应商资质检查": {"status": "completed", "result": "unqualified"}}
- 预期最终状态：blocked
- 预期阻断来源：供应商资质检查
- 预期路线选择：{}
- 示例序列：无
- 强制偏序：
  - 无
- 任务级约束：[{"type": "conflict_block", "trigger_skill": "供应商资质检查", "trigger_results": ["unqualified"], "blocked_skills": ["供应商选择", "合同生成"]}]
- Gold解释：供应商资质检查不合格会同时阻止供应商选择和合同生成。
- 评分备注：正确答案可以没有新增执行Skill，但必须返回blocked，且不得调用两个被阻止的Skill。

## GT17_SPECIAL_INVALID_INVOICE — 无效发票要求付款
- 类别：special_constraint
- 难度：hard
- Prompt：采购物品已经通过交付验收，但发票核验结果显示发票无效或与合同、订单不匹配。供应商仍要求立即付款。请判断系统应如何处理，并给出最终状态。
- 必要部门：Finance Agent
- 必要Skills：无
- 可选Skills：无
- 禁止Skills：付款审批、账务处理
- 初始状态：{"交付验收": {"status": "completed", "result": "passed"}, "发票核验": {"status": "completed", "result": "invalid"}}
- 预期最终状态：blocked
- 预期阻断来源：发票核验
- 预期路线选择：{}
- 示例序列：无
- 强制偏序：
  - 无
- 任务级约束：[{"type": "conflict_block", "trigger_skill": "发票核验", "trigger_results": ["invalid", "mismatch"], "blocked_skills": ["付款审批", "账务处理"]}]
- Gold解释：发票核验失败会阻止付款审批，账务处理也不应继续。
- 评分备注：正确答案可以没有新增执行Skill，但必须明确阻止付款审批。

## GT18_SPECIAL_BUILD_OR_BUY — 内部开发与外部采购互斥选择
- 类别：special_constraint
- 难度：hard
- Prompt：公司已经决定对同一个技术需求采用内部开发，不能再采购外部技术服务。技术需求已经识别，目标是完成到技术测试验收为止的内部开发路线。请规划应调用的 Skills。
- 必要部门：Technology Agent
- 必要Skills：可行性评估、技术规格确认、技术方案设计、任务拆解、开发或实施、技术测试验收
- 可选Skills：无
- 禁止Skills：采购需求识别
- 初始状态：{"技术需求识别": {"status": "completed", "result": "success"}}
- 预期最终状态：completed
- 预期阻断来源：无
- 预期路线选择：{"build_or_buy": "internal_development"}
- 示例序列：可行性评估 → 技术规格确认 → 技术方案设计 → 任务拆解 → 开发或实施 → 技术测试验收
- 强制偏序：
  - 可行性评估 → 技术规格确认
  - 技术规格确认 → 技术方案设计
  - 技术方案设计 → 任务拆解
  - 任务拆解 → 开发或实施
  - 开发或实施 → 技术测试验收
- 任务级约束：[{"type": "mutex_route", "decision_id": "build_or_buy", "expected_choice": "internal_development", "forbidden_route_skills": ["采购需求识别"]}]
- Gold解释：同一技术需求已经选择内部开发，因此不得再进入采购需求识别路线。

## GT19_NO_TOOL_CLEAR — 普通闲聊
- 类别：no_tool
- 难度：easy
- Prompt：给我讲一个轻松的笑话。
- 必要部门：无
- 必要Skills：无
- 可选Skills：无
- 禁止Skills：ALL_BUSINESS_SKILLS
- 初始状态：{}
- 预期最终状态：no_tool
- 预期阻断来源：无
- 预期路线选择：{}
- 示例序列：无
- 强制偏序：
  - 无
- 任务级约束：[]
- Gold解释：普通对话，不需要调用任何企业Skill。

## GT20_NO_TOOL_FINANCE — 带财务关键词的概念解释
- 类别：no_tool
- 难度：medium
- Prompt：请用简单语言解释“预算检查”是什么意思，不要读取、分析或修改公司的任何预算数据。
- 必要部门：无
- 必要Skills：无
- 可选Skills：无
- 禁止Skills：ALL_BUSINESS_SKILLS
- 初始状态：{}
- 预期最终状态：no_tool
- 预期阻断来源：无
- 预期路线选择：{}
- 示例序列：无
- 强制偏序：
  - 无
- 任务级约束：[]
- Gold解释：用户只要求概念解释，并明确不处理公司数据。

## GT21_NO_TOOL_PROC — 带采购关键词的玩笑
- 类别：no_tool
- 难度：medium
- Prompt：给我讲一个关于采购部门的笑话，不需要执行任何采购流程。
- 必要部门：无
- 必要Skills：无
- 可选Skills：无
- 禁止Skills：ALL_BUSINESS_SKILLS
- 初始状态：{}
- 预期最终状态：no_tool
- 预期阻断来源：无
- 预期路线选择：{}
- 示例序列：无
- 强制偏序：
  - 无
- 任务级约束：[]
- Gold解释：虽然出现采购关键词，但不应触发采购Skill。
