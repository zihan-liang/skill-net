# Skill Name Mapping Report

Authoritative source: `main@cdb4ecdf838fdd4e0bbb01e4c766b32eb430eb47`.

## Resolution rules

- `id` is the exact directory/frontmatter ID under `main/.agents/skills/`.
- `name_en` is the exact H1 title in the authoritative `SKILL.md`.
- Department machine IDs are exact `parent` values in `main/skill_relations.json`.
- Main defines no separate department title or Chinese department label. The English department
  labels preserve the existing V4 display convention, while Chinese department labels are display-only.
- Chinese Skill names are preserved only as display metadata and are never accepted as evaluator keys.

## Department inventory

| Department ID | English name | 中文显示名 | Authoritative source |
|---|---|---|---|
| `finance-agent` | Finance Agent | 财务部门 | `skill_relations.json#/contains/0/parent` |
| `procurement-agent` | Procurement Agent | 采购部门 | `skill_relations.json#/contains/1/parent` |
| `technology-agent` | Technology Agent | 技术部门 | `skill_relations.json#/contains/2/parent` |
| `business-agent` | Business Agent | 业务部门 | `skill_relations.json#/contains/3/parent` |
| `hr-agent` | HR Agent | 人力资源部门 | `skill_relations.json#/contains/4/parent` |

## Complete Skill inventory

