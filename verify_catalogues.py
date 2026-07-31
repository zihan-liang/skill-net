#!/usr/bin/env python3
"""Verify Catalogue integrity for SkillNet Common Adapter Setup"""
import json, hashlib, subprocess, sys
from pathlib import Path

REPO = str(Path(__file__).resolve().parent)

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

print("=" * 60)
print("CATALOGUE HASH VERIFICATION")
print("=" * 60)

# Compute hashes
catalogues = [
    ("size_10/A_flat_catalogue.json", "size_10", "A"),
    ("size_10/B_department_grouped_catalogue.json", "size_10", "B"),
    ("size_10/C_graph_structured_catalogue.json", "size_10", "C"),
    ("size_30/A_flat_catalogue.json", "size_30", "A"),
    ("size_30/B_department_grouped_catalogue.json", "size_30", "B"),
    ("size_30/C_graph_structured_catalogue.json", "size_30", "C"),
    ("size_46/A_flat_catalogue.json", "size_46", "A"),
    ("size_46/B_department_grouped_catalogue.json", "size_46", "B"),
    ("size_46/C_graph_structured_catalogue.json", "size_46", "C"),
]

with open(f"{REPO}/skillnet_run_guide_v1_1/catalogues/catalogue_manifest.json") as f:
    manifest = json.load(f)

# Build manifest hash lookup
manifest_hashes = {}
for c in manifest.get("catalogues", []):
    path = c.get("path", "")
    if "A_flat" in path or "B_department" in path or "C_graph" in path:
        manifest_hashes[path] = c["file_sha256"]

all_ok = True
for rel_path, size, cfg in catalogues:
    full_path = f"{REPO}/skillnet_run_guide_v1_1/catalogues/{rel_path}"
    computed = sha256_file(full_path)
    manifest_key = f"skillnet_run_guide_v1_1/catalogues/{rel_path}"
    expected = manifest_hashes.get(manifest_key, "NOT_FOUND")
    match = computed == expected
    status = "✅" if match else "❌"
    if not match:
        all_ok = False
    print(f"  {status} {size}/{cfg}: computed={computed[:16]}... expected={expected[:16]}...")

print(f"\n  Overall hash match: {'✅ PASS' if all_ok else '❌ FAIL'}")

print("\n" + "=" * 60)
print("A/B/C CONSISTENCY VERIFICATION")
print("=" * 60)

for size in ["10", "30", "46"]:
    base = f"{REPO}/skillnet_run_guide_v1_1/catalogues/size_{size}"
    
    with open(f"{base}/A_flat_catalogue.json") as f:
        a = json.load(f)
    with open(f"{base}/B_department_grouped_catalogue.json") as f:
        b = json.load(f)
    with open(f"{base}/C_graph_structured_catalogue.json") as f:
        c = json.load(f)
    
    # Extract skills from A
    a_skills = a.get("skills", [])
    
    # Extract skills from B (department-grouped)
    b_skills = []
    for dept in b.get("departments", []):
        b_skills.extend(dept.get("skills", []))
    
    # Extract skills from C (graph-structured, department-grouped)
    c_skills = []
    for dept in c.get("departments", []):
        c_skills.extend(dept.get("skills", []))
    
    a_ids = set(s["skill_id"] for s in a_skills)
    b_ids = set(s["skill_id"] for s in b_skills)
    c_ids = set(s["skill_id"] for s in c_skills)
    
    print(f"\n  Size {size}:")
    print(f"    A count: {len(a_ids)}, B count: {len(b_ids)}, C count: {len(c_ids)}")
    print(f"    A==B: {'✅' if a_ids == b_ids else '❌'}")
    print(f"    B==C: {'✅' if b_ids == c_ids else '❌'}")
    print(f"    A is flat (no departments): {'✅' if 'departments' not in a else '❌'}")
    
    # Check B/C department grouping consistency
    b_depts = {d["department_id"]: set(s["skill_id"] for s in d.get("skills", []))
               for d in b.get("departments", [])}
    c_depts = {d["department_id"]: set(s["skill_id"] for s in d.get("skills", []))
               for d in c.get("departments", [])}
    
    if b_depts and c_depts:
        print(f"    B departments: {sorted(b_depts.keys())}")
        print(f"    C dept grouping == B: {'✅' if b_depts == c_depts else '❌'}")
    
    # Check C has relations
    c_relations = c.get("relations", [])
    print(f"    C has relations: {'✅' if c_relations else '❌'}")
    print(f"    C relation count: {len(c_relations)}")
    
    # Check C relation_semantics
    c_semantics = c.get("relation_semantics", {})
    print(f"    C has relation_semantics: {'✅' if c_semantics else '❌'}")
    
    # Check C only adds relations to B structure
    c_extra_keys = set(c.keys()) - set(b.keys())
    print(f"    C extra keys vs B: {c_extra_keys}")

print("\n" + "=" * 60)
print("GOLD TASKS & EVALUATOR CHECK")
print("=" * 60)

# Check Gold prompts
import os
prompts_dir = f"{REPO}/SkillNet_Gold_Tasks_V4/prompts"
prompt_files = sorted(os.listdir(prompts_dir))
print(f"  Gold prompts: {len(prompt_files)} files")
for pf in prompt_files:
    print(f"    {pf}")

# Check evaluator
eval_dir = f"{REPO}/SkillNet_Gold_Tasks_V4/evaluation"
eval_files = sorted(os.listdir(eval_dir))
print(f"\n  Evaluation files: {len(eval_files)}")
for ef in eval_files:
    ef_path = os.path.join(eval_dir, ef)
    if os.path.isdir(ef_path):
        print(f"    {ef}/ (dir)")
    else:
        print(f"    {ef}")

# Check prediction schema
with open(f"{eval_dir}/prediction_schema.json") as f:
    schema = json.load(f)
print(f"\n  Prediction schema loaded: ✅")
print(f"    Schema type: {schema.get('type', 'N/A')}")

# Check evaluator script exists
eval_script = f"{eval_dir}/evaluate_skillnet.py"
print(f"  Evaluator script exists: {'✅' if os.path.exists(eval_script) else '❌'}")

# Check E1 gold tasks
e1_path = f"{REPO}/experiments/skillnet/frozen_eval/E1_Gold_5_tasks.json"
with open(e1_path) as f:
    e1 = json.load(f)
if isinstance(e1, list):
    print(f"\n  E1 Gold 5 tasks: {len(e1)} task definitions")
elif isinstance(e1, dict):
    print(f"\n  E1 Gold 5 tasks: keys = {list(e1.keys())}")

print("\n" + "=" * 60)
print("EXPERIMENT FRAMEWORK CHECK")
print("=" * 60)

exp_dir = f"{REPO}/experiments/skillnet"
for item in ["RUNBOOK.md", "run_condition.py", "verify_condition.py", 
             "requirements.txt", "tests/test_artifact_contract.py",
             "frozen_eval/E1_Gold_5_tasks.json", "frozen_eval/E1_Gold_5_tasks_validation.json"]:
    path = f"{exp_dir}/{item}"
    print(f"  {item}: {'✅' if os.path.exists(path) else '❌'}")

print("\n" + "=" * 60)
print("COMMIT INFO")
print("=" * 60)
result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO)
head = result.stdout.strip()
print(f"  HEAD: {head}")
print(f"  Manifest source_commit: {manifest['source_commit']}")

print("\n✅ Common Adapter Setup verification complete.")
print("❌ Issues found" if not all_ok else "")
