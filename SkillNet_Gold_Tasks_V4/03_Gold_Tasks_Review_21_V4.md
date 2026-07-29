# SkillNet Gold Tasks V4 — Bilingual Review

## English review

This review is generated from the same Gold data used by the evaluator. Machine-readable
Skill and department fields use exact canonical IDs from `main`.

| Task | English title | Category | Status | Required departments | Required Skills |
|---|---|---|---|---|---:|
| `GT01_SINGLE` | Supplier Qualification Verification | `single_skill` | `completed` | `procurement-agent` | 1 |
| `GT02_FIN_GOAL` | Month-End Financial Statement Preparation | `single_department_goal` | `completed` | `finance-agent` | 2 |
| `GT03_PROC_GOAL` | Select a Qualified Supplier | `single_department_goal` | `completed` | `procurement-agent` | 6 |
| `GT04_TECH_GOAL` | Prepare a Solution Ready for Development | `single_department_goal` | `completed` | `technology-agent` | 4 |
| `GT05_BUS_GOAL` | Assess an Opportunity and Prepare a Preliminary Quotation | `single_department_goal` | `completed` | `business-agent` | 3 |
| `GT06_HR_GOAL` | Produce an Interview Candidate Shortlist | `single_department_goal` | `completed` | `hr-agent` | 3 |
| `GT07_CROSS_CUSTOM_TECH_SUPPLIER` | Select a Supplier for a Custom Technical Project | `cross_department_goal` | `completed` | `business-agent`, `technology-agent`, `finance-agent`, `procurement-agent` | 14 |
| `GT08_CROSS_TECH_DELIVERY_PAYMENT` | Pay and Account for Delivered Technical Equipment | `cross_department_goal` | `completed` | `procurement-agent`, `technology-agent`, `finance-agent` | 6 |
| `GT09_CROSS_BUS_SERVICE_PAYMENT` | Pay after Business-Service Acceptance | `cross_department_goal` | `completed` | `procurement-agent`, `business-agent`, `finance-agent` | 6 |
| `GT10_CROSS_ONBOARDING_EQUIPMENT` | Onboard an Employee after Equipment Is Ready | `cross_department_goal` | `completed` | `procurement-agent`, `technology-agent`, `hr-agent` | 5 |
| `GT11_CROSS_RECRUIT_BUDGET_OFFER` | Complete an Offer after Recruitment Budget Confirmation | `cross_department_goal` | `completed` | `hr-agent`, `finance-agent` | 6 |
| `GT12_CROSS_BUSINESS_TO_PO` | Generate a Purchase Order for a Customer Project Requiring an External Service | `cross_department_goal` | `completed` | `business-agent`, `finance-agent`, `procurement-agent` | 14 |
| `GT13_CROSS_INTERNAL_DEV_STAFF_DATA` | Use Employee Capability Data to Complete Technical Task Breakdown | `cross_department_goal` | `completed` | `technology-agent`, `hr-agent` | 5 |
| `GT14_CROSS_PAYMENT_PERFORMANCE` | Complete Payment and Accounting and Update Supplier Performance | `cross_department_goal` | `completed` | `finance-agent`, `procurement-agent` | 4 |
| `GT15_CROSS_SUPPLIER_CONTRACT_PO` | Complete a Supplier Contract and Purchase Order | `cross_department_goal` | `completed` | `procurement-agent`, `business-agent` | 3 |
| `GT16_SPECIAL_SUPPLIER_FAIL` | Block Contracting with an Unqualified Supplier | `special_constraint` | `blocked` | `procurement-agent` | 0 |
| `GT17_SPECIAL_INVALID_INVOICE` | Block Payment for an Invalid Invoice | `special_constraint` | `blocked` | `finance-agent` | 0 |
| `GT18_SPECIAL_BUILD_OR_BUY` | Choose the Internal-Build Route under Build-or-Buy Mutual Exclusion | `special_constraint` | `completed` | `technology-agent` | 6 |
| `GT19_NO_TOOL_CLEAR` | Casual Conversation | `no_tool` | `no_tool` | — | 0 |
| `GT20_NO_TOOL_FINANCE` | Concept Explanation with a Finance Keyword | `no_tool` | `no_tool` | — | 0 |
| `GT21_NO_TOOL_PROC` | Joke with a Procurement Keyword | `no_tool` | `no_tool` | — | 0 |

