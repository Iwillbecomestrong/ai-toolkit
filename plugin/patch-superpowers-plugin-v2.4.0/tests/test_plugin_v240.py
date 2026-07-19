from pathlib import Path
import importlib.util
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), path
    _, raw, _ = text.split("---", 2)
    result = {}
    for line in raw.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip('"')
    return result


def test_native_plugin_manifest_and_no_hooks():
    manifest = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "patch-superpowers"
    assert manifest["version"] == "2.4.0"
    assert manifest["defaultEnabled"] is True
    assert not (ROOT / "hooks").exists()


def test_all_skill_folders_and_names_are_patch_prefixed():
    dirs = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
    assert dirs
    for directory in dirs:
        assert directory.name.startswith("patch-"), directory.name
        fm = parse_frontmatter(directory / "SKILL.md")
        assert fm["name"] == directory.name
    assert {p.name for p in dirs} == {
        "patch-using-superpowers",
        "patch-brainstorming",
        "patch-writing-plans",
        "patch-challenging-plans",
        "patch-parallel-dag-development",
        "patch-dag-worktree-development",
        "patch-subagent-driven-development",
        "patch-sol-final-audit",
    }


def test_agents_are_patch_prefixed_and_only_claude_roles_exist():
    agents = {p.name for p in (ROOT / "agents").glob("*.md")}
    assert agents == {
        "patch-investigator.md",
        "patch-plan-challenger.md",
        "patch-tdd-implementer.md",
        "patch-integration-operator.md",
    }
    for path in (ROOT / "agents").glob("*.md"):
        fm = parse_frontmatter(path)
        assert fm["name"].startswith("patch-")
        assert fm["model"] == "inherit"
    combined = "\n".join(p.read_text(encoding="utf-8").lower() for p in (ROOT / "agents").glob("*.md"))
    assert "luna reviewer agent" not in combined
    assert "sol planner agent" not in combined


def test_brainstorming_classifies_inputs_and_defers_references():
    skill = (ROOT / "skills/patch-brainstorming/SKILL.md").read_text(encoding="utf-8")
    template = (ROOT / "skills/patch-brainstorming/INPUT_SOURCE_CLASSIFICATION_TEMPLATE.md").read_text(encoding="utf-8")
    for token in ["MUST_FOLLOW", "CONFIRMED_FACTS", "UNKNOWN", "REFERENCE_ONLY_PATHS"]:
        assert token in skill and token in template
    assert "NOT_READ" in template
    assert "默认不得读取" in skill
    assert "先调查代码" in skill


def test_reference_access_is_explicit_and_claims_need_confirmation():
    request = (ROOT / "skills/patch-brainstorming/REFERENCE_ACCESS_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")
    claims = (ROOT / "skills/patch-brainstorming/REFERENCE_CLAIM_VALIDATION_TEMPLATE.md").read_text(encoding="utf-8")
    assert "REFERENCE_ACCESS_REQUIRED" in request
    assert "failed_approaches" in request
    assert "UNVERIFIED_REFERENCE" in claims
    for status in ["CONFIRMED", "FALSIFIED", "INCONCLUSIVE"]:
        assert status in claims


def test_sol_core_prompt_does_not_read_reference_body_initially():
    prompt = (ROOT / "skills/patch-writing-plans/SOL_CORE_PLANNER_PROMPT.md").read_text(encoding="utf-8")
    assert "REFERENCE_ONLY_PATHS" in prompt
    assert "不得读取其正文" in prompt
    assert "REFERENCE_ACCESS_REQUIRED" in prompt
    assert "REFERENCE_SOLUTIONS.md" not in prompt
    assert "MUST_FOLLOW_INDEX.md" in prompt


