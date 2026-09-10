"""Acceptance gate for the real CESTOVNE_PR_L/O v1.1 machine-readable pilot.

This test is intentionally domain-specific. It does not infer business truth; it
checks that the reviewed v1.1 contract has not been silently truncated while
being represented by the generic schema.
"""
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
CP = ROOT / "catalog/transport/cestovne-prikazy"


def load(name):
    return yaml.safe_load((CP / name).read_text(encoding="utf-8"))


class CPV11AcceptanceTests(unittest.TestCase):
    def test_complete_physical_field_inventory(self):
        header = load("fields-cestovne_pr_l.yaml")
        bridge = load("fields-cestovne_pr_o.yaml")
        self.assertEqual(121, len(header["records"]))
        self.assertEqual(43, len(bridge["records"]))
        self.assertEqual(164, len(header["records"]) + len(bridge["records"]))
        self.assertEqual(list(range(1, 122)), sorted(r["ordinal_position"] for r in header["records"]))
        self.assertEqual(list(range(1, 44)), sorted(r["ordinal_position"] for r in bridge["records"]))
        self.assertEqual(121, len({r["field_id"] for r in header["records"]}))
        self.assertEqual(43, len({r["field_id"] for r in bridge["records"]}))

    def test_core_identity_constraints_exist(self):
        constraints = load("constraints.yaml")["records"]
        by_name = {(r["object_ref"], r["oracle_name"]): r for r in constraints}
        header_pk = by_name[("mc.object.cestovne_pr_l", "XPKCESTOVNE_PR_L")]
        bridge_pk = by_name[("mc.object.cestovne_pr_o", "XPK_C_PR_O")]
        bridge_fk = by_name[("mc.object.cestovne_pr_o", "R_176")]
        self.assertEqual("PK", header_pk["constraint_type"])
        self.assertEqual(["mc.field.cestovne_pr_l.rid"], header_pk["column_refs"])
        self.assertEqual("PK", bridge_pk["constraint_type"])
        self.assertEqual(["mc.field.cestovne_pr_o.rid_r"], bridge_pk["column_refs"])
        self.assertEqual("FK", bridge_fk["constraint_type"])
        self.assertEqual("mc.object.cestovne_pr_l", bridge_fk["referenced_object_ref"])

    def test_all_eleven_core_triggers_are_materialized(self):
        entities = load("oracle-entities.yaml")["records"]
        names = {r["oracle_name"] for r in entities if r["oracle_object_type"] == "TRIGGER"}
        expected = {
            "T_CESTOVNE_PR_L_TRACKTRACE", "T_CESTOVNE_PR_L_WMS_OUE",
            "T_CESTOVNE_PR_O_AFTER", "T_CESTOVNE_PR_O_NAKLADY",
            "T_CESTOVNE_PR_O_TRACKTRACE", "T_MCCARTER_CESTOVNE_PR_L",
            "T_R_CESTOVNE_PR_L", "T_R_CESTOVNE_PR_O", "T_S_CESTOVNE_PR_L",
            "T_S_CESTOVNE_PR_L_INS", "T_S_CESTOVNE_PR_O",
        }
        self.assertTrue(expected.issubset(names), sorted(expected - names))

    def test_direct_dependency_register_has_107_unique_oracle_objects(self):
        records = load("dependency-closure.yaml")["records"]
        direct = [r for r in records if r["direction"] == "INBOUND" and r["min_depth"] == 1]
        direct_objects = {(r["source_owner"], r["source_name"], r["source_type"]) for r in direct}
        self.assertEqual(107, len(direct_objects))
        self.assertEqual({"MC"}, {owner for owner, _, _ in direct_objects})

    def test_dependency_closure_edge_counts_match_reviewed_v11(self):
        doc = load("dependency-closure.yaml")
        records = doc["records"]
        inbound = [r for r in records if r["direction"] == "INBOUND"]
        outbound = [r for r in records if r["direction"] == "OUTBOUND"]
        self.assertEqual(348, len(inbound))
        self.assertEqual(1296, len(outbound))
        self.assertEqual(4, max(r["min_depth"] for r in inbound))
        self.assertEqual(8, max(r["min_depth"] for r in outbound))
        self.assertEqual(348, doc["summary"]["inbound_count"])
        self.assertEqual(1296, doc["summary"]["outbound_count"])

    def test_complete_mc_core_api_caller_register_matches_cp14(self):
        paths = sorted(CP.glob("api-references-part*.yaml"))
        self.assertEqual(12, len(paths))
        records = []
        for path in paths:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertEqual("MC", doc["environment"])
            self.assertEqual("CP_14_CORE_API_CALLERS.xlsx", doc["source_dataset"])
            records.extend(doc["records"])
        self.assertEqual(397, len(records))
        callers = {(r["caller_owner"], r["caller_name"], r["caller_type"]) for r in records}
        members = {(r["target_package"], r["member_name_raw"].lower()) for r in records}
        loci = {(r["caller_owner"], r["caller_name"], r["caller_type"], line)
                for r in records for line in r["hit_lines"]}
        self.assertEqual(66, len(callers))
        self.assertEqual(160, len(members))
        self.assertEqual(922, len(loci))
        self.assertEqual(982, sum(r["hit_count"] for r in records))
        self.assertEqual({"MC"}, {r["caller_owner"] for r in records})
        self.assertTrue(all("cp.evidence.b2.callers" in r["evidence_refs"] for r in records))

        triples = {(r["caller_name"], r["target_package"], r["member_name_raw"].lower()) for r in records}
        for required in {
            ("C_CESTOVNE_PR_TRASA", "D_CPR_L", "naceste"),
            ("C_CESTOVNE_PR_TRASA", "D_CPR_L", "zavezeny"),
            ("C_CESTOVNE_PR_TRASA", "D_CPR_L", "prepocitajobsahc"),
            ("HANDYGO", "D_CPR_L", "adddoklad"),
            ("HANDYGO", "D_CPR_L", "naceste"),
            ("HANDYGO", "D_CPR_L", "uzavri"),
            ("HANDYGO", "D_CPR_L", "vyraddoklad"),
            ("HANDYGO", "D_CPR_L", "prepocitajobsahc"),
            ("D_KASA_UHRADA_L", "D_CPR_O", "zmenstavfinvysp"),
        }:
            self.assertIn(required, triples)

    def test_mc_www_application_boundary_is_explicit(self):
        doc = load("api-references-mc_www.yaml")
        self.assertEqual("MC_WWW", doc["environment"])
        self.assertEqual(2, len(doc["records"]))
        self.assertEqual({"BP_IBARIS"}, {r["caller_name"] for r in doc["records"]})
        self.assertEqual({("inst", 456), ("CP_Uzavrety", 466)},
                         {(r["member_name_raw"], r["hit_lines"][0]) for r in doc["records"]})

    def test_raw_and_effective_state_contract(self):
        records = load("value-domains.yaml")["records"]
        raw = {r["raw_value"]: r for r in records if r["scope_ref"] == "mc.field.cestovne_pr_l.stav"}
        self.assertEqual(set(range(-1, 7)), set(raw))
        self.assertEqual("Rozpracovaný", raw[-1]["business_label_sk"])
        self.assertEqual("Otvorený", raw[0]["business_label_sk"])
        self.assertEqual("Uzavretý", raw[1]["business_label_sk"])
        self.assertEqual("Na ceste", raw[2]["business_label_sk"])
        self.assertEqual("Zavezený", raw[3]["business_label_sk"])
        self.assertEqual("Vybavený", raw[4]["business_label_sk"])
        self.assertEqual("Zrušený", raw[5]["business_label_sk"])
        self.assertEqual("Skompletizovaný", raw[6]["business_label_sk"])
        self.assertFalse(raw[6]["observed_live"])
        effective = {r["raw_value"]: r for r in records if r["scope_ref"] == "mc.field.cestovne_pr_l.flags_b"}
        self.assertEqual({7, 8, 9, 10}, set(effective))
        self.assertTrue(effective[9]["observed_live"])
        self.assertEqual(121, effective[9]["observed_count"])

    def test_temporal_contract_prevents_false_history_inference(self):
        records = load("temporal.yaml")["records"]
        by_id = {r["temporal_rule_id"]: r for r in records}
        for name in ("uzavrel_stamp", "odchod_stamp", "prichod_stamp", "vybavil_stamp", "s_stamp"):
            row = by_id[f"cp.temporal.{name}"]
            self.assertEqual("TRANSITION STAMP", row["classification"])
            self.assertFalse(row["reconstructable"])
        bridge = by_id["cp.temporal.bridge_membership"]
        self.assertEqual("SELECTIVE HISTORY", bridge["classification"])
        self.assertFalse(bridge["reconstructable"])
        self.assertIn("DELETE", bridge["rollback_behavior_sk"])

    def test_mutation_matrix_covers_reviewed_critical_surfaces(self):
        records = load("mutations.yaml")["records"]
        ids = {r["mutation_id"] for r in records}
        expected = {
            "cp.mutation.header_state", "cp.mutation.bridge_state",
            "cp.mutation.derived_header", "cp.mutation.header_cost",
            "cp.mutation.bridge_cost", "cp.mutation.route_stop_fields",
            "cp.mutation.vehicle_driver", "cp.mutation.financial_state",
            "cp.mutation.flags_b", "cp.mutation.rid_v_membership",
            "cp.mutation.bridge_insert", "cp.mutation.wms_319_side_effect",
        }
        self.assertTrue(expected.issubset(ids), sorted(expected - ids))

    def test_trigger_flows_are_structured_not_free_text_only(self):
        records = load("flows.yaml")["records"]
        self.assertEqual(11, len(records))
        for record in records:
            for key in ("watched_field_refs", "calls", "direct_mutations", "side_effects", "exceptions"):
                self.assertIn(key, record, f"{record['flow_id']} missing {key}")
            self.assertTrue(record["watched_field_refs"] or record["calls"] or
                            record["direct_mutations"] or record["side_effects"] or
                            record["exceptions"], record["flow_id"])
        after = next(r for r in records if r["flow_id"] == "cp.flow.t_cestovne_pr_o_after")
        self.assertIn("GetReplikacia=1", after["session_or_bypass_sk"])
        stamps = next(r for r in records if r["flow_id"] == "cp.flow.t_s_cestovne_pr_l")
        mutated = {ref for m in stamps["direct_mutations"] for ref in m["scope_refs"]}
        for ref in {
            "mc.field.cestovne_pr_l.uzavrel_stamp", "mc.field.cestovne_pr_l.odchod_stamp",
            "mc.field.cestovne_pr_l.prichod_stamp", "mc.field.cestovne_pr_l.vybavil_stamp",
            "mc.field.cestovne_pr_l.s_stamp",
        }:
            self.assertIn(ref, mutated)

    def test_live_dq_snapshot_is_preserved_as_nonblocking_observation(self):
        records = load("data-quality.yaml")["records"]
        self.assertEqual(7, len(records))
        self.assertFalse(any(r["blocking"] for r in records))
        by_id = {r["dq_id"]: r for r in records}
        for dq_id, count in {
            "cp.dq.document_count_stored_drift": "577",
            "cp.dq.volume_stored_drift": "782",
            "cp.dq.weight_stored_drift": "6238",
            "cp.dq.pallet_count_stored_drift": "10556",
        }.items():
            self.assertIn(count, by_id[dq_id]["observation_sk"])
            self.assertEqual("2026-09-09", by_id[dq_id]["snapshot_date"])
        self.assertIn("0 unresolved", by_id["cp.dq.ridv_unresolved"]["observation_sk"])

    def test_canonical_sql_toolkit_is_complete_and_read_only_declared(self):
        registry = load("sql-registry.yaml")["records"]
        self.assertEqual(11, len(registry))
        for record in registry:
            compatibility = record["compatibility"]
            self.assertEqual("SQL Navigator 5.5.4.847", compatibility["sql_client"])
            self.assertIsNone(compatibility["oracle_server_version"])
            self.assertIs(True, compatibility["read_only"])
            self.assertTrue((ROOT / record["sql_file"]).is_file(), record["sql_file"])

    def test_agent_ready_objects_and_nonblocking_backlog(self):
        for obj in (load("object-cestovne_pr_l.yaml"), load("object-cestovne_pr_o.yaml")):
            self.assertEqual("AGENT-READY", obj["maturity"])
            self.assertEqual("POTVRDENÉ", obj["status"])
        backlog = load("backlog.yaml")["records"]
        self.assertFalse(any(r["blocking"] for r in backlog),
                         "Reviewed v1.1 had no blocking backlog items")

    def test_polymorphic_rid_v_current_targets_are_present(self):
        relationships = load("relationships.yaml")["records"]
        poly = next(r for r in relationships if r.get("relationship_type") == "POLYMORPHIC"
                    and "mc.field.cestovne_pr_o.rid_v" in r.get("from_field_refs", []))
        target_names = {t["to_object_ref"] for t in poly["targets"]}
        expected = {"mc.oracle.mc_prijemky_list", "mc.oracle.mc_dlaf_l",
                    "mc.oracle.mc_vyd_l", "mc.oracle.mc_docasny_rozvoz"}
        self.assertTrue(expected.issubset(target_names), sorted(expected - target_names))


if __name__ == "__main__":
    unittest.main()
