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

        self.assertEqual(list(range(1, 122)),
                         sorted(r["ordinal_position"] for r in header["records"]))
        self.assertEqual(list(range(1, 44)),
                         sorted(r["ordinal_position"] for r in bridge["records"]))
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
            "T_CESTOVNE_PR_L_TRACKTRACE",
            "T_CESTOVNE_PR_L_WMS_OUE",
            "T_CESTOVNE_PR_O_AFTER",
            "T_CESTOVNE_PR_O_NAKLADY",
            "T_CESTOVNE_PR_O_TRACKTRACE",
            "T_MCCARTER_CESTOVNE_PR_L",
            "T_R_CESTOVNE_PR_L",
            "T_R_CESTOVNE_PR_O",
            "T_S_CESTOVNE_PR_L",
            "T_S_CESTOVNE_PR_L_INS",
            "T_S_CESTOVNE_PR_O",
        }
        self.assertTrue(expected.issubset(names), sorted(expected - names))

    def test_direct_dependency_register_has_107_unique_oracle_objects(self):
        # v1.1 defines this count from CP_13 / ALL_DEPENDENCIES, not from the
        # curated dependencies.yaml register, which may also contain explicit
        # application/API boundary records.
        records = load("dependency-closure.yaml")["records"]
        direct = [r for r in records
                  if r["direction"] == "INBOUND" and r["min_depth"] == 1]
        direct_objects = {
            (r["source_owner"], r["source_name"], r["source_type"])
            for r in direct
        }
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
        self.assertEqual(4, doc["summary"]["max_inbound_depth"])
        self.assertEqual(8, doc["summary"]["max_outbound_depth"])

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
        header = load("object-cestovne_pr_l.yaml")
        bridge = load("object-cestovne_pr_o.yaml")
        for obj in (header, bridge):
            self.assertEqual("AGENT-READY", obj["maturity"])
            self.assertEqual("POTVRDENÉ", obj["status"])

        backlog = load("backlog.yaml")["records"]
        self.assertFalse(any(r["blocking"] for r in backlog),
                         "Reviewed v1.1 had no blocking backlog items")

    def test_polymorphic_rid_v_current_targets_are_present(self):
        relationships = load("relationships.yaml")["records"]
        poly = next(r for r in relationships
                    if r.get("relationship_type") == "POLYMORPHIC"
                    and "mc.field.cestovne_pr_o.rid_v" in r.get("from_field_refs", []))
        target_names = {t["to_object_ref"] for t in poly["targets"]}
        expected = {
            "mc.oracle.mc_prijemky_list",
            "mc.oracle.mc_dlaf_l",
            "mc.oracle.mc_vyd_l",
            "mc.oracle.mc_docasny_rozvoz",
        }
        self.assertTrue(expected.issubset(target_names), sorted(expected - target_names))


if __name__ == "__main__":
    unittest.main()