def test_planning_state_validator_enforces_reference_and_must_follow_rules():
    module = load("planning_v240", "bin/patch-superpowers-validate-planning.py")
    state = json.loads((ROOT / "skills/patch-writing-plans/PLANNING_STATE_TEMPLATE.json").read_text(encoding="utf-8"))
    state["must_follow_files"] = [{"id": "MF-1", "status": "READ_AND_APPLIED"}]
    state["core_plan"]["must_follow_coverage"] = ["MF-1"]
    state["core_plan"]["challenge_status"] = "PASS"
    state["core_plan"]["user_approval"] = "APPROVED"
    state["core_plan"]["approval_id"] = "CPA-1"
    state["detailed_plan"]["status"] = "READY"
    state["detailed_plan"]["challenge_status"] = "PASS"
    assert module.validate_state(state) == []

    bad_must = json.loads(json.dumps(state))
    bad_must["must_follow_files"][0]["status"] = "NOT_READ"
    assert any("MUST_FOLLOW" in e for e in module.validate_state(bad_must))

    early_ref = json.loads(json.dumps(state))
    early_ref["reference_only_paths"] = [{"id": "REF-1", "read_status": "READ", "access_status": "NOT_REQUESTED"}]
    assert any("参考" in e for e in module.validate_state(early_ref))

    unverified = json.loads(json.dumps(state))
    unverified["reference_claims"] = [{"id": "UR-1", "status": "UNVERIFIED_REFERENCE", "used_in_plan": True}]
    assert any("UNVERIFIED_REFERENCE" in e for e in module.validate_state(unverified))


def test_exact_codex_model_routes_and_resume():
    config = json.loads((ROOT / "config/model-routing.json").read_text(encoding="utf-8"))
    roles = config["codex_cli_roles"]
    for role in ["core_planner", "detailed_planner", "repair_planner", "plan_patch", "final_auditor"]:
        assert roles[role]["model"] == "gpt-5.6-sol"
        assert roles[role]["reasoning_effort"] == "medium"
    for role in ["task_reviewer", "integration_reviewer"]:
        assert roles[role]["model"] == "gpt-5.6-luna"
        assert roles[role]["reasoning_effort"] == "medium"
    assert roles["architecture_reviewer"]["reasoning_effort"] == "high"

    workflow = load("codex_v240", "bin/patch-superpowers-codex-workflow.py")
    cfg = workflow.load_config(ROOT / "config/model-routing.json")
    core = workflow.build_role_command(cfg, "core_planner")
    assert core[:4] == ["codex", "exec", "-m", "gpt-5.6-sol"]
    detail = workflow.build_role_command(cfg, "detailed_planner", thread_id="thread-1")
    assert detail[-3:] == ["resume", "thread-1", "-"]
    assert 'model_reasoning_effort="medium"' in detail


def test_patch_skills_do_not_route_to_replaced_original_skills():
    text = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "skills").rglob("*.md"))
    for scoped in [
        "patch-superpowers:patch-brainstorming",
        "patch-superpowers:patch-writing-plans",
        "patch-superpowers:patch-challenging-plans",
        "patch-superpowers:patch-dag-worktree-development",
    ]:
        assert scoped in text
    forbidden = ["superpowers:brainstorming", "superpowers:writing-plans", "superpowers:dag-worktree-development"]
    for token in forbidden:
        assert token not in text


def test_no_wave_cluster_or_legacy_overlay_names():
    text = "\n".join(str(p.relative_to(ROOT)).lower() for p in ROOT.rglob("*"))
    for token in ["task-wave", "cluster-worktree", "wave-integration", "_dag-runtime"]:
        assert token not in text


def test_installer_targets_skills_directory_plugin_and_preserves_original():
    text = (ROOT / "Install.ps1").read_text(encoding="utf-8")
    assert ".claude\\skills\\patch-superpowers" in text
    assert "CleanLegacyOverlay" in text
    assert "brainstorming" in text  # explicit preserve checks
    assert "writing-plans" in text
    assert "Remove-Item $original" not in text


def test_python_scripts_compile():
    scripts = list((ROOT / "bin").glob("*.py")) + [ROOT / "Verify-Package.py"]
    result = subprocess.run([sys.executable, "-m", "py_compile", *map(str, scripts)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

def test_legacy_cleanup_never_deletes_original_superpowers_skills():
    text = (ROOT / "Install.ps1").read_text(encoding="utf-8")
    cleanup_match = re.search(r"\$legacySkills\s*=\s*@\((.*?)\)", text, re.S)
    assert cleanup_match
    cleanup = cleanup_match.group(1)
    for original_name in ["brainstorming", "writing-plans", "using-superpowers", "subagent-driven-development"]:
        assert f"'{original_name}'" not in cleanup
