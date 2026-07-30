#!/usr/bin/env python3
"""Deterministically build frozen SkillNet E1-v2 Gold, pools, and Catalogues.

This builder never invokes a model and only writes inside the E1-v2 namespaces.
Use ``--check`` after generation to compare every generated JSON value without
rewriting any file.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
E1V2_DIR = ROOT / "experiments" / "skillnet_e1v2"
SOURCE_GOLD = ROOT / "SkillNet_Gold_Tasks_V4" / "02_Gold_Standard_21_V4.json"
SOURCE_SCHEMA = (
    ROOT
    / "SkillNet_Gold_Tasks_V4"
    / "evaluation"
    / "prediction_schema.json"
)
FULL_A = (
    ROOT
    / "skillnet_run_guide_v1_1"
    / "catalogues"
    / "size_46"
    / "A_flat_catalogue.json"
)
FULL_B = (
    ROOT
    / "skillnet_run_guide_v1_1"
    / "catalogues"
    / "size_46"
    / "B_department_grouped_catalogue.json"
)
FULL_C = (
    ROOT
    / "skillnet_run_guide_v1_1"
    / "catalogues"
    / "size_46"
    / "C_graph_structured_catalogue.json"
)
GOLD_DIR = ROOT / "SkillNet_Gold_Tasks_V4" / "e1v2"
CATALOGUE_ROOT = (
    ROOT / "skillnet_run_guide_v1_1" / "e1v2_catalogues"
)

REPLACEMENTS = {
    "GT03_PROC_GOAL": "E1V2_GT03_PROC_SHORT",
    "GT07_CROSS_CUSTOM_TECH_SUPPLIER": "E1V2_GT07_CUSTOM_TECH_SUPPLIER_SHORT",
    "GT12_CROSS_BUSINESS_TO_PO": "E1V2_GT12_BUSINESS_TO_PO_SHORT",
}
CONFIGURATION_FILENAMES = {
    "A": "A_flat_catalogue.json",
    "B": "B_department_grouped_catalogue.json",
    "C": "C_graph_structured_catalogue.json",
}
ENDPOINTS = {
    "prerequisite": ("before", "after"),
    "conflict": ("gate_skill", "blocked_skill"),
    "mutex": ("skill_a", "skill_b"),
    "enhances": ("source", "target"),
}
GOLD_LEAK_KEYS = {
    "required_skills",
    "optional_skills",
    "forbidden_skills",
    "canonical_sequence",
    "hard_order_constraints",
    "initial_skill_states",
    "expected_blocked_by",
    "expected_route_choice",
    "task_constraints",
    "gold",
    "gold_answer",
    "prompt_en",
    "prompt_zh",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")


def stable_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_bytes(value)).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install(path: Path, value: Any, *, check: bool) -> None:
    expected = json_bytes(value)
    if check:
        if not path.is_file():
            raise RuntimeError(f"Missing generated file: {path}")
        if path.read_bytes() != expected:
            raise RuntimeError(f"Generated file drift: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(expected)


def install_text(path: Path, text: str, *, check: bool) -> None:
    expected = text.encode("utf-8")
    if check:
        if not path.is_file() or path.read_bytes() != expected:
            raise RuntimeError(f"Generated text drift: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(expected)


def new_short_tasks() -> dict[str, dict[str, Any]]:
    return {
        "E1V2_GT03_PROC_SHORT": {
            "task_id": "E1V2_GT03_PROC_SHORT",
            "category": "single_department_goal",
            "difficulty": "medium",
            "title_en": "Select a Supplier from Qualified Comparable Quotes",
            "title_zh": "从合格且可比的报价中确定供应商",
            "prompt_en": (
                "The procurement team has completed supplier qualification and "
                "received RFQ responses from the qualified candidates. Normalize "
                "and compare the quotes, score the qualified suppliers, and select "
                "one supplier. Stop at selection; do not negotiate, generate a "
                "contract, or create a purchase order."
            ),
            "prompt_zh": (
                "采购团队已经完成供应商资质核验，并收到合格候选供应商的询价回复。"
                "请对报价进行归一化比较、对合格供应商评分并确定一家供应商；任务到选择"
                "供应商为止，不要进入谈判、生成合同或创建采购订单。"
            ),
            "use_skills": True,
            "required_departments": ["procurement-agent"],
            "required_skills": [
                "procurement-quote-comparison",
                "procurement-supplier-scoring",
                "procurement-supplier-selection",
            ],
            "optional_skills": [],
            "forbidden_skills": [
                "business-negotiation",
                "procurement-contract-generation",
                "procurement-purchase-order",
            ],
            "forbid_all_skills": False,
            "relations_tested": ["prerequisite"],
            "relations_tested_display_zh": ["前置依赖"],
            "gold_rationale_en": (
                "Qualification and RFQ generation are completed gates. The remaining "
                "route compares quotes, scores suppliers, and selects one, then stops."
            ),
            "gold_rationale_zh": (
                "资质核验和询价生成已完成；剩余路线依次比较报价、评分和选择供应商，"
                "并在选择后停止。"
            ),
            "scoring_notes_en": (
                "The completed qualification and RFQ Skills must not be repeated."
            ),
            "scoring_notes_zh": "已完成的资质核验和询价生成 Skill 不得重复调用。",
            "hard_order_constraints": [
                {
                    "before": "procurement-quote-comparison",
                    "after": "procurement-supplier-scoring",
                    "constraint_type": "mandatory_order",
                },
                {
                    "before": "procurement-supplier-scoring",
                    "after": "procurement-supplier-selection",
                    "constraint_type": "mandatory_order",
                },
            ],
            "canonical_sequence": [
                "procurement-quote-comparison",
                "procurement-supplier-scoring",
                "procurement-supplier-selection",
            ],
            "initial_skill_states": {
                "procurement-supplier-qualification": {
                    "status": "completed",
                    "result": "qualified",
                },
                "procurement-rfq-generation": {
                    "status": "completed",
                    "result": "responses_received",
                },
            },
            "initial_route_choices": {},
            "expected_final_status": "completed",
            "expected_blocked_by": [],
            "expected_route_choice": {},
            "task_constraints": [],
            "e1v2_design_provenance": {
                "source_task_id": "GT03_PROC_GOAL",
                "scale_compatibility_method": "freeze upstream qualification and RFQ as completed; preserve the supplier-selection tail and downstream stop gates",
            },
        },
        "E1V2_GT07_CUSTOM_TECH_SUPPLIER_SHORT": {
            "task_id": "E1V2_GT07_CUSTOM_TECH_SUPPLIER_SHORT",
            "category": "cross_department_goal",
            "difficulty": "hard",
            "title_en": "Finalize Supplier Selection for a Custom Technical Project",
            "title_zh": "完成定制技术项目的供应商选择",
            "prompt_en": (
                "For a custom customer solution requiring external equipment, the "
                "business solution, technical specification, procurement budget, "
                "and normalized quote comparison have all been completed. Use the "
                "existing evidence to score the suppliers and select one. Do not "
                "negotiate, sign either a customer or supplier contract, or create "
                "a purchase order."
            ),
            "prompt_zh": (
                "一个需要外部设备的客户定制技术方案已经完成业务方案、技术规格、采购"
                "预算确认和报价归一化比较。请使用现有证据完成供应商评分并确定一家供应商；"
                "不要进入谈判，不要签客户合同或供应合同，也不要创建采购订单。"
            ),
            "use_skills": True,
            "required_departments": ["procurement-agent"],
            "required_skills": [
                "procurement-supplier-scoring",
                "procurement-supplier-selection",
            ],
            "optional_skills": [],
            "forbidden_skills": [
                "business-negotiation",
                "business-contract-signing",
                "procurement-contract-generation",
                "procurement-purchase-order",
            ],
            "forbid_all_skills": False,
            "relations_tested": ["prerequisite", "cross_department_state"],
            "relations_tested_display_zh": ["前置依赖", "跨部门已完成状态"],
            "gold_rationale_en": (
                "The cross-department definition and commercial comparison are "
                "frozen as completed inputs. Only scoring and selection remain, and "
                "all premature contracting steps are prohibited."
            ),
            "gold_rationale_zh": (
                "跨部门方案定义和商业比较已作为完成输入冻结；只剩评分与选择，并禁止"
                "提前进入谈判、合同和订单。"
            ),
            "scoring_notes_en": (
                "This task retains hard cross-department state tracking and "
                "over-call control while fitting the ten-Skill visibility bound."
            ),
            "scoring_notes_zh": (
                "本题保留跨部门已完成状态识别和过度调用控制，同时满足十 Skill 可见性上限。"
            ),
            "hard_order_constraints": [
                {
                    "before": "procurement-supplier-scoring",
                    "after": "procurement-supplier-selection",
                    "constraint_type": "mandatory_order",
                }
            ],
            "canonical_sequence": [
                "procurement-supplier-scoring",
                "procurement-supplier-selection",
            ],
            "initial_skill_states": {
                "business-solution-quotation": {
                    "status": "completed",
                    "result": "approved",
                },
                "technology-specification-confirmation": {
                    "status": "completed",
                    "result": "confirmed",
                },
                "finance-budget-check": {
                    "status": "completed",
                    "result": "approved",
                },
                "procurement-quote-comparison": {
                    "status": "completed",
                    "result": "normalized",
                },
            },
            "initial_route_choices": {},
            "expected_final_status": "completed",
            "expected_blocked_by": [],
            "expected_route_choice": {},
            "task_constraints": [],
            "e1v2_design_provenance": {
                "source_task_id": "GT07_CROSS_CUSTOM_TECH_SUPPLIER",
                "scale_compatibility_method": "freeze four cross-department inputs as completed; retain supplier scoring/selection and premature-contract controls without adding a route decision absent from the source task",
            },
        },
        "E1V2_GT12_BUSINESS_TO_PO_SHORT": {
            "task_id": "E1V2_GT12_BUSINESS_TO_PO_SHORT",
            "category": "cross_department_goal",
            "difficulty": "hard",
            "title_en": "Create the Supplier Contract and PO for a Customer Project",
            "title_zh": "为客户项目形成供应合同和采购订单",
            "prompt_en": (
                "A customer project's solution and quotation are approved, its "
                "external-service budget is approved, and a supplier has been "
                "formally selected. Complete supplier negotiation, generate the "
                "supplier contract, and create the purchase order. Do not sign a "
                "customer contract or begin delivery tracking in this task."
            ),
            "prompt_zh": (
                "一个客户项目的方案与报价已经通过，外部服务预算也已批准，并且供应商已"
                "正式选定。请完成供应商谈判、生成供应合同并创建采购订单；本任务不要签"
                "客户合同，也不要开始交付跟踪。"
            ),
            "use_skills": True,
            "required_departments": [
                "business-agent",
                "procurement-agent",
            ],
            "required_skills": [
                "business-negotiation",
                "procurement-contract-generation",
                "procurement-purchase-order",
            ],
            "optional_skills": [],
            "forbidden_skills": [
                "business-contract-signing",
                "procurement-delivery-tracking",
            ],
            "forbid_all_skills": False,
            "relations_tested": ["prerequisite", "cross_department_state"],
            "relations_tested_display_zh": ["前置依赖", "跨部门已完成状态"],
            "gold_rationale_en": (
                "The customer solution, budget, and supplier-selection gates are "
                "completed. The remaining cross-department route is negotiation, "
                "supplier contract generation, and purchase-order generation."
            ),
            "gold_rationale_zh": (
                "客户方案、预算和供应商选择门禁已完成；剩余跨部门路线是谈判、供应合同"
                "生成和采购订单生成。"
            ),
            "scoring_notes_en": (
                "Customer contract signing and post-PO delivery tracking are distinct "
                "tempting downstream branches and are forbidden."
            ),
            "scoring_notes_zh": (
                "客户合同签署和订单后的交付跟踪是易混淆分支，本题明确禁止。"
            ),
            "hard_order_constraints": [
                {
                    "before": "business-negotiation",
                    "after": "procurement-contract-generation",
                    "constraint_type": "mandatory_order",
                },
                {
                    "before": "procurement-contract-generation",
                    "after": "procurement-purchase-order",
                    "constraint_type": "mandatory_order",
                },
            ],
            "canonical_sequence": [
                "business-negotiation",
                "procurement-contract-generation",
                "procurement-purchase-order",
            ],
            "initial_skill_states": {
                "business-solution-quotation": {
                    "status": "completed",
                    "result": "approved",
                },
                "finance-budget-check": {
                    "status": "completed",
                    "result": "approved",
                },
                "procurement-supplier-selection": {
                    "status": "completed",
                    "result": "selected",
                },
            },
            "initial_route_choices": {},
            "expected_final_status": "completed",
            "expected_blocked_by": [],
            "expected_route_choice": {},
            "task_constraints": [],
            "e1v2_design_provenance": {
                "source_task_id": "GT12_CROSS_BUSINESS_TO_PO",
                "scale_compatibility_method": "freeze customer solution, budget, and supplier selection as completed; retain the negotiation-to-PO cross-department tail",
            },
        },
    }


def build_gold(source: dict[str, Any]) -> dict[str, Any]:
    source_by_id = {task["task_id"]: task for task in source["tasks"]}
    replacements = new_short_tasks()
    tasks = []
    mapping = []
    for original in source["tasks"]:
        source_id = original["task_id"]
        if source_id in REPLACEMENTS:
            task = replacements[REPLACEMENTS[source_id]]
            origin = "new_scale_compatible_short"
        else:
            task = copy.deepcopy(original)
            origin = "original_compatible"
        tasks.append(task)
        mapping.append(
            {
                "task_id": task["task_id"],
                "source_task_id": source_id,
                "task_origin": origin,
                "original_task_record_json_value_preserved": origin == "original_compatible",
            }
        )
    gold = copy.deepcopy(source)
    gold.update(
        {
            "version": "E1V2-setup-frozen-v1",
            "date": "2026-07-30",
            "task_count": 21,
            "tasks": tasks,
            "distribution": dict(Counter(task["category"] for task in tasks)),
            "experiment_id": "E1V2",
            "e1v2_provenance": {
                "source_gold_path": str(SOURCE_GOLD.relative_to(ROOT)),
                "source_gold_sha256": file_hash(SOURCE_GOLD),
                "selection_rule": "Use every original task whose complete GoldRelevantSkills set fits size 10; replace GT03, GT07, and GT12 with frozen scale-compatible short tasks.",
                "task_mapping": mapping,
                "formal_model_calls_before_freeze": 0,
            },
        }
    )
    return gold


def add_source(sources: dict[str, set[str]], skill: str, source: str) -> None:
    sources[skill].add(source)


def gold_relevant(task: dict[str, Any]) -> tuple[list[str], dict[str, list[str]]]:
    sources: dict[str, set[str]] = defaultdict(set)
    for field in ("required_skills", "optional_skills", "forbidden_skills"):
        for index, skill in enumerate(task.get(field, [])):
            add_source(sources, skill, f"{field}[{index}]")
    for skill in task.get("initial_skill_states", {}):
        add_source(sources, skill, f"initial_skill_states.{skill}")
    for index, skill in enumerate(task.get("expected_blocked_by", [])):
        add_source(sources, skill, f"expected_blocked_by[{index}]")
    for index, skill in enumerate(task.get("canonical_sequence", [])):
        add_source(sources, skill, f"canonical_sequence[{index}]")
    for index, pair in enumerate(task.get("hard_order_constraints", [])):
        add_source(sources, pair["before"], f"hard_order_constraints[{index}].before")
        add_source(sources, pair["after"], f"hard_order_constraints[{index}].after")
    for index, rule in enumerate(task.get("task_constraints", [])):
        if rule.get("trigger_skill"):
            add_source(
                sources,
                rule["trigger_skill"],
                f"task_constraints[{index}].trigger_skill",
            )
        for field in ("blocked_skills", "forbidden_route_skills", "skills"):
            for item_index, skill in enumerate(rule.get(field, [])):
                add_source(
                    sources,
                    skill,
                    f"task_constraints[{index}].{field}[{item_index}]",
                )
    normalized = {
        skill: sorted(values) for skill, values in sorted(sources.items())
    }
    return sorted(normalized), normalized


def graph_features(full_c: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    features: dict[str, dict[str, list[str]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for relation_type, records in full_c["relations"].items():
        left, right = ENDPOINTS[relation_type]
        for record in records:
            source, target = record[left], record[right]
            features[source][target].append(f"{relation_type}:outgoing")
            features[target][source].append(f"{relation_type}:incoming")
    return features


def keyword_department_hints(task: dict[str, Any]) -> set[str]:
    text = f"{task.get('prompt_en', '')} {task.get('prompt_zh', '')}".lower()
    mapping = {
        "finance-agent": ("finance", "budget", "invoice", "payment", "财务", "预算", "发票", "付款"),
        "procurement-agent": ("procurement", "supplier", "purchase", "采购", "供应商", "订单"),
        "technology-agent": ("technology", "technical", "development", "技术", "开发", "设备"),
        "business-agent": ("business", "customer", "contract", "业务", "客户", "合同"),
        "hr-agent": ("employee", "recruit", "offer", "员工", "招聘", "入职"),
    }
    return {
        department
        for department, terms in mapping.items()
        if any(term in text for term in terms)
    }


def rank_distractors(
    task: dict[str, Any],
    relevant: set[str],
    cards: dict[str, dict[str, Any]],
    features: dict[str, dict[str, list[str]]],
) -> list[dict[str, Any]]:
    relevant_departments = {
        cards[skill]["department_id"] for skill in relevant
    } | set(task.get("required_departments", []))
    hint_departments = keyword_department_hints(task)
    relevant_tokens = {
        token
        for skill in relevant
        for token in skill.split("-")
        if token not in {"finance", "procurement", "technology", "business", "hr"}
    }
    ranked = []
    for skill_id, card in cards.items():
        if skill_id in relevant:
            continue
        score = 0
        reasons = []
        department = card["department_id"]
        if department in relevant_departments:
            score += 100
            reasons.append("same_department_as_gold_relevant")
        if department in hint_departments:
            score += 35
            reasons.append("task_text_department_keyword")
        adjacent = sorted(set(features.get(skill_id, {})) & relevant)
        if adjacent:
            score += 80 + 4 * len(adjacent)
            reasons.append(f"graph_adjacent_to_gold:{','.join(adjacent)}")
        shared = sorted(set(skill_id.split("-")) & relevant_tokens)
        if shared:
            score += 10 * len(shared)
            reasons.append(f"name_token_similarity:{','.join(shared)}")
        outgoing_to_gold = sorted(
            target
            for target in adjacent
            if any(
                label.endswith("outgoing")
                for label in features[skill_id][target]
            )
        )
        incoming_from_gold = sorted(
            target
            for target in adjacent
            if any(
                label.endswith("incoming")
                for label in features[skill_id][target]
            )
        )
        if incoming_from_gold:
            score += 30
            reasons.append(
                f"tempting_downstream_overcall:{','.join(incoming_from_gold)}"
            )
        if outgoing_to_gold:
            score += 20
            reasons.append(
                f"tempting_upstream_repetition:{','.join(outgoing_to_gold)}"
            )
        if not reasons:
            reasons.append("deterministic_global_fill")
        ranked.append(
            {
                "skill_id": skill_id,
                "score": score,
                "reasons": reasons,
            }
        )
    return sorted(ranked, key=lambda item: (-item["score"], item["skill_id"]))


def relation_subset(full_c: dict[str, Any], skill_ids: set[str]) -> dict[str, Any]:
    output = {}
    for relation_type, records in full_c["relations"].items():
        left, right = ENDPOINTS[relation_type]
        output[relation_type] = [
            copy.deepcopy(record)
            for record in records
            if record[left] in skill_ids and record[right] in skill_ids
        ]
    return output


def build_catalogues(
    *,
    task_id: str,
    size: int,
    skill_ids: list[str],
    cards: dict[str, dict[str, Any]],
    full_b: dict[str, Any],
    full_c: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    selected_cards = [copy.deepcopy(cards[skill]) for skill in sorted(skill_ids)]
    card_hash = stable_hash(selected_cards)
    base = {
        "schema_version": "E1V2-1.0",
        "experiment_id": "E1V2",
        "source_commit": full_c["source_commit"],
        "task_id": task_id,
        "catalogue_size": size,
        "skill_cards_sha256": card_hash,
        "candidate_skill_ids_sha256": stable_hash(skill_ids),
    }
    a = {
        **base,
        "configuration": "A",
        "organization": "flat",
        "skills": selected_cards,
    }
    departments = []
    selected_by_id = {card["skill_id"]: card for card in selected_cards}
    for source_department in full_b["departments"]:
        departments.append(
            {
                key: copy.deepcopy(value)
                for key, value in source_department.items()
                if key != "skills"
            }
            | {
                "skills": [
                    copy.deepcopy(selected_by_id[card["skill_id"]])
                    for card in source_department["skills"]
                    if card["skill_id"] in selected_by_id
                ]
            }
        )
    b = {
        **base,
        "configuration": "B",
        "organization": "department_grouped",
        "departments": departments,
    }
    relations = relation_subset(full_c, set(skill_ids))
    c = {
        **base,
        "configuration": "C",
        "organization": "department_grouped_graph",
        "departments": copy.deepcopy(departments),
        "relations_sha256": stable_hash(relations),
        "relations": relations,
        "relation_semantics": copy.deepcopy(full_c["relation_semantics"]),
    }
    return {"A": a, "B": b, "C": c}


def prompt_text(task: dict[str, Any]) -> str:
    return f"""Task ID: {task['task_id']}