### GT01_SINGLE — Supplier Qualification Verification / 供应商资质核验

**English prompt:** The procurement team has compiled a list of supplier candidates. Determine only whether these suppliers have the basic qualifications to participate in this procurement. Do not request quotations, score suppliers, or select a supplier. Return the Skill that should be invoked.

**中文任务：** 采购团队已经整理出一份候选供应商名单。现在只需要判断这些供应商是否具备参与本次采购的基本资质，不需要询价、评分或选择供应商。请给出应调用的 Skill。

**Required Skill IDs:** `procurement-supplier-qualification`

**Optional Skill IDs:** None

**Forbidden Skill IDs:** None

**Forbid all Skills:** `false`

**Gold rationale (EN):** This is the only retained single-Skill basic check; the current objective is limited to supplier qualification.

**Gold 理由（中文）：** 这是唯一保留的单 Skill 基础检查；当前目标只涉及供应商资质核验。

### GT02_FIN_GOAL — Month-End Financial Statement Preparation / 月末报表准备

**English prompt:** All approved payments for this month have been paid, but they have not yet been posted to the accounting system. Management needs to review this month's financial statements next Monday. Plan the work the finance department must complete next.

**中文任务：** 本月所有已批准款项都已经支付，但还没有进入账务系统。管理层下周一需要查看本月财务报表。请规划财务部门接下来需要完成的工作。

**Required Skill IDs:** `finance-accounting`, `finance-reporting`

**Optional Skill IDs:** None

**Forbidden Skill IDs:** None

**Forbid all Skills:** `false`

**Gold rationale (EN):** After payment is complete, accounting must be performed before the financial statements are generated.

**Gold 理由（中文）：** 付款完成后，应先完成账务处理，再生成财务报表。

### GT03_PROC_GOAL — Select a Qualified Supplier / 确定合格供应商

**English prompt:** The procurement requirement and budget have been confirmed. The company currently has no supplier candidates and wants to select a supplier with suitable qualifications, pricing, and overall performance. This task does not yet require negotiation, contract signing, or purchase-order generation. Plan the Skills the procurement department must invoke.

**中文任务：** 采购需求和预算已经确认。公司目前没有候选供应商，希望最终选出一家资质、价格和综合表现都合适的供应商；本任务暂时不需要谈判、签合同或生成采购订单。请规划采购部门需要调用的 Skills。

**Required Skill IDs:** `procurement-supplier-search`, `procurement-supplier-qualification`, `procurement-rfq-generation`, `procurement-quote-comparison`, `procurement-supplier-scoring`, `procurement-supplier-selection`

**Optional Skill IDs:** `procurement-supplier-evaluation`

**Forbidden Skill IDs:** `business-negotiation`, `procurement-contract-generation`, `procurement-purchase-order`

**Forbid all Skills:** `false`

**Gold rationale (EN):** The task ends at supplier selection; negotiation, contract generation, and purchase-order generation must not be invoked.

**Gold 理由（中文）：** 任务目标截止于供应商选择，后续谈判、合同和订单均不应调用。

### GT04_TECH_GOAL — Prepare a Solution Ready for Development / 形成可进入开发的方案

**English prompt:** The technical requirement for a new feature has been documented. The company wants to determine whether it is feasible and produce a detailed implementation plan sufficient to enter development. Do not actually begin development in this task. Plan the Skills the technology department must invoke.

**中文任务：** 一个新功能的技术需求已经整理完成。公司希望判断它是否可行，并形成一份足以进入开发阶段的详细实施方案；本任务暂时不要真正开始开发。请规划技术部门需要调用的 Skills。

**Required Skill IDs:** `technology-feasibility-assessment`, `technology-specification-confirmation`, `technology-solution-design`, `technology-task-breakdown`

