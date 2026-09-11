"""Acceptance gate for the approved VYD v1.1 canonical bundle."""
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
VYD = ROOT / "catalog/warehouse/vydajky"


def load(name):
    return yaml.safe_load((VYD / name).read_text(encoding="utf-8"))


class VYDV11AcceptanceTests(unittest.TestCase):
    def test_complete_physical_field_inventories(self):
        expected = {"VYD_L": 67, "VYD_O": 34, "VYD_O_P_PRIJ": 5}
        for name, count in expected.items():
            records = load(f"fields-{name.lower()}.yaml")["records"]
            self.assertEqual(count, len(records), name)
            self.assertEqual(list(range(1, count + 1)), sorted(r["ordinal_position"] for r in records))
            self.assertEqual(count, len({r["field_id"] for r in records}))

    def test_all_39_triggers_and_source_flows_are_present(self):
        entities = load("oracle-entities.yaml")["records"]
        trigger_names = {r["oracle_name"] for r in entities if r["oracle_object_type"] == "TRIGGER"}
        flows = load("flows.yaml")["records"]
        self.assertEqual(39, len(flows))
        self.assertEqual(39, len({r["trigger_or_procedure_ref"] for r in flows}))
        # Some trigger identities may resolve to an already accepted cross-domain entity.
        all_entity_docs = list((ROOT / "catalog").rglob("oracle-entities.yaml"))
        all_triggers = set(trigger_names)
        for path in all_entity_docs:
            all_triggers.update(r["oracle_name"] for r in yaml.safe_load(path.read_text())["records"]
                                if r["oracle_object_type"] == "TRIGGER")
        self.assertEqual(39, len({r["trigger_or_procedure_ref"].split(".")[-1] for r in flows}))
        self.assertGreaterEqual(len(all_triggers), 39)

    def test_direct_dependency_surface(self):
        doc = load("dependency-direct-edges.yaml")
        records = doc["records"]
        self.assertEqual(632, len(records))
        self.assertEqual(316, len({(r["source_owner"], r["source_name"], r["source_type"]) for r in records}))
        self.assertTrue(all(r["min_depth"] == 1 for r in records))

    def test_edges_and_closure_nodes_are_distinct_and_complete(self):
        edge_doc = load("dependency-closure-edges.yaml")
        node_doc = load("dependency-closure-nodes.yaml")
        self.assertEqual("dependency-edges", edge_doc["kind"])
        self.assertEqual("dependency-nodes", node_doc["kind"])
        self.assertEqual(63622, len(edge_doc["records"]))
        inbound = [r for r in node_doc["records"] if r["direction"] == "INBOUND"]
        outbound = [r for r in node_doc["records"] if r["direction"] == "OUTBOUND"]
        self.assertEqual(5274, len(inbound))
        self.assertEqual(370, len(outbound))
        self.assertEqual(5, max(r["min_depth"] for r in inbound))
        self.assertEqual(4, max(r["min_depth"] for r in outbound))

    def test_api_source_hits_are_not_runtime_roles(self):
        records = []
        for path in sorted(VYD.glob("api-references-part*.yaml")):
            records.extend(yaml.safe_load(path.read_text(encoding="utf-8"))["records"])
        self.assertEqual(742, len(records))
        self.assertEqual(112, len({(r["caller_owner"], r["caller_name"], r["caller_type"]) for r in records}))
        self.assertEqual(1790, sum(r["hit_count"] for r in records))
        self.assertEqual(216, len({(r["target_package"], r["member_name_raw"].lower()) for r in records}))
        self.assertEqual({"SOURCE MEMBER REFERENCE"}, {r["classification"] for r in records})

    def test_confirmed_direct_writer_register(self):
        writers = [r for r in load("dependencies.yaml")["records"]
                   if r["role"] == "DIRECT WRITER"]
        self.assertEqual(73, len({r["source_ref"] for r in writers}))
        by_target = {}
        for target in ("mc.object.vyd_l", "mc.object.vyd_o", "mc.object.vyd_o_p_prij"):
            by_target[target] = len({r["source_ref"] for r in writers if r["target_ref"] == target})
        self.assertEqual({"mc.object.vyd_l": 54, "mc.object.vyd_o": 40,
                          "mc.object.vyd_o_p_prij": 2}, by_target)
        self.assertTrue(all(r["status"] == "POTVRDENÉ" for r in writers))

    def test_access_capability_is_not_promoted_to_runtime_use(self):
        records = load("dependencies.yaml")["records"]
        grants = [r for r in records if r["discovery_method"] == "ALL_TAB_PRIVS"]
        self.assertEqual(35, len(grants))
        self.assertEqual({"ACCESS CAPABILITY"}, {r["role"] for r in grants})

    def test_polymorphic_routing_keeps_join_validation_separate(self):
        poly = next(r for r in load("relationships.yaml")["records"]
                    if r["relationship_id"] == "vyd.rel.line_source_polymorphic")
        self.assertEqual(3, len(poly["targets"]))
        by_prefix = {r["selector_condition_sk"].split("'")[1]: r for r in poly["targets"]}
        self.assertIn("2 486 928 / 2 486 928", by_prefix["019"]["validation_summary_sk"])
        self.assertIn("294 068 / 294 068", by_prefix["003"]["validation_summary_sk"])
        rek = by_prefix["021"]
        self.assertEqual("TREBA OVERIŤ", rek["status"])
        self.assertIn("nie je dôkaz JOINu", rek["safe_usage_sk"])

    def test_agent_ready_and_zero_blocking_backlog(self):
        self.assertEqual("AGENT-READY", load("contract.yaml")["maturity"])
        for name in ("vyd_l", "vyd_o", "vyd_o_p_prij"):
            self.assertEqual("AGENT-READY", load(f"object-{name}.yaml")["maturity"])
        self.assertFalse(any(r["blocking"] for r in load("backlog.yaml")["records"]))

    def test_canonical_sql_registry(self):
        records = load("sql-registry.yaml")["records"]
        self.assertEqual(8, len(records))
        for record in records:
            self.assertEqual("SQL Navigator 5.5.4.847", record["compatibility"]["sql_client"])
            self.assertIsNone(record["compatibility"]["oracle_server_version"])
            self.assertIs(True, record["compatibility"]["read_only"])
            self.assertTrue((ROOT / record["sql_file"]).is_file())


if __name__ == "__main__":
    unittest.main()