Task title (English): {task['title_en']}
任务名称（中文）：{task['title_zh']}

English task prompt
{task['prompt_en']}

中文任务
{task['prompt_zh']}

Output requirements
Return exactly one valid JSON object with these fields:
task_id, use_skills, selected_departments, skill_sequence, final_status,
blocked_by, route_choice, reason.

Use exact canonical English Skill IDs from the current Catalogue in skill_sequence
and blocked_by. Use exact canonical department IDs from the current Catalogue in
selected_departments. Do not output a Markdown code block or non-JSON text.
"""


def recursive_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(value)
        for item in value.values():
            keys.update(recursive_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(recursive_keys(item))
    return keys


def build(check: bool) -> dict[str, Any]:
    source = load_json(SOURCE_GOLD)
    schema = copy.deepcopy(load_json(SOURCE_SCHEMA))
    full_a = load_json(FULL_A)
    full_b = load_json(FULL_B)
    full_c = load_json(FULL_C)
    gold = build_gold(source)
    schema["title"] = "SkillNet E1-v2 Prediction — Fixed Eight Fields"
    schema["description"] = (
        "E1-v2 isolated wrapper of the unchanged canonical eight-field contract; "
        "only the task_id pattern is expanded for the three new frozen short tasks."
    )
    schema["properties"]["task_id"]["pattern"] = (
        r"^(?:GT[0-9]{2}_[A-Z0-9_]+|"
        r"E1V2_GT(?:03|07|12)_[A-Z0-9_]+)$"
    )
    schema["e1v2_provenance"] = {
        "source_schema_path": str(SOURCE_SCHEMA.relative_to(ROOT)),
        "source_schema_sha256": file_hash(SOURCE_SCHEMA),
        "canonical_fields_changed": [],
        "task_id_pattern_only_wrapper_change": True,
    }
    install(
        E1V2_DIR / "prediction_schema_e1v2.json",
        schema,
        check=check,
    )
    cards = {card["skill_id"]: card for card in full_a["skills"]}
    full_skill_ids = list(cards)
    features = graph_features(full_c)
    if len(cards) != 46:
        raise RuntimeError("The frozen full Catalogue must contain 46 Skills")

    install(GOLD_DIR / "E1V2_Gold_21.json", gold, check=check)
    for task in gold["tasks"]:
        install_text(
            GOLD_DIR / "prompts" / f"{task['task_id']}.txt",
            prompt_text(task),
            check=check,
        )
        perfect_prediction = {
            "task_id": task["task_id"],
            "use_skills": task["use_skills"],
            "selected_departments": list(task["required_departments"]),
            "skill_sequence": list(task["canonical_sequence"]),
            "final_status": task["expected_final_status"],
            "blocked_by": list(task["expected_blocked_by"]),
            "route_choice": dict(task["expected_route_choice"]),
            "reason": "Frozen deterministic Setup fixture.",
        }
        install_text(
            E1V2_DIR
            / "fixtures"
            / "gold_perfect"
            / f"{task['task_id']}.txt",
            json.dumps(perfect_prediction, ensure_ascii=False) + "\n",
            check=check,
        )

    source_by_id = {task["task_id"]: task for task in source["tasks"]}
    pool_records = []
    catalogue_manifest_records = []
    relevant_report = []
    for task in gold["tasks"]:
        task_id = task["task_id"]
        source_id = (
            task.get("e1v2_design_provenance", {}).get("source_task_id")
            or task_id
        )
        origin = (
            "new_scale_compatible_short"
            if task_id.startswith("E1V2_")
            else "original_compatible"
        )
        if origin == "original_compatible" and task != source_by_id[source_id]:
            raise RuntimeError(f"Original task JSON value changed: {task_id}")
        relevant_ids, relevant_sources = gold_relevant(task)
        if len(relevant_ids) > 10:
            raise RuntimeError(
                f"STOPPED: {task_id} has {len(relevant_ids)} GoldRelevantSkills"
            )
        ranked = rank_distractors(
            task, set(relevant_ids), cards, features
        )
        distractor_ids = [item["skill_id"] for item in ranked]
        ordered = relevant_ids + distractor_ids
        if set(ordered) != set(full_skill_ids) or len(ordered) != 46:
            raise RuntimeError(f"Candidate ordering is not the full set: {task_id}")
        pools = {}
        for size in (10, 30, 46):
            ids = ordered[:size]
            selection = []
            ranking_by_id = {item["skill_id"]: item for item in ranked}
            for index, skill_id in enumerate(ids):
                if skill_id in relevant_sources:
                    selection.append(
                        {
                            "position": index + 1,
                            "skill_id": skill_id,
                            "kind": "gold_relevant",
                            "reasons": relevant_sources[skill_id],
                        }
                    )
                else:
                    rank = ranking_by_id[skill_id]
                    selection.append(
                        {
                            "position": index + 1,
                            "skill_id": skill_id,
                            "kind": "frozen_distractor",
                            "difficulty_score": rank["score"],
                            "reasons": rank["reasons"],
                        }
                    )
            pools[str(size)] = {
                "skill_ids": ids,
                "skill_ids_sha256": stable_hash(ids),
                "task_text_json_sha256": stable_hash(task["prompt_zh"]),
                "gold_json_sha256": stable_hash(task),
                "selection": selection,
                "source": (
                    "frozen_complete_46_skill_set"
                    if size == 46
                    else "gold_relevant_then_deterministic_distractor_ranking"
                ),
            }
            catalogues = build_catalogues(
                task_id=task_id,
                size=size,
                skill_ids=ids,
                cards=cards,
                full_b=full_b,
                full_c=full_c,
            )
            for configuration, catalogue in catalogues.items():
                relative = (
                    Path("tasks")
                    / task_id
                    / f"size_{size}"
                    / CONFIGURATION_FILENAMES[configuration]
                )
                path = CATALOGUE_ROOT / relative
                install(path, catalogue, check=check)
                catalogue_manifest_records.append(
                    {
                        "task_id": task_id,
                        "catalogue_size": size,
                        "configuration": configuration,
                        "path": str(
                            (
                                Path("skillnet_run_guide_v1_1")
                                / "e1v2_catalogues"
                                / relative
                            )
                        ),
                        "file_sha256": (
                            hashlib.sha256(json_bytes(catalogue)).hexdigest()
                            if check
                            else file_hash(path)
                        ),
                        "skill_cards_sha256": catalogue["skill_cards_sha256"],
                        "candidate_skill_ids_sha256": catalogue[
                            "candidate_skill_ids_sha256"
                        ],
                        "relations_sha256": catalogue.get("relations_sha256"),
                    }
                )
        record = {
            "task_id": task_id,
            "source_task_id": source_id,
            "task_origin": origin,
            "task_text_json_sha256": stable_hash(task["prompt_zh"]),
            "gold_json_sha256": stable_hash(task),
            "gold_relevant_skills": {
                "skill_ids": relevant_ids,
                "count": len(relevant_ids),
                "sources": relevant_sources,
                "sources_complete": True,
                "derivation_rule": (
                    "Union of required, optional, forbidden, initial states, "
                    "expected blockers, canonical sequence, hard-order endpoints, "
                    "conflict endpoints, mutex route Skills, and blocked downstream Skills."
                ),
            },
            "pools": pools,
        }
        pool_records.append(record)
        relevant_report.append(
            {
                "task_id": task_id,
                "source_task_id": source_id,
                "count": len(relevant_ids),
                "skill_ids": relevant_ids,
                "sources": relevant_sources,
            }
        )

    pool_manifest = {
        "schema_version": "E1V2-1.0",
        "experiment_id": "E1V2",
        "hash_algorithm": "SHA-256",
        "hash_canonicalization": "UTF-8 compact JSON with sort_keys=true",
        "task_count": 21,
        "pool_sizes": [10, 30, 46],
        "full_skill_set_source": str(FULL_A.relative_to(ROOT)),
        "full_skill_set_source_sha256": file_hash(FULL_A),
        "deterministic_distractor_rule": {
            "freeze_time": "before_formal_model_calls",
            "inputs": [
                "GoldRelevantSkills",
                "canonical department ownership",
                "frozen full relation graph adjacency",
                "canonical Skill ID token similarity",
                "task-text department keyword hints",
            ],
            "priority": (
                "descending fixed score, then ascending canonical skill_id; "
                "S10 takes the first 10, S30 the first 30, S46 all 46"
            ),
            "post_result_adjustment_allowed": False,
        },
        "tasks": pool_records,
    }
    install(
        CATALOGUE_ROOT / "candidate_pool_manifest.json",
        pool_manifest,
        check=check,
    )
    install(
        GOLD_DIR / "gold_relevant_skills.json",
        {
            "schema_version": "E1V2-1.0",
            "experiment_id": "E1V2",
            "task_count": 21,
            "records": relevant_report,
        },
        check=check,
    )

    catalogue_manifest = {
        "schema_version": "E1V2-1.0",
        "experiment_id": "E1V2",
        "catalogue_count": len(catalogue_manifest_records),
        "expected_catalogue_count": 21 * 3 * 3,
        "source_full_catalogues": {
            "A": {
                "path": str(FULL_A.relative_to(ROOT)),
                "sha256": file_hash(FULL_A),
            },
            "B": {
                "path": str(FULL_B.relative_to(ROOT)),
                "sha256": file_hash(FULL_B),
            },
            "C": {
                "path": str(FULL_C.relative_to(ROOT)),
                "sha256": file_hash(FULL_C),
            },
        },
        "catalogues": catalogue_manifest_records,
    }
    install(
        CATALOGUE_ROOT / "catalogue_manifest.json",
        catalogue_manifest,
        check=check,
    )

    validation = validate_generated(
        gold=gold,
        pool_manifest=pool_manifest,
        full_c=full_c,
        check=check,
    )
    install(
        CATALOGUE_ROOT / "setup_validation_report.json",
        validation,
        check=check,
    )
    install(
        CATALOGUE_ROOT / "candidate_pool_validation_report.json",
        {
            "schema_version": "E1V2-1.0",
            "experiment_id": "E1V2",
            "status": validation["status"],
            "valid": validation["valid"],
            "task_count": validation["task_count"],
            "checks": {
                key: validation["checks"][key]
                for key in (
                    "task_count_unique_21",
                    "gold_relevant_at_most_10",
                    "nested_pool_sizes",
                    "gold_relevant_in_s10",
                )
            },
            "errors": [
                item
                for item in validation["errors"]
                if any(
                    token in item
                    for token in (
                        "task_count",
                        "gold_relevant",
                        "pool_nesting",
                    )
                )
            ],
            "formal_model_tasks_started": 0,
        },
        check=check,
    )
    install(
        CATALOGUE_ROOT / "catalogue_validation_report.json",
        {
            "schema_version": "E1V2-1.0",
            "experiment_id": "E1V2",
            "status": validation["status"],
            "valid": validation["valid"],
            "catalogue_count": validation["catalogue_count"],
            "checks": {
                key: validation["checks"][key]
                for key in (
                    "abc_skill_cards_identical",
                    "ab_relations_absent",
                    "c_complete_induced_subgraph",
                    "catalogue_gold_leak_absent",
                )
            },
            "errors": [
                item
                for item in validation["errors"]
                if any(
                    token in item
                    for token in (
                        "abc_cards",
                        "relation",
                        "induced_subgraph",
                        "gold_leak",
                    )
                )
            ],
            "formal_model_tasks_started": 0,
        },
        check=check,
    )
    return validation


def flatten_catalogue(catalogue: dict[str, Any]) -> list[dict[str, Any]]:
    if catalogue["configuration"] == "A":
        return catalogue["skills"]
    return [
        card
        for department in catalogue["departments"]
        for card in department["skills"]
    ]


def validate_generated(
    *,
    gold: dict[str, Any],
    pool_manifest: dict[str, Any],
    full_c: dict[str, Any],
    check: bool,
) -> dict[str, Any]:
    errors = []
    task_ids = [task["task_id"] for task in gold["tasks"]]
    if len(task_ids) != 21 or len(set(task_ids)) != 21:
        errors.append("task_count_or_uniqueness")
    for record in pool_manifest["tasks"]:
        task_id = record["task_id"]
        relevant = set(record["gold_relevant_skills"]["skill_ids"])
        pools = {
            size: record["pools"][size]["skill_ids"]
            for size in ("10", "30", "46")
        }
        if len(relevant) > 10:
            errors.append(f"{task_id}:gold_relevant_over_10")
        if not relevant <= set(pools["10"]):
            errors.append(f"{task_id}:gold_relevant_missing_from_s10")
        if not (
            len(pools["10"]) == 10
            and len(pools["30"]) == 30
            and len(pools["46"]) == 46
            and set(pools["10"]) < set(pools["30"]) < set(pools["46"])
        ):
            errors.append(f"{task_id}:pool_nesting")
        for size in ("10", "30", "46"):
            directory = CATALOGUE_ROOT / "tasks" / task_id / f"size_{size}"
            catalogues = {
                configuration: load_json(directory / filename)
                for configuration, filename in CONFIGURATION_FILENAMES.items()
            }
            cards = {
                configuration: {
                    card["skill_id"]: card
                    for card in flatten_catalogue(catalogue)
                }
                for configuration, catalogue in catalogues.items()
            }
            if not cards["A"] == cards["B"] == cards["C"]:
                errors.append(f"{task_id}:{size}:abc_cards")
            if (
                "relations" in catalogues["A"]
                or "relation_semantics" in catalogues["A"]
                or "relations" in catalogues["B"]
                or "relation_semantics" in catalogues["B"]
            ):
                errors.append(f"{task_id}:{size}:ab_relation_leak")
            expected_relations = relation_subset(full_c, set(cards["C"]))
            if catalogues["C"]["relations"] != expected_relations:
                errors.append(f"{task_id}:{size}:not_induced_subgraph")
            for catalogue in catalogues.values():
                leaks = recursive_keys(catalogue) & GOLD_LEAK_KEYS
                if leaks:
                    errors.append(
                        f"{task_id}:{size}:{catalogue['configuration']}:gold_leak:{sorted(leaks)}"
                    )
    return {
        "schema_version": "E1V2-1.0",
        "experiment_id": "E1V2",
        "status": "passed" if not errors else "failed",
        "valid": not errors,
        "checks": {
            "task_count_unique_21": not any(
                "task_count_or_uniqueness" in item for item in errors
            ),
            "gold_relevant_at_most_10": not any(
                "gold_relevant_over_10" in item for item in errors
            ),
            "nested_pool_sizes": not any(
                "pool_nesting" in item for item in errors
            ),
            "gold_relevant_in_s10": not any(
                "gold_relevant_missing_from_s10" in item for item in errors
            ),
            "abc_skill_cards_identical": not any(
                "abc_cards" in item for item in errors
            ),
            "ab_relations_absent": not any(
                "ab_relation_leak" in item for item in errors
            ),
            "c_complete_induced_subgraph": not any(
                "not_induced_subgraph" in item for item in errors
            ),
            "catalogue_gold_leak_absent": not any(
                "gold_leak" in item for item in errors
            ),
        },
        "task_count": len(task_ids),
        "catalogue_count": 21 * 3 * 3,
        "errors": errors,
        "generation_mode": "deterministic_builder",
        "formal_model_tasks_started": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = build(args.check)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