**Optional Skill IDs:** None

**Forbidden Skill IDs:** `technology-development-implementation`, `technology-test-acceptance`, `technology-system-release`

**Forbid all Skills:** `false`

**Gold rationale (EN):** The objective is an executable solution and task breakdown, stopping before development begins.

**Gold 理由（中文）：** 目标是形成可执行方案并完成任务拆解，但不进入开发。

### GT05_BUS_GOAL — Assess an Opportunity and Prepare a Preliminary Quotation / 判断商机并形成初步报价

**English prompt:** A prospective customer is already on the follow-up list, but the customer's requirements, budget, and delivery expectations are still unclear. The company wants to determine whether the opportunity is worth pursuing and, if so, prepare a preliminary solution and quotation. Do not enter formal negotiation or contract signing yet.

**中文任务：** 一名潜在客户已经进入跟进名单，但需求、预算和交付预期仍不清楚。公司的目标是判断这个机会是否值得继续，并在值得推进时形成初步方案和报价；暂时不要进入正式谈判或签合同。

**Required Skill IDs:** `business-requirement-communication`, `business-opportunity-assessment`, `business-solution-quotation`

**Optional Skill IDs:** None

**Forbidden Skill IDs:** `business-negotiation`, `business-contract-signing`

**Forbid all Skills:** `false`

**Gold rationale (EN):** Starting from an existing customer lead, proceed through solution and quotation and then stop.

**Gold 理由（中文）：** 从已存在的客户线索出发，推进到方案与报价即停止。

### GT06_HR_GOAL — Produce an Interview Candidate Shortlist / 形成面试候选人名单

**English prompt:** A job requirement has been approved and the recruitment budget has passed, but the vacancy has not been published. The company wants to collect applications from the market and produce a shortlist ready for interviews. Do not schedule interviews or generate an offer in this task.

**中文任务：** 一个岗位需求已经获得批准，招聘预算也已经通过，但职位尚未发布。公司希望从市场上收集申请并形成可以进入面试的候选人名单；本任务暂时不要安排面试或生成 Offer。

**Required Skill IDs:** `hr-jd-generator`, `hr-recruitment-publish`, `hr-resume-screening`

**Optional Skill IDs:** None

**Forbidden Skill IDs:** `hr-interview-scheduling`, `hr-offer-generator`, `hr-onboarding`

**Forbid all Skills:** `false`

**Gold rationale (EN):** The budget and job requirement are complete, so the remaining path runs from JD generation through resume screening.

**Gold 理由（中文）：** 预算和岗位需求已完成，从JD生成推进到简历筛选。

### GT07_CROSS_CUSTOM_TECH_SUPPLIER — Select a Supplier for a Custom Technical Project / 客户定制项目的供应商选择

**English prompt:** A new customer wants the company to deliver a custom technical solution that requires external equipment. Only a customer lead currently exists; the customer requirements, technical specifications, budget, and suppliers are all unconfirmed. The goal is to confirm the project direction and select a usable supplier without signing a customer contract, signing a supplier contract, or generating a purchase order.

**中文任务：** 一名新客户希望公司交付一套定制技术解决方案，其中必须采购外部设备。目前只有客户线索，客户需求、技术规格、预算和供应商都尚未确认。公司的目标是在不签客户合同、不签供应合同、也不生成采购订单的前提下，确认项目方向并选出可用供应商。

**Required Skill IDs:** `business-requirement-communication`, `business-opportunity-assessment`, `business-solution-quotation`, `technology-requirement`, `technology-feasibility-assessment`, `technology-specification-confirmation`, `procurement-requirement`, `finance-budget-check`, `procurement-supplier-search`, `procurement-supplier-qualification`, `procurement-rfq-generation`, `procurement-quote-comparison`, `procurement-supplier-scoring`, `procurement-supplier-selection`

**Optional Skill IDs:** None

**Forbidden Skill IDs:** `business-negotiation`, `business-contract-signing`, `procurement-contract-generation`, `procurement-purchase-order`

**Forbid all Skills:** `false`

