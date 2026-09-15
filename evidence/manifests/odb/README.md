# ODB evidence

`approved-contract.yaml` je accepted D manifest používateľom schváleného human
semantic contractu v1.2. Nenahrádza raw Oracle A/B/B2 evidence. Pôvodný DOCX bol
pri intake overený voči SHA256SUMS; retained JSON je odvodená textová extrakcia,
nie pôvodný DOCX. Kontrola 41 vstupov je zachovaná v
`evidence/source-extracts/odb/intake-integrity.json`.

Pri materializácii 15. 9. 2026 už pôvodný source bundle nebol na zadanej ceste.
Raw XLSX manifests/claims sa neoznačujú ako skontrolované na základe checksumu
samotného. Chýbajúce claims sú v domain backlogu. Publication zostáva blocked.
