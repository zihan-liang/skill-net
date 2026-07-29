# E1 规模实验关系文件使用说明

## 文件

- `E1_scale_manifest.json`：E1 五条任务、10-Skill 与 30-Skill 集合。
- `src/build_scaled_relations.py`：根据完整 `skill_relations.json` 生成闭合的 10/30/46 关系文件。
- `scale_relations/skill_relations_10.json`
- `scale_relations/skill_relations_30.json`
- `scale_relations/skill_relations_46.json`
- `scale_relations/scale_relations_validation_report.json`

## 重新生成

```bash
python src/build_scaled_relations.py \
  --relations path/to/skill_relations.json \
  --manifest E1_scale_manifest.json \
  --out-dir scale_relations
```

脚本会检查：

- 完整文件是否包含 46 个唯一原子 Skill；
- 10、30 集合的数量和 Skill ID 是否正确；
- `10 ⊂ 30 ⊂ 46` 是否成立；
- 裁剪后是否存在清单外 Skill 引用；
- 每个允许 Skill 是否仍出现在 `contains` 中。

## Configuration C 的使用原则

- 10-Skill 条件只读取 `skill_relations_10.json`；
- 30-Skill 条件只读取 `skill_relations_30.json`；
- 46-Skill 条件只读取 `skill_relations_46.json`；
- 同一会话不能同时访问完整关系文件或其他规模文件；
- Python 只生成和验证关系文件，不为 Codex 规划最终路线。