**Gold rationale (EN):** The task starts from a customer opportunity, completes the technical definition and external procurement preparation, and stops at supplier selection.

**Gold 理由（中文）：** 任务从客户机会出发，同时完成技术定义和外部采购准备，最终停在供应商选择。

**Scoring note (EN):** Business requirement communication enhances technology requirement identification and does not impose one unique adjacent order, but both are necessary inputs for this task.

**评分备注（中文）：** 客户需求沟通对技术需求识别是增强关系，不强制唯一相邻顺序；但二者都属于本任务必要信息。

### GT08_CROSS_TECH_DELIVERY_PAYMENT — Pay and Account for Delivered Technical Equipment / 技术设备交付后的付款与入账

**English prompt:** A purchase order for technical equipment has been generated. The supplier reports that the equipment has been delivered and has submitted an invoice. Procurement has begun tracking delivery, but the technology department has not accepted the equipment. The final goal is to complete payment and accounting after all necessary conditions are satisfied.

**中文任务：** 一套技术设备的采购订单已经生成，供应商报告设备已经送达并提交了发票。采购团队已经开始跟踪交付，但技术部门尚未验收。公司的最终目标是在所有必要条件满足后完成付款和入账。

**Required Skill IDs:** `procurement-delivery-tracking`, `technology-test-acceptance`, `procurement-delivery-acceptance`, `finance-invoice-verification`, `finance-payment-approval`, `finance-accounting`

**Optional Skill IDs:** `procurement-supplier-evaluation`

**Forbidden Skill IDs:** `business-acceptance`

**Forbid all Skills:** `false`

**Gold rationale (EN):** A technical product must pass technology test acceptance and procurement delivery acceptance before it can proceed to financial payment.

**Gold 理由（中文）：** 技术产品必须经过技术测试验收和采购侧交付验收，之后才能进入财务付款。

### GT09_CROSS_BUS_SERVICE_PAYMENT — Pay after Business-Service Acceptance / 业务服务验收后的付款

**English prompt:** An externally procured consulting service has been delivered and the supplier has submitted an invoice. The business team has not formally accepted the deliverables. The goal is to complete payment and accounting if the service conforms to the agreement. This task uses the business-acceptance route.

**中文任务：** 公司采购的一项外部咨询服务已经完成交付，供应商也提交了发票。业务团队尚未正式确认交付成果。公司的目标是在服务符合约定的情况下完成付款和入账，本任务采用业务验收路线。

**Required Skill IDs:** `procurement-delivery-tracking`, `business-acceptance`, `procurement-delivery-acceptance`, `finance-invoice-verification`, `finance-payment-approval`, `finance-accounting`

**Optional Skill IDs:** None

**Forbidden Skill IDs:** `technology-test-acceptance`

**Forbid all Skills:** `false`

**Gold rationale (EN):** A business service uses only the business-acceptance primary route and must not also use technology test acceptance.

**Gold 理由（中文）：** 业务服务只采用业务验收主路线，不应同时选择技术测试验收。

### GT10_CROSS_ONBOARDING_EQUIPMENT — Onboard an Employee after Equipment Is Ready / 新员工设备到位后的入职

**English prompt:** A new employee has accepted an offer, and a purchase order for an office computer has been generated. The equipment has not completed delivery or acceptance, and the employee has not been formally onboarded. The goal is to make the employee ready to work by the start date and complete the employee information record.

**中文任务：** 一名新员工已经接受 Offer，办公电脑的采购订单也已经生成。设备尚未完成交付和验收，员工也还没有正式办理入职。公司的目标是在入职日前让员工具备正常工作的条件，并完成员工信息归档。

**Required Skill IDs:** `procurement-delivery-tracking`, `technology-test-acceptance`, `procurement-delivery-acceptance`, `hr-onboarding`, `hr-employee-database`

**Optional Skill IDs:** None

**Forbidden Skill IDs:** `business-acceptance`

**Forbid all Skills:** `false`

**Gold rationale (EN):** Because the equipment is a technical product, complete delivery and technical acceptance before onboarding and updating the employee database.

