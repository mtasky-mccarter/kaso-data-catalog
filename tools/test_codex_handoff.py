import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "check_codex_handoff.py"
SPEC = importlib.util.spec_from_file_location("check_codex_handoff", MODULE_PATH)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class CodexHandoffTests(unittest.TestCase):
    def valid_handoff(self):
        return {
            "schema_version": "1.0",
            "kind": "codex-handoff",
            "handoff_id": "x.handoff.1",
            "status": "READY_FOR_CODEX_HANDOFF",
            "repository": {
                "name": "mtasky-mccarter/kaso-data-catalog",
                "base_branch": "main",
                "base_commit": "abc123",
            },
            "scope": {
                "domain": "sales",
                "slug": "example",
                "oracle_objects": ["MC.EXAMPLE"],
                "authoritative_environment": "MC",
                "canonical_path": "catalog/sales/example/",
            },
            "target": {
                "maturity": "AGENT-READY",
                "documentation_version": "1.0",
                "breaking_change": False,
            },
            "semantic_contract": {"approved": True},
            "backlog": {"blocking_count": 0},
            "acceptance": {"unresolved_refs": 0, "duplicate_global_ids": 0},
            "publication": {"enabled": False},
            "execution": {"standard": "docs/codex-execution-standard-v3.md"},
            "repository_actions": {"merge_only_with_green_ci": True},
        }

    def test_valid_handoff_passes(self):
        errors, warnings = MOD.validate(self.valid_handoff())
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_agent_ready_rejects_blocking_backlog(self):
        handoff = self.valid_handoff()
        handoff["backlog"]["blocking_count"] = 1
        errors, _ = MOD.validate(handoff)
        self.assertTrue(any("AGENT-READY" in error for error in errors))

    def test_required_placeholder_is_rejected(self):
        handoff = self.valid_handoff()
        handoff["repository"]["base_commit"] = "<sha>"
        errors, _ = MOD.validate(handoff)
        self.assertTrue(any("base_commit" in error for error in errors))

    def test_publication_requires_resolved_fields(self):
        handoff = self.valid_handoff()
        handoff["publication"] = {
            "enabled": True,
            "slug": "example",
            "subject_sk": "<subject>",
            "output_dir": "generated/example/",
            "generator_command": "python tools/generate_publication.py example",
        }
        errors, _ = MOD.validate(handoff)
        self.assertTrue(any("publication.subject_sk" in error for error in errors))

    def test_canonical_only_handoff_can_defer_documentation_version(self):
        handoff = self.valid_handoff()
        handoff['target'].update(contract_version='1.0', documentation_version=None)
        self.assertEqual([], MOD.validate(handoff)[0])
        handoff['publication']['enabled'] = True
        self.assertTrue(any('documentation_version' in e for e in MOD.validate(handoff)[0]))
        handoff['publication']['enabled'] = False
        handoff['target']['contract_version'] = '<version>'
        self.assertTrue(any('documentation_version' in e for e in MOD.validate(handoff)[0]))


if __name__ == "__main__":
    unittest.main()
