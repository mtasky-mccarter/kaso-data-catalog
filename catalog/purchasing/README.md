# Purchasing v1.0

Kanonický vstup je `pur.contract.purchasing.1_0` v `contract.yaml`. Scope je MC nákupný návrh, supplier PO (`00028`), supplier PL (`00029`) a receiving boundary. Podporné tabuľky majú celý dostupný fyzický inventár; neznáme business významy zostávajú null.

Stav vybavenia poskytuje `MC.D_OBJD_L.GetS_STAV(FLAGS_S)` (Flag 11). Raw `OBJD_L.STAV` zostáva dohľadateľný. `P_PL` nie je fyzický príjem. Efektívny termín je `NVL(O.TERMIN_DOD, NVL(L.TERMIN_DOD, L.DATUM_P))` na každom riadku.

`temporal.yaml` zachováva STORED CURRENT význam množstevných bucketov pomocou existujúcej klasifikácie RAW CURRENT s explicitným popisom autority. Súčasná receipt lineage nie je úplná event história P_PRIJ. `backlog.yaml` zachováva sedem schválených neblokujúcich hraníc.

`api-references.yaml` obsahuje lexikálne member referencie z dodaného zdrojového textu. Môžu zahŕňať konštanty, komentáre či stringy; nie sú automaticky volaním alebo zápisom. Konkrétne schválené volanie HandyGO je v `flows.yaml`. `source-mutations.yaml` zachováva explicitné UPDATE source loci pre kritické polia, bez spúšťania kódu a bez domyslených runtime vetiev.

`dependencies.yaml` zachováva MP01 metadata a osobitne source-confirmed MC_ST reader hranicu. `inbound-closure.yaml` zachováva priamu F4 surface. Depth-2 export zostáva v dôkazoch; generic crawling sa neopakuje. `access-capabilities.yaml` a `cross-schema.yaml` oddeľujú grants/synonyms a compile dependencies od runtime správania.

Diagnostiky sú v `sql/diagnostic/purchasing/` a ich grain, dôkazná sila, limity a parametre v `sql-registry.yaml`. Comparator P_PRIJ zobrazuje net množstvo súčasných receipt riadkov, nie historicky rekonštruovaný príjem; pri chýbajúcej lineage necháva NULL. Voliteľný report podľa tvorcu nebol zavedený, pretože handoff neobsahuje potvrdený creator/UI binding. Riadkový overdue report je k dispozícii.

Externé Oracle entity sa referencujú existujúcimi ID. Chýbajúce FK target field referencie boli doplnené k existujúcim boundary entitám bez prepisu ich business významu. CHECK predicates a underlying function-based index výrazy neboli v exporte dodané; zachované sú dostupné constraint a hidden-column údaje, bez domýšľania výrazov.

Overenie:

```text
python tools/validate_catalog.py
python -m unittest discover -s tools -p 'test_*.py' -v
python -m unittest discover -s tools -p 'test_pur_*.py' -v
```

Tieto kontroly nevolajú Oracle. AGENT-READY scope zo schváleného handoffu sa do kanonického main prijíma až cez kompletné overenie dôkazov a zelené CI. Rozšírenie schema enumu PUR-SCHEMA-001 je engineering zmena, oddelená od troch semantic breaking changes v `revisions.yaml`.