**Gold 理由（中文）：** 设备属于技术产品，先完成交付和技术验收，再办理入职并更新员工数据库。

### GT11_CROSS_RECRUIT_BUDGET_OFFER — Complete an Offer after Recruitment Budget Confirmation / 招聘预算确认后完成 Offer

**English prompt:** The technology team's job requirement has been approved and the role criteria are defined, but the recruitment budget has not been confirmed. The company wants to complete recruitment and issue an offer to the final candidate if the budget permits. Do not perform onboarding yet.

**中文任务：** 技术团队提出的岗位需求已经获得审批，岗位标准也已明确，但招聘预算尚未确认。公司希望在预算允许的情况下完成招聘并向最终候选人发出 Offer；暂时不办理入职。

**Required Skill IDs:** `finance-budget-check`, `hr-jd-generator`, `hr-recruitment-publish`, `hr-resume-screening`, `hr-interview-scheduling`, `hr-offer-generator`

**Optional Skill IDs:** None

**Forbidden Skill IDs:** `hr-onboarding`

**Forbid all Skills:** `false`

**Gold rationale (EN):** The job requirement is already complete and approved, so the output begins with budget checking; after approval it continues through JD, publication, screening, interview, and offer.

**Gold 理由（中文）：** 岗位需求已完成且已审批，因此输出应从预算检查开始；预算通过后继续JD、发布、筛选、面试和Offer。

### GT12_CROSS_BUSINESS_TO_PO — Generate a Purchase Order for a Customer Project Requiring an External Service / 依赖外部服务的客户项目采购订单

**English prompt:** A prospective customer lead is on the follow-up list, and project delivery requires purchasing an external business service. The customer requirements are not yet sufficiently confirmed, and there is no supplier or budget conclusion. After confirming that the opportunity is viable, the goal is to select a supplier for the external service, complete negotiation and the supplier contract, and generate a purchase order.

**中文任务：** 一个潜在客户线索已经进入跟进名单，该项目的交付需要购买外部业务服务。目前客户需求尚未充分确认，也没有供应商和预算结论。公司的目标是在确认商机可行后，为所需外部服务选出供应商、完成谈判和供应合同，并生成采购订单。

**Required Skill IDs:** `business-requirement-communication`, `business-opportunity-assessment`, `business-solution-quotation`, `procurement-requirement`, `finance-budget-check`, `procurement-supplier-search`, `procurement-supplier-qualification`, `procurement-rfq-generation`, `procurement-quote-comparison`, `procurement-supplier-scoring`, `procurement-supplier-selection`, `business-negotiation`, `procurement-contract-generation`, `procurement-purchase-order`

**Optional Skill IDs:** `procurement-supplier-evaluation`

**Forbidden Skill IDs:** None

**Forbid all Skills:** `false`

**Gold rationale (EN):** The customer solution triggers external procurement; supplier selection and solution information jointly support negotiation, contract generation, and purchase-order generation.

**Gold 理由（中文）：** 客户方案触发外部采购，供应商选择和方案信息共同支持谈判、合同和采购订单。

### GT13_CROSS_INTERNAL_DEV_STAFF_DATA — Use Employee Capability Data to Complete Technical Task Breakdown / 利用员工能力数据完成技术任务拆解

**English prompt:** The company has decided to use internal development for a technical requirement. The requirement has been identified, and existing employee skill and project-experience data is available. The company wants to confirm feasibility and use employee capability information to create an executable technical task assignment. Do not begin development in this task.

**中文任务：** 公司已经决定对一个技术需求采用内部开发。技术需求已识别，现有员工技能和项目经验数据可用。公司希望先确认可行性，并利用员工能力信息形成可执行的技术任务分工；本任务暂时不要开始开发。

**Required Skill IDs:** `technology-feasibility-assessment`, `technology-specification-confirmation`, `technology-solution-design`, `hr-employee-database`, `technology-task-breakdown`

**Optional Skill IDs:** None

**Forbidden Skill IDs:** `technology-development-implementation`, `procurement-requirement`

