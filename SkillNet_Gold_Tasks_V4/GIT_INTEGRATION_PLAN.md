# Git Integration Plan — Do Not Execute Before Approval

## Current comparison

- Authoritative main: `cdb4ecdf838fdd4e0bbb01e4c766b32eb430eb47`
- Current package branch: `codex/hr-skills`
- Current package-branch tip: `62910cb97d6fb9e05b1895825106355724be3658`
- Merge-base: `bbc590da94c54afbfedacb6f962805d12d29b816`
- Divergence: 47 commits only on main; 2 commits only on `codex/hr-skills`
- Paths changed on both sides since the merge-base: none
- `SkillNet_Gold_Tasks_V4` currently exists on `codex/hr-skills` but not on main.

Although there is no same-path conflict, `codex/hr-skills` is far behind main.
Comparing its complete tree directly with main shows many main files as absent.
Using that old branch directly for integration would create a noisy and risky
review even though the package paths themselves are isolated.

## Recommended integration method

After review and explicit approval:

1. Fetch and fast-forward from the latest main.
2. Create a clean feature branch from that exact main.
3. Copy only the approved bilingual package into
   `SkillNet_Gold_Tasks_V4/`.
4. Re-run authoritative and package tests.
5. Review the staged diff, especially ensuring no `.agents/skills`, test, or
   relation source from main is changed.
6. Commit the package in one clear commit.
7. Push the clean feature branch.
8. Open a pull request into main and review before merging.

Do not merge, push, delete the old branch, or rewrite main as part of the current
review phase.

## Proposed commands for the later approved phase

These commands are a plan only and have not been executed:

```bash
cd /Users/xrx/Desktop/SJTU_Summer_School/skill-net

git status --short --branch
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c codex/skillnet-gold-v4-english

mkdir -p SkillNet_Gold_Tasks_V4
rsync -a --exclude='.DS_Store' \
  /Users/xrx/Desktop/SJTU_Summer_School/SkillNet_Gold_Tasks_V4_English_Bilingual/ \
  SkillNet_Gold_Tasks_V4/

python3 SkillNet_Gold_Tasks_V4/evaluation/evaluate_skillnet.py validate-package \
  --gold SkillNet_Gold_Tasks_V4/02_Gold_Standard_21_V4.json \
  --output SkillNet_Gold_Tasks_V4/results/package_validation_report.json

SKILLNET_MAIN_ROOT="$(pwd)" \
SKILLNET_ORIGINAL_PACKAGE=/Users/xrx/Desktop/SJTU_Summer_School/skill-net/SkillNet_Gold_Tasks_V4 \
PYTHONDONTWRITEBYTECODE=1 \
python3 -m unittest discover \
  -s SkillNet_Gold_Tasks_V4/evaluation/tests -v

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v

git status --short
git diff -- SkillNet_Gold_Tasks_V4
git add SkillNet_Gold_Tasks_V4
git diff --cached --check
git diff --cached --stat
git diff --cached --name-status

git commit -m "feat: add bilingual SkillNet Gold Tasks V4"
git push -u origin codex/skillnet-gold-v4-english

gh pr create \
  --base main \
  --head codex/skillnet-gold-v4-english \
  --title "Add bilingual SkillNet Gold Tasks V4" \
  --body-file SkillNet_Gold_Tasks_V4/CHANGE_REPORT.md
```

Before the later commit, verify that `git diff --cached --name-only` contains only
paths under `SkillNet_Gold_Tasks_V4/`.

## Likely conflicts

- Direct content conflicts in the package path are currently unlikely because
  main does not contain the package.
- The principal risk is branch-level divergence: using `codex/hr-skills` directly
  could present unrelated main content as deletions or regressions.
- If main gains a `SkillNet_Gold_Tasks_V4/` directory before approval, regenerate
  the comparison from the new main and manually review every overlapping file
  before staging.
- If main changes canonical Skill IDs, titles, department IDs, or relation
  membership, rerun the mapping and all validation tests before integration.

## Rollback strategy

Before merge, simply close the future pull request or abandon the clean feature
branch; main remains unchanged. No deletion of `codex/hr-skills` is recommended
or required.