| Canonical Skill ID | Canonical English title | 中文显示名 | Department ID | Department English name | 中文部门名 | Source in main |
|---|---|---|---|---|---|---|
| `business-acceptance` | Business Acceptance | 业务验收 | `business-agent` | Business Agent | 业务部门 | `.agents/skills/business-acceptance/SKILL.md` |
| `business-contract-signing` | Business Contract Signing | 合同签署 | `business-agent` | Business Agent | 业务部门 | `.agents/skills/business-contract-signing/SKILL.md` |
| `business-customer-lead` | Business Customer Lead | 客户线索管理 | `business-agent` | Business Agent | 业务部门 | `.agents/skills/business-customer-lead/SKILL.md` |
| `business-negotiation` | Business Negotiation | 商务谈判 | `business-agent` | Business Agent | 业务部门 | `.agents/skills/business-negotiation/SKILL.md` |
| `business-opportunity-assessment` | Business Opportunity Assessment | 商机评估 | `business-agent` | Business Agent | 业务部门 | `.agents/skills/business-opportunity-assessment/SKILL.md` |
| `business-project-delivery-tracking` | Business Project Delivery Tracking | 项目交付跟踪 | `business-agent` | Business Agent | 业务部门 | `.agents/skills/business-project-delivery-tracking/SKILL.md` |
| `business-renewal` | Business Renewal | 客户续约 | `business-agent` | Business Agent | 业务部门 | `.agents/skills/business-renewal/SKILL.md` |
| `business-requirement-communication` | Business Requirement Communication | 客户需求沟通 | `business-agent` | Business Agent | 业务部门 | `.agents/skills/business-requirement-communication/SKILL.md` |
| `business-solution-quotation` | Business Solution and Quotation | 方案与报价 | `business-agent` | Business Agent | 业务部门 | `.agents/skills/business-solution-quotation/SKILL.md` |
| `finance-accounting` | Finance Accounting | 账务处理 | `finance-agent` | Finance Agent | 财务部门 | `.agents/skills/finance-accounting/SKILL.md` |
| `finance-budget-check` | Finance Budget Check | 预算检查 | `finance-agent` | Finance Agent | 财务部门 | `.agents/skills/finance-budget-check/SKILL.md` |
| `finance-budget-planning` | Finance Budget Planning | 预算制定 | `finance-agent` | Finance Agent | 财务部门 | `.agents/skills/finance-budget-planning/SKILL.md` |
| `finance-expense-request` | Finance Expense Request | 费用申请 | `finance-agent` | Finance Agent | 财务部门 | `.agents/skills/finance-expense-request/SKILL.md` |
| `finance-expense-review` | Finance Expense Review | 费用审核 | `finance-agent` | Finance Agent | 财务部门 | `.agents/skills/finance-expense-review/SKILL.md` |
| `finance-invoice-verification` | Finance Invoice Verification | 发票核验 | `finance-agent` | Finance Agent | 财务部门 | `.agents/skills/finance-invoice-verification/SKILL.md` |
| `finance-payment-approval` | Finance Payment Approval | 付款审批 | `finance-agent` | Finance Agent | 财务部门 | `.agents/skills/finance-payment-approval/SKILL.md` |
| `finance-reporting` | Finance Reporting | 财务报表生成 | `finance-agent` | Finance Agent | 财务部门 | `.agents/skills/finance-reporting/SKILL.md` |
| `hr-employee-database` | HR Employee Database | 员工数据库 | `hr-agent` | HR Agent | 人力资源部门 | `.agents/skills/hr-employee-database/SKILL.md` |
| `hr-interview-scheduling` | HR Interview Scheduling | 面试安排 | `hr-agent` | HR Agent | 人力资源部门 | `.agents/skills/hr-interview-scheduling/SKILL.md` |
| `hr-jd-generator` | HR JD Generator | JD生成 | `hr-agent` | HR Agent | 人力资源部门 | `.agents/skills/hr-jd-generator/SKILL.md` |
| `hr-job-requirement` | HR Job Requirement | 岗位需求 | `hr-agent` | HR Agent | 人力资源部门 | `.agents/skills/hr-job-requirement/SKILL.md` |
| `hr-offer-generator` | HR Offer Generator | Offer生成 | `hr-agent` | HR Agent | 人力资源部门 | `.agents/skills/hr-offer-generator/SKILL.md` |
| `hr-onboarding` | HR Onboarding | 入职管理 | `hr-agent` | HR Agent | 人力资源部门 | `.agents/skills/hr-onboarding/SKILL.md` |
| `hr-recruitment-publish` | HR Recruitment Publish | 招聘发布 | `hr-agent` | HR Agent | 人力资源部门 | `.agents/skills/hr-recruitment-publish/SKILL.md` |
| `hr-resume-screening` | HR Resume Screening | 简历筛选 | `hr-agent` | HR Agent | 人力资源部门 | `.agents/skills/hr-resume-screening/SKILL.md` |
| `procurement-contract-generation` | Procurement Contract Generation | 合同生成 | `procurement-agent` | Procurement Agent | 采购部门 | `.agents/skills/procurement-contract-generation/SKILL.md` |
| `procurement-delivery-acceptance` | Procurement Delivery Acceptance | 交付验收 | `procurement-agent` | Procurement Agent | 采购部门 | `.agents/skills/procurement-delivery-acceptance/SKILL.md` |
| `procurement-delivery-tracking` | Procurement Delivery Tracking | 交付跟踪 | `procurement-agent` | Procurement Agent | 采购部门 | `.agents/skills/procurement-delivery-tracking/SKILL.md` |
| `procurement-purchase-order` | Procurement Purchase Order | 采购订单生成 | `procurement-agent` | Procurement Agent | 采购部门 | `.agents/skills/procurement-purchase-order/SKILL.md` |
| `procurement-quote-comparison` | Procurement Quote Comparison | 报价比较 | `procurement-agent` | Procurement Agent | 采购部门 | `.agents/skills/procurement-quote-comparison/SKILL.md` |
| `procurement-requirement` | Procurement Requirement | 采购需求识别 | `procurement-agent` | Procurement Agent | 采购部门 | `.agents/skills/procurement-requirement/SKILL.md` |
| `procurement-rfq-generation` | Procurement RFQ Generation | 询价单生成 | `procurement-agent` | Procurement Agent | 采购部门 | `.agents/skills/procurement-rfq-generation/SKILL.md` |
| `procurement-supplier-evaluation` | Procurement Supplier Evaluation | 供应商绩效评价 | `procurement-agent` | Procurement Agent | 采购部门 | `.agents/skills/procurement-supplier-evaluation/SKILL.md` |
| `procurement-supplier-qualification` | Procurement Supplier Qualification | 供应商资质检查 | `procurement-agent` | Procurement Agent | 采购部门 | `.agents/skills/procurement-supplier-qualification/SKILL.md` |
| `procurement-supplier-scoring` | Procurement Supplier Scoring | 供应商评分 | `procurement-agent` | Procurement Agent | 采购部门 | `.agents/skills/procurement-supplier-scoring/SKILL.md` |
| `procurement-supplier-search` | Procurement Supplier Search | 供应商搜索 | `procurement-agent` | Procurement Agent | 采购部门 | `.agents/skills/procurement-supplier-search/SKILL.md` |
| `procurement-supplier-selection` | Procurement Supplier Selection | 供应商选择 | `procurement-agent` | Procurement Agent | 采购部门 | `.agents/skills/procurement-supplier-selection/SKILL.md` |
| `technology-development-implementation` | Technology Development and Implementation | 开发或实施 | `technology-agent` | Technology Agent | 技术部门 | `.agents/skills/technology-development-implementation/SKILL.md` |
| `technology-feasibility-assessment` | Technology Feasibility Assessment | 可行性评估 | `technology-agent` | Technology Agent | 技术部门 | `.agents/skills/technology-feasibility-assessment/SKILL.md` |
| `technology-operations-maintenance` | Technology Operations and Maintenance | 运行维护 | `technology-agent` | Technology Agent | 技术部门 | `.agents/skills/technology-operations-maintenance/SKILL.md` |
| `technology-requirement` | Technology Requirement | 技术需求识别 | `technology-agent` | Technology Agent | 技术部门 | `.agents/skills/technology-requirement/SKILL.md` |
| `technology-solution-design` | Technology Solution Design | 技术方案设计 | `technology-agent` | Technology Agent | 技术部门 | `.agents/skills/technology-solution-design/SKILL.md` |
| `technology-specification-confirmation` | Technology Specification Confirmation | 技术规格确认 | `technology-agent` | Technology Agent | 技术部门 | `.agents/skills/technology-specification-confirmation/SKILL.md` |
| `technology-system-release` | Technology System Release | 系统上线 | `technology-agent` | Technology Agent | 技术部门 | `.agents/skills/technology-system-release/SKILL.md` |
| `technology-task-breakdown` | Technology Task Breakdown | 任务拆解 | `technology-agent` | Technology Agent | 技术部门 | `.agents/skills/technology-task-breakdown/SKILL.md` |
| `technology-test-acceptance` | Technology Test Acceptance | 技术测试验收 | `technology-agent` | Technology Agent | 技术部门 | `.agents/skills/technology-test-acceptance/SKILL.md` |