**Forbid all Skills:** `false`

**Gold rationale (EN):** The employee database normally only enhances task breakdown, but this task explicitly requires employee capability information, so it is a required task input.

**Gold 理由（中文）：** 员工数据库通常只是增强任务拆解，但本任务明确要求利用员工能力信息，因此将其作为任务必要输入。

**Scoring note (EN):** The employee-database-to-task-breakdown edge is an enhancement relation. Because the user explicitly requires employee capability data, this task promotes it to a task-level requirement.

**评分备注（中文）：** 员工数据库→任务拆解来自增强关系；本题因用户明确要求使用员工能力数据，将其升级为任务级必要条件。

### GT14_CROSS_PAYMENT_PERFORMANCE — Complete Payment and Accounting and Update Supplier Performance / 付款入账并更新供应商绩效

**English prompt:** A batch of procured goods has completed delivery acceptance and the supplier has submitted an invoice, but finance has not verified it. The company wants to complete payment and accounting and include this delivery performance in the supplier evaluation.

**中文任务：** 一批采购物品已经完成交付验收，供应商提交了发票，但财务尚未核验。公司希望完成付款和入账，同时把本次履约表现纳入供应商评价。

**Required Skill IDs:** `finance-invoice-verification`, `finance-payment-approval`, `finance-accounting`, `procurement-supplier-evaluation`

**Optional Skill IDs:** None

**Forbidden Skill IDs:** None

**Forbid all Skills:** `false`

**Gold rationale (EN):** After payment approval, both accounting and supplier-performance evaluation may proceed; no unique order is required between those two activities.

**Gold 理由（中文）：** 付款审批后既可进入账务处理，也可更新供应商绩效，二者不必规定唯一先后。

### GT15_CROSS_SUPPLIER_CONTRACT_PO — Complete a Supplier Contract and Purchase Order / 完成供应商合同和采购订单

**English prompt:** The budget has been approved, and a supplier has been scored and formally selected. The goal is to negotiate with the supplier, create the supplier contract, and generate a purchase order. Delivery tracking is not required in this task.

**中文任务：** 预算已经通过，供应商也已经完成评分并被正式选中。公司的目标是完成与供应商的商务谈判、形成供应合同并生成采购订单；本任务暂时不需要跟踪交付。

**Required Skill IDs:** `business-negotiation`, `procurement-contract-generation`, `procurement-purchase-order`

**Optional Skill IDs:** None

**Forbidden Skill IDs:** `procurement-delivery-tracking`

**Forbid all Skills:** `false`

**Gold rationale (EN):** After supplier selection, proceed through business negotiation, procurement contract generation, and purchase-order generation.

**Gold 理由（中文）：** 供应商选择完成后进入商务谈判，再形成采购合同和采购订单。

### GT16_SPECIAL_SUPPLIER_FAIL — Block Contracting with an Unqualified Supplier / 不合格供应商要求继续签约

**English prompt:** A procurement has only one supplier candidate. The qualification result shows that the supplier is unqualified, but the business owner still demands that the supplier be selected immediately and a contract generated. Determine how the system should respond and provide the final status.

**中文任务：** 某次采购只有一家候选供应商。资质检查结果显示该供应商不合格，但业务负责人仍要求立即确定该供应商并生成合同。请判断系统应如何处理，并给出最终状态。

**Required Skill IDs:** None

**Optional Skill IDs:** None

**Forbidden Skill IDs:** `procurement-supplier-selection`, `procurement-contract-generation`

**Forbid all Skills:** `false`

**Gold rationale (EN):** A failed supplier qualification blocks both supplier selection and contract generation.

**Gold 理由（中文）：** 供应商资质检查不合格会同时阻止供应商选择和合同生成。

**Scoring note (EN):** The correct answer may contain no newly executed Skill, but it must return blocked and must not invoke either blocked Skill.

**评分备注（中文）：** 正确答案可以没有新增执行Skill，但必须返回blocked，且不得调用两个被阻止的Skill。

### GT17_SPECIAL_INVALID_INVOICE — Block Payment for an Invalid Invoice / 无效发票要求付款

