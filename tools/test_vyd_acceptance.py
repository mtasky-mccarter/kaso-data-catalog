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
        synonyms = [r for r in records if r["discovery_method"] == "ALL_SYNONYMS"]
        self.assertEqual(11, len(synonyms))
        self.assertEqual({"DEPENDENCY ONLY"}, {r["role"] for r in synonyms})

    def test_confirmed_facts_and_runtime_roles_have_non_e_evidence(self):
        evidence_classes = {}
        for path in (ROOT / "evidence/manifests/vyd").glob("*.yaml"):
            manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
            evidence_classes[manifest["evidence_id"]] = manifest["evidence_class"]
        runtime_roles = {"DIRECT WRITER", "API WRITER", "CORE DOMAIN", "CALLER", "READER"}
        excluded = {"dependency-closure-edges.yaml", "dependency-closure-nodes.yaml",
                    "dependency-direct-edges.yaml"}
        for path in VYD.glob("*.yaml"):
            if path.name in excluded:
                continue
            for record in yaml.safe_load(path.read_text(encoding="utf-8")).get("records", []):
                if record.get("status") == "POTVRDENÉ" or record.get("role") in runtime_roles:
                    refs = record.get("evidence_refs", [])
                    self.assertTrue(refs, record)
                    self.assertTrue(any(evidence_classes.get(ref) != "E" for ref in refs), record)

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

    def test_playbooks_use_deliberate_diagnostic_entry_points(self):
        records = {r["playbook_id"]: r for r in load("playbooks.yaml")["records"]}
        self.assertEqual({
            "vyd.playbook.01": "vyd.sql.01",
            "vyd.playbook.02": "vyd.sql.03",
            "vyd.playbook.03": "vyd.sql.05",
            "vyd.playbook.04": "vyd.sql.02",
            "vyd.playbook.05": "vyd.sql.01",
            "vyd.playbook.06": "vyd.sql.06",
            "vyd.playbook.07": "vyd.sql.07",
            "vyd.playbook.08": "vyd.sql.01",
        }, {key: row["first_sql_ref"] for key, row in records.items()})
        for row in records.values():
            self.assertTrue(row["proves_sk"], row["playbook_id"])
            self.assertTrue(row["does_not_prove_sk"], row["playbook_id"])
            self.assertTrue(row["dependency_or_boundary_refs"], row["playbook_id"])
        self.assertIn("vyd.flow.t_vyd_o_rez", records["vyd.playbook.04"]["flow_refs"])
        self.assertIn("vyd.flow.t_vyd_o_kontrola_na_fak",
                      records["vyd.playbook.08"]["flow_refs"])

    def test_sql_registry_preserves_bind_grain_and_interpretation_limits(self):
        records = {r["sql_id"]: r for r in load("sql-registry.yaml")["records"]}
        expected_parameters = {
            "vyd.sql.01": ["rid"], "vyd.sql.02": ["rid"],
            "vyd.sql.03": ["order_rid"], "vyd.sql.04": ["issue_rid"],
            "vyd.sql.05": ["issue_rid"], "vyd.sql.06": ["issue_rid"],
            "vyd.sql.07": ["issue_rid"], "vyd.sql.08": [],
        }
        for sql_id, row in records.items():
            self.assertEqual(expected_parameters[sql_id],
                             [p["name"] for p in row["input_parameters"]])
            self.assertTrue(row["result_grain_sk"], sql_id)
            self.assertTrue(row["fanout_warning_sk"], sql_id)
            self.assertTrue(row["proves_sk"], sql_id)
            self.assertTrue(row["does_not_prove_sk"], sql_id)
        self.assertIn("1:N", records["vyd.sql.03"]["fanout_warning_sk"])
        self.assertIn("nie je univerzálne totožná", records["vyd.sql.05"]["does_not_prove_sk"])
        self.assertIn("historickú", records["vyd.sql.06"]["does_not_prove_sk"])
        self.assertIn("1 454", records["vyd.sql.07"]["fanout_warning_sk"])
        self.assertIn("nie dôkaz", records["vyd.sql.08"]["does_not_prove_sk"])

    def test_external_mutation_targets_are_field_level_boundaries(self):
        entities = load("oracle-entities.yaml")["records"]
        fields = {}
        for entity in entities:
            for field in entity.get("fields", []):
                fields[(entity["oracle_name"], field["oracle_name"])] = field["oracle_field_id"]
        records = {r["mutation_id"]: r for r in load("mutations.yaml")["records"]}
        expected = {
            "vyd.mutation.02": {fields[("OBJ_ODB_O", "P_REZ")]},
            "vyd.mutation.08": {fields[("PRIJEMKY_LIST", "RID_VYDAJ")]},
            "vyd.mutation.09": {fields[("PRIJEMKY_OBSAH", "P_VYD")]},
            "vyd.mutation.10": {fields[("REK_DOD_O", "P_DEL")],
                                fields[("REK_DOD_O", "P_VYSKL")]},
            "vyd.mutation.11": {fields[("WMS_QUE", "MIESTO_DOD")]},
            "vyd.mutation.12": {fields[("ROZVOZ_QUE", name)] for name in
                                ("DOPRAVA", "TYP_UHRADY", "PARTNER", "MIESTO_DOD", "ADRESA")},
        }
        for mutation_id, target_refs in expected.items():
            self.assertEqual(target_refs, set(records[mutation_id]["target_refs"]), mutation_id)
            self.assertTrue(records[mutation_id]["writer_ref"], mutation_id)
            self.assertTrue(records[mutation_id]["event_sk"], mutation_id)
            self.assertTrue(records[mutation_id]["direct_mutations_sk"], mutation_id)

    def test_critical_source_flows_preserve_approved_structure(self):
        records = {r["flow_id"]: r for r in load("flows.yaml")["records"]}
        critical = {
            "vyd.flow.t_vyd_o_rez", "vyd.flow.t_sz_p_vyd_o",
            "vyd.flow.t_s_vyd_l", "vyd.flow.t_sz_p_vyd_l",
            "vyd.flow.t_vyd_l_prijem", "vyd.flow.t_vyd_l_after",
            "vyd.flow.t_vyd_o_kontrola_na_fak",
        }
        for flow_id in critical:
            row = records[flow_id]
            self.assertTrue(row["watched_field_refs"], flow_id)
            self.assertTrue(row["business_effect_sk"], flow_id)
            self.assertTrue(row["diagnostic_meaning_sk"], flow_id)
            self.assertTrue(row["calls"] or row["direct_mutations"] or
                            row["side_effects"] or row["exceptions"], flow_id)
        self.assertIn("GetSwap", records["vyd.flow.t_vyd_o_rez"]["session_or_bypass_sk"])
        self.assertIn("GetReplikacia", records["vyd.flow.t_vyd_l_after"]["session_or_bypass_sk"])
        self.assertIn("ODPIS=0", records["vyd.flow.t_vyd_o_rez"]["exceptions"][0]["description_sk"])
        return_flows = [r for key, r in records.items() if key.startswith("vyd.flow.t_vratky_")]
        self.assertEqual(2, len(return_flows))
        self.assertTrue(all(r["calls"] for r in return_flows))

    def test_deferred_invoice_boundary_keeps_original_status_meaning(self):
        row = next(r for r in load("backlog.yaml")["records"]
                   if "RID_R_DLAF" in r["question_sk"])
        self.assertEqual("TREBA OVERIŤ", row["status"])
        self.assertFalse(row["blocking"])
        self.assertIn("ODLOŽENÉ", row["reason_sk"])

    def test_final_closure_freezes_contract_v11_without_breaking_change(self):
        closure = next(
            row for row in load("revisions.yaml")["records"]
            if row["revision_id"] == "vyd.revision.1_1_final_closure"
        )
        self.assertEqual("1.1", closure["contract_version"])
        self.assertFalse(closure["breaking_change"])
        self.assertIn("zmrazené", closure["reason_sk"])
        self.assertIn("evidence", closure["reason_sk"])


if __name__ == "__main__":
    unittest.main()
