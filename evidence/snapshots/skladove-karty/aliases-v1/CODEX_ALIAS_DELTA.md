# KASO Data Catalog — SKLAD_KARTA canonical alias delta v1.0

Date: 2026-09-17
Authority: ChatGPT / semantic mapping orchestrator, based on the approved Product Master handoff and MP01-A physical inventory.

## Decision

The attached alias dictionary is approved for Codex materialization. It covers all 169 physical fields of `MC.SKLAD_KARTA`.

- `canonical_alias` is an English/ASCII `snake_case` technical alias.
- The alias is a naming layer only. It MUST NOT upgrade or replace `business_definition_sk`, evidence status, source-of-truth, lookup meaning, or backlog status.
- `APPROVED_TRANSLATION` means the alias is a straightforward translation of already-supported technical/business meaning.
- `TECHNICAL_NEUTRAL` means the field meaning is not sufficiently closed for a stronger English expansion. The alias intentionally preserves an acronym or uses a neutral literal form and MUST NOT be treated as new semantic evidence.
- All aliases are unique and syntactically validated.

## Critical semantic guards

1. `T_TOVARU -> item_type`: do not import the historical Oracle comment value mapping as the current type dictionary.
2. `TYP_T -> item_group_code`: current `00` remains unresolved; alias does not close the backlog.
3. `NAHRADA -> replacement_group_id`: technical grouping only; do not assert physical/commercial substitutability.
4. `N_STAMP -> new_item_stamp`: Novinka-related selective stamp; not creation date or universal lifecycle timestamp.
5. `ALERGENY -> legacy_allergens` and `FLAGS_A -> legacy_allergen_flags`: root mechanism is current-unpopulated/dormant; typed notes remain current allergen authority.
6. Neutral aliases such as `c_ekv`, `kir_1..7`, `c_stamp`, `method_up`, `nutrition_batch_h`, `sco_weight`, `eudr_1/2` are naming placeholders only and do not assert acronym expansion.

## Codex action

Use `SKLAD_KARTA_canonical_aliases_v1.0.csv` as the authoritative alias dictionary for the root `MC.SKLAD_KARTA` field records. Preserve the existing approved Slovak definitions/status/evidence from the main handoff. Do not derive additional business meaning from alias names.
