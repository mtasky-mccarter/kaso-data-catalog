# Cestovné príkazy — CESTOVNE_PR_L / CESTOVNE_PR_O

**Contract version:** 1.1  
**Authoritative environment:** `MC`  
**Maturity:** `AGENT-READY` / `EXHAUSTIVE DEPENDENCY-GRADE`  
**Mapping state:** **CLOSED for normal mapping**

The canonical machine-readable entry point is [`contract.yaml`](contract.yaml). This directory is the accepted semantic contract for `MC.CESTOVNE_PR_L` and `MC.CESTOVNE_PR_O` on GitHub `main`.

The contract covers the complete 164-field physical inventory (121 header + 43 bridge), identity and constraints/indexes, live JOIN/cardinality rules, polymorphic `RID_V`, raw/effective lifecycle state, temporal/history limits, 11 core trigger flows, `D_CPR_L` / `D_CPR_O`, Mutation Matrix, source-visible dependency closure, core API caller surface, MC_WWW application boundary, DQ observations, DO NOT ASSUME rules, playbooks and canonical read-only SQL.

## Canonical locations

- Contract: [`contract.yaml`](contract.yaml)
- Header object: [`object-cestovne_pr_l.yaml`](object-cestovne_pr_l.yaml)
- Bridge object: [`object-cestovne_pr_o.yaml`](object-cestovne_pr_o.yaml)
- Fields: [`fields-cestovne_pr_l.yaml`](fields-cestovne_pr_l.yaml), [`fields-cestovne_pr_o.yaml`](fields-cestovne_pr_o.yaml)
- Relationships: [`relationships.yaml`](relationships.yaml)
- Lifecycle/value domains: [`value-domains.yaml`](value-domains.yaml)
- Temporal contract: [`temporal.yaml`](temporal.yaml)
- Mutation Matrix: [`mutations.yaml`](mutations.yaml)
- Trigger/source flows: [`flows.yaml`](flows.yaml)
- Dependencies: [`dependencies.yaml`](dependencies.yaml), [`dependency-closure.yaml`](dependency-closure.yaml)
- API caller register: `api-references-*.yaml`
- Data quality: [`data-quality.yaml`](data-quality.yaml)
- DO NOT ASSUME: [`do-not-assume.yaml`](do-not-assume.yaml)
- Playbooks: [`playbooks.yaml`](playbooks.yaml)
- SQL registry: [`sql-registry.yaml`](sql-registry.yaml)
- Backlog: [`backlog.yaml`](backlog.yaml)
- Revisions: [`revisions.yaml`](revisions.yaml)
- Accepted evidence manifests: [`../../../evidence/manifests/cp/`](../../../evidence/manifests/cp/)
- Domain acceptance gate: [`../../../tools/test_cp_acceptance.py`](../../../tools/test_cp_acceptance.py)
- Human-readable publication: [`../../../generated/transport/cestovne-prikazy/`](../../../generated/transport/cestovne-prikazy/)

## Closure rule

There is **no blocking backlog**. Remaining items in `backlog.yaml` are explicit non-blocking domain/temporal boundaries and do not require reopening the CP mapping for ordinary reporting, SQL, diagnostics or agent use.

Do **not** remap CP simply because a new project or chat needs it. Reopen semantic mapping only when one of these occurs:

1. new Oracle metadata/source or live evidence contradicts a confirmed fact;
2. a production system change modifies fields, JOIN keys, lifecycle, source-of-truth or mutation behavior;
3. a currently non-blocking boundary becomes required for a concrete use case;
4. a new live `RID_V` target/state appears and changes the accepted contract;
5. an explicit revalidation is requested after a relevant release/change.

Runtime/dynamic SQL outside Oracle-visible source remains an explicit system boundary. It is not a hidden blocking gap.
