import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "SkillNet_Gold_Tasks_V4"
GOLD_PATH = PACKAGE / "02_Gold_Standard_21_V4.json"
EVALUATOR_PATH = PACKAGE / "evaluation" / "evaluate_skillnet.py"
RUNNER_PATH = PACKAGE / "evaluation" / "run_experiments.py"
PREDICTION_SCHEMA_PATH = PACKAGE / "evaluation" / "prediction_schema.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_gold():
    return json.loads(GOLD_PATH.read_text(encoding="utf-8"))


def project_skill_names():
    return {
        path.name
        for path in (ROOT / ".agents" / "skills").iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    }


def task_skill_references(task):
    references = set()
    for field in (
        "required_skills",
        "optional_skills",
        "canonical_sequence",
        "expected_blocked_by",
    ):
        references.update(task.get(field, []))
    references.update(
        skill
        for skill in task.get("forbidden_skills", [])
        if skill != "ALL_BUSINESS_SKILLS"
    )
    references.update(task.get("initial_skill_states", {}))
    for pair in task.get("hard_order_constraints", []):
        references.update((pair["before"], pair["after"]))
    for constraint in task.get("task_constraints", []):
        trigger = constraint.get("trigger_skill")
        if trigger:
            references.add(trigger)
        references.update(constraint.get("blocked_skills", []))
        references.update(constraint.get("forbidden_route_skills", []))
    return references


class GoldIdentifierTests(unittest.TestCase):
    def test_gold_catalog_exactly_matches_project_yaml_slugs(self):
        gold = load_gold()

        self.assertEqual(set(gold["skill_catalog"]), project_skill_names())

    def test_every_task_skill_reference_uses_a_project_yaml_slug(self):
        gold = load_gold()
        canonical = project_skill_names()

        invalid = {
            task["task_id"]: sorted(task_skill_references(task) - canonical)
            for task in gold["tasks"]
            if task_skill_references(task) - canonical
        }

        self.assertEqual(invalid, {})


class CandidateWorkspaceTests(unittest.TestCase):
    def prepare(self, configuration):
        self.assertTrue(RUNNER_PATH.is_file(), "experiment runner must exist")
        runner = load_module(RUNNER_PATH, f"skillnet_runner_{configuration}")
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        destination = Path(temporary.name) / configuration
        runner.prepare_candidate_workspace(
            repo_root=ROOT,
            package_root=PACKAGE,
            configuration=configuration,
            task_prompt_path=PACKAGE / "prompts" / "GT01_SINGLE.txt",
            destination=destination,
        )
        return destination

    def test_each_configuration_exposes_exactly_the_same_46_skills(self):
        expected = project_skill_names()

        for configuration in ("A", "B", "C"):
            with self.subTest(configuration=configuration):
                workspace = self.prepare(configuration)
                exposed = {
                    path.name
                    for path in (workspace / ".agents" / "skills").iterdir()
                    if path.is_dir() and (path / "SKILL.md").is_file()
                }
                self.assertEqual(exposed, expected)

    def test_candidate_workspaces_expose_only_the_intended_treatment(self):
        expected_files = {
            "A": {"AGENTS.md", "task.txt"},
            "B": {"AGENTS.md", "department_groups.json", "task.txt"},
            "C": {"AGENTS.md", "skill_relations.json", "task.txt"},
        }

        for configuration, expected in expected_files.items():
            with self.subTest(configuration=configuration):
                workspace = self.prepare(configuration)
                visible = {
                    path.name
                    for path in workspace.iterdir()
                    if path.name != ".agents"
                }
                self.assertEqual(visible, expected)
                self.assertFalse((workspace / "SkillNet_Gold_Tasks_V4").exists())
                self.assertFalse((workspace / "evaluation").exists())


class EvaluatorStrictnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gold = load_gold()
        cls.evaluator = load_module(EVALUATOR_PATH, "skillnet_evaluator_strictness")
        cls.tasks = {task["task_id"]: task for task in cls.gold["tasks"]}

    def canonical_prediction(self, task_id):
        task = self.tasks[task_id]
        return {
            "task_id": task_id,
            "use_skills": task["use_skills"],
            "selected_departments": task["required_departments"],
            "skill_sequence": task["canonical_sequence"],
            "final_status": task["expected_final_status"],
            "blocked_by": task["expected_blocked_by"],
            "route_choice": task["expected_route_choice"],
            "reason": "strictness test",
        }

    def evaluate(self, task_id, prediction):
        return self.evaluator.evaluate_record(
            prediction,
            self.tasks[task_id],
            self.gold,
            "TEST",
            "1",
        )

    def test_extra_unknown_blocker_prevents_blocked_flow_success(self):
        prediction = self.canonical_prediction("GT17_SPECIAL_INVALID_INVOICE")
        prediction["blocked_by"] = [
            "finance-invoice-verification",
            "not-a-real-skill",
        ]

        result = self.evaluate("GT17_SPECIAL_INVALID_INVOICE", prediction)

        self.assertFalse(result["functional_success"])
        self.assertIn("UNKNOWN_BLOCKER", [result["primary_failure"], *result["secondary_failures"]])

    def test_unexpected_route_choice_prevents_success(self):
        prediction = self.canonical_prediction("GT18_SPECIAL_BUILD_OR_BUY")
        prediction["route_choice"] = {
            "build_or_buy": "internal_development",
            "unrequested_decision": "invented",
        }

        result = self.evaluate("GT18_SPECIAL_BUILD_OR_BUY", prediction)

        self.assertFalse(result["functional_success"])
        self.assertIn(
            "UNEXPECTED_ROUTE_CHOICE",
            [result["primary_failure"], *result["secondary_failures"]],
        )

    def test_prediction_loader_ignores_run_manifest_metadata(self):
        prediction = self.canonical_prediction("GT01_SINGLE")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "GT01_SINGLE.json").write_text(
                json.dumps(prediction, ensure_ascii=False),
                encoding="utf-8",
            )
            (root / "run_manifest.json").write_text(
                json.dumps({"configuration": "A", "task_ids": ["GT01_SINGLE"]}),
                encoding="utf-8",
            )

            records = self.evaluator.load_predictions(root)

        self.assertEqual([record["task_id"] for record in records], ["GT01_SINGLE"])


class ExperimentRunnerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_module(RUNNER_PATH, "skillnet_runner_contract")

    def test_codex_command_fixes_model_context_and_read_only_execution(self):
        command = self.runner.build_codex_command(
            codex_executable=Path("/opt/codex"),
            workspace=Path("/tmp/candidate"),
            schema_path=Path("/tmp/prediction_schema.json"),
            output_path=Path("/tmp/prediction.json"),
            model="gpt-test",
            reasoning_effort="medium",
            prompt="route this task",
        )

        self.assertEqual(command[:2], ["/opt/codex", "exec"])
        self.assertIn("--ephemeral", command)
        self.assertIn("--ignore-user-config", command)
        self.assertIn("--skip-git-repo-check", command)
        self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
        self.assertEqual(command[command.index("--model") + 1], "gpt-test")
        self.assertIn('model_reasoning_effort="medium"', command)
        self.assertEqual(command[command.index("--cd") + 1], "/tmp/candidate")
        self.assertEqual(command[-1], "route this task")

    def test_output_schema_avoids_unsupported_unique_items_keyword(self):
        schema = json.loads(PREDICTION_SCHEMA_PATH.read_text(encoding="utf-8"))

        def keyword_paths(value, path=()):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == "uniqueItems":
                        yield path + (key,)
                    yield from keyword_paths(child, path + (key,))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    yield from keyword_paths(child, path + (index,))

        self.assertEqual(list(keyword_paths(schema)), [])

    def test_output_schema_uses_closed_nullable_route_choice_fields(self):
        schema = json.loads(PREDICTION_SCHEMA_PATH.read_text(encoding="utf-8"))
        route_choice = schema["properties"]["route_choice"]

        self.assertFalse(route_choice["additionalProperties"])
        self.assertEqual(
            set(route_choice["properties"]),
            {"acceptance_route", "build_or_buy"},
        )
        self.assertEqual(
            set(route_choice["required"]),
            set(route_choice["properties"]),
        )

    def test_validate_prediction_removes_null_route_choices(self):
        prediction = {
            "task_id": "GT01_SINGLE",
            "use_skills": True,
            "selected_departments": ["Procurement Agent"],
            "skill_sequence": ["procurement-supplier-evaluation"],
            "final_status": "completed",
            "blocked_by": [],
            "route_choice": {
                "acceptance_route": None,
                "build_or_buy": None,
            },
            "reason": "single Skill route",
        }

        normalized = self.runner.validate_prediction(prediction, "GT01_SINGLE")

        self.assertEqual(normalized["route_choice"], {})

    def test_validate_prediction_requires_the_requested_task_id(self):
        prediction = {
            "task_id": "WRONG",
            "use_skills": False,
            "selected_departments": [],
            "skill_sequence": [],
            "final_status": "no_tool",
            "blocked_by": [],
            "route_choice": {},
            "reason": "none",
        }

        with self.assertRaisesRegex(ValueError, "task_id"):
            self.runner.validate_prediction(prediction, "GT19_NO_TOOL_CLEAR")

    def test_run_manifest_records_all_controlled_variables(self):
        manifest = self.runner.build_run_manifest(
            configuration="C",
            run_id="1",
            task_ids=["GT01_SINGLE", "GT02_FIN_GOAL"],
            model="gpt-test",
            reasoning_effort="medium",
            codex_version="codex-cli test",
            max_workers=3,
        )

        self.assertEqual(manifest["configuration"], "C")
        self.assertEqual(manifest["task_ids"], ["GT01_SINGLE", "GT02_FIN_GOAL"])
        self.assertEqual(manifest["model"], "gpt-test")
        self.assertEqual(manifest["reasoning_effort"], "medium")
        self.assertEqual(manifest["codex_version"], "codex-cli test")
        self.assertEqual(manifest["max_workers"], 3)
        self.assertTrue(manifest["independent_ephemeral_sessions"])
        self.assertEqual(manifest["sandbox"], "read-only")


if __name__ == "__main__":
    unittest.main()
