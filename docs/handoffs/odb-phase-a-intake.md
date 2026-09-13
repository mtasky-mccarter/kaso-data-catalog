# ODB Phase A — intake and missing inputs

The user supplied `odb-phase-a.txt` on 2026-09-13. It is retained verbatim.
Continue from `fd90c03a04f9185b9ca8e764bea93bbb7141d217` on the existing feature
branch; no branch reset, no merge, no publication.

Authorization is received: MC, diagnostic-grade target, revision 1.2,
breaking_change=false. This is not a request for renewed approval.
The handoff explicitly approves grain, identity, primary 1:N join, quantity
formulas, DO NOT ASSUME rules and future-domain gaps. These instructions are
preserved in the supplied text; missing detail must not be reconstructed from them.

## HANDOFF BLOCKED — missing files, not a schema limitation

1. Approved **KASO Data Catalog - Technical & Diagnostic Reference - obchodné
   prípady v1.2**: full text, Relationship Contract Register, field aliases and
   definitions, exact CHECK/DECODE nuance, temporal assignments and interpretation
   limits. The formulas alone do not specify those exceptions.
2. MC physical metadata: the actual 79 header and 44 line field records, ordered
   constraints/indexes and source null/default/comment values. Counts cannot supply
   the missing names or attributes.
3. Approved source/evidence: actual 17 header and 33 line trigger identities,
   source-confirmed flows, mutation targets/conditions, roles and evidence links.
   The nine named mutation topics are not individual source records.
4. Approved ODB_DIAG packs and executable read-only SQL, associated binds, grain,
   fan-out/proves/does-not-prove metadata, DQ snapshots and playbooks.
5. Evidence inventory tying the above to files, review status, classes, provenance,
   dates and retention. No accepted manifest for an unavailable file is created.

Search covered available attachments, workspace and the current feature-branch
tree. Only the handoff text and existing scaffold were available for ODB.
No known schema v1.0 limitation prevents representing the supplied facts. A
lossless assessment of the missing document cannot yet be completed.

## Phase boundaries preserved

Exhaustive dependency closure and AGENT-READY are not required for Phase A.
The following supplied future-domain items are non-blocking for DIAGNOSTIC-GRADE:
CENA_OCA detail; OK detail; XML/domain-index detail; ZMENY_VYKRYTIA_OBJ_ODB mapping;
deeper CT_* architecture; OBJ_D_NAVRH/OBJD lifecycle; cross-environment RID/global
identity; master temporal validity; exact invoice-line persistent join.
They are not converted to facts or promoted to Phase A blockers. Detailed
AGENT-READY closure conditions await the later hardening handoff.

VYD boundary IDs remain owned by VYD and unchanged. New object IDs remain
`mc.object.obj_odb_l` and `mc.object.obj_odb_o`.

## Materialization status

- New populated domain record files: 0. This commit records intake only.
- Fields: 0/79 and 0/44; triggers: 0/17 and 0/33.
- Relationships: 0; mutations: 0. No count is manufactured to satisfy acceptance.
- New evidence manifests: 0. New SQL files: 0.
- Scaffold maturity remains DISCOVERY until lossless materialization is possible;
  the authorized target is DIAGNOSTIC-GRADE, not AGENT-READY.
- Domain-scoped schema/ID/ref validation and six scaffold tests are rerun.
  They do not establish production acceptance. Full repository regression and
  global duplicate/reference checks require a complete checkout and remain unverified.

The backlog now distinguishes received authorization/counts/revision from missing
referenced inputs. Supply the files above to continue Phase A without re-scaffolding.