## Metadata-title discrepancies reviewed

`SKILL.md` H1 is used for `name_en`; `agents/openai.yaml` remains interface metadata.

| Skill ID | SKILL.md H1 used as name_en | openai.yaml display_name |
|---|---|---|
| `business-solution-quotation` | Business Solution and Quotation | Business Solution Quotation |
| `hr-employee-database` | HR Employee Database | Hr Employee Database |
| `hr-interview-scheduling` | HR Interview Scheduling | Hr Interview Scheduling |
| `hr-jd-generator` | HR JD Generator | Hr Jd Generator |
| `hr-job-requirement` | HR Job Requirement | Hr Job Requirement |
| `hr-offer-generator` | HR Offer Generator | Hr Offer Generator |
| `hr-onboarding` | HR Onboarding | Hr Onboarding |
| `hr-recruitment-publish` | HR Recruitment Publish | Hr Recruitment Publish |
| `hr-resume-screening` | HR Resume Screening | Hr Resume Screening |
| `procurement-rfq-generation` | Procurement RFQ Generation | Procurement Rfq Generation |
| `technology-development-implementation` | Technology Development and Implementation | Technology Development Implementation |
| `technology-operations-maintenance` | Technology Operations and Maintenance | Technology Operations Maintenance |

## Ambiguities and resolutions

- The old Chinese aliases 技术验收、供应商资质核验、财务报告生成 are not retained as
  machine aliases. Exact canonical IDs are required, so `aliases` is empty.
- The old `ALL_BUSINESS_SKILLS` sentinel is not a canonical Skill ID. It is replaced by
  the boolean task field `forbid_all_skills: true` for no-tool tasks.
- Both 前置依赖 and 跨部门依赖 map to authoritative relation type `prerequisite`.
  Chinese labels remain in `relations_tested_display_zh`.