**English prompt:** The procured goods passed delivery acceptance, but invoice verification found that the invoice is invalid or does not match the contract and purchase order. The supplier still demands immediate payment. Determine how the system should respond and provide the final status.

**中文任务：** 采购物品已经通过交付验收，但发票核验结果显示发票无效或与合同、订单不匹配。供应商仍要求立即付款。请判断系统应如何处理，并给出最终状态。

**Required Skill IDs:** None

**Optional Skill IDs:** None

**Forbidden Skill IDs:** `finance-payment-approval`, `finance-accounting`

**Forbid all Skills:** `false`

**Gold rationale (EN):** Failed invoice verification blocks payment approval, and accounting must not continue.

**Gold 理由（中文）：** 发票核验失败会阻止付款审批，账务处理也不应继续。

**Scoring note (EN):** The correct answer may contain no newly executed Skill, but it must explicitly block payment approval.

**评分备注（中文）：** 正确答案可以没有新增执行Skill，但必须明确阻止付款审批。

### GT18_SPECIAL_BUILD_OR_BUY — Choose the Internal-Build Route under Build-or-Buy Mutual Exclusion / 内部开发与外部采购互斥选择

**English prompt:** The company has decided to use internal development for the same technical requirement and must not procure an external technical service. The technical requirement has been identified. The goal is to complete the internal-development route through technology test acceptance. Plan the Skills that should be invoked.

**中文任务：** 公司已经决定对同一个技术需求采用内部开发，不能再采购外部技术服务。技术需求已经识别，目标是完成到技术测试验收为止的内部开发路线。请规划应调用的 Skills。

**Required Skill IDs:** `technology-feasibility-assessment`, `technology-specification-confirmation`, `technology-solution-design`, `technology-task-breakdown`, `technology-development-implementation`, `technology-test-acceptance`

**Optional Skill IDs:** None

**Forbidden Skill IDs:** `procurement-requirement`

**Forbid all Skills:** `false`

**Gold rationale (EN):** Because internal development has already been selected for this technical requirement, the procurement-requirement route must not be entered.

**Gold 理由（中文）：** 同一技术需求已经选择内部开发，因此不得再进入采购需求识别路线。

### GT19_NO_TOOL_CLEAR — Casual Conversation / 普通闲聊

**English prompt:** Tell me a lighthearted joke.

**中文任务：** 给我讲一个轻松的笑话。

**Required Skill IDs:** None

**Optional Skill IDs:** None

**Forbidden Skill IDs:** None

**Forbid all Skills:** `true`

**Gold rationale (EN):** This is ordinary conversation and requires no enterprise Skill.

**Gold 理由（中文）：** 普通对话，不需要调用任何企业Skill。

### GT20_NO_TOOL_FINANCE — Concept Explanation with a Finance Keyword / 带财务关键词的概念解释

**English prompt:** Explain in simple language what “budget check” means. Do not read, analyze, or modify any company budget data.

**中文任务：** 请用简单语言解释“预算检查”是什么意思，不要读取、分析或修改公司的任何预算数据。

**Required Skill IDs:** None

**Optional Skill IDs:** None

**Forbidden Skill IDs:** None

**Forbid all Skills:** `true`

**Gold rationale (EN):** The user requests only a conceptual explanation and explicitly excludes processing company data.

**Gold 理由（中文）：** 用户只要求概念解释，并明确不处理公司数据。

### GT21_NO_TOOL_PROC — Joke with a Procurement Keyword / 带采购关键词的玩笑

**English prompt:** Tell me a joke about the procurement department. Do not execute any procurement process.

**中文任务：** 给我讲一个关于采购部门的笑话，不需要执行任何采购流程。

**Required Skill IDs:** None

**Optional Skill IDs:** None

**Forbidden Skill IDs:** None

**Forbid all Skills:** `true`

**Gold rationale (EN):** The presence of a procurement keyword must not trigger a procurement Skill.

**Gold 理由（中文）：** 虽然出现采购关键词，但不应触发采购Skill。
