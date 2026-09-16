# Obchodné prípady v1.2

MC.OBJ_ODB_L/O: schválený semantic contract a raw physical/source closure podľa
`docs/handoffs/odb-final-closure.txt`. Canonical YAML/SQL sú autorita; publikácie
v `generated/obchodne-pripady/` sú odvodené. Feature branch je návrh až do merge.

79/44 polí, 130 constraints, 34 indexov, 50 triggerov; tri package spec/body
páry vrátane supporting direct writer D_OBJ_ODB_L_B. Zachované aliases, business
významy, SQL a existujúce VYD boundary IDs. Physical index X_OBJODBO_XML35
zachováva pôvodné stable ID; úplný domain-index výraz zostáva neblokujúcou medzerou.

Offline BFS používa presné (owner, name, type): 55 logical seeds / 58 graph seeds.
Inbound 285 nodes / 673 edges, max node depth 3; outbound 477 / 2515, max node
depth 4. Edge traversal depth môže byť 5 pri spätných/cyklických hranách.
Priame hrany: 581/889. ALL_DEPENDENCIES znamená DEPENDENCY ONLY.

MC API/source: 4515 jednotlivých lexikálnych výskytov, 595 normalizovaných
členov, 145 source objektov. Raw spelling aj presný source riadok zostávajú
zachované. Toto nie je dôkaz runtime writer/caller správania. 71 grants a 9
synonyms znamenajú iba ACCESS CAPABILITY. Dva nulové job audity dokazujú iba
absenciu priameho name match v ich explicitnom rozsahu.

Deväť neblokujúcich future-domain/business medzier zostáva otvorených.
Sedem historických Phase A blockerov zostáva v checksum-pinned snapshot histórii.
Dynamic SQL, application runtime, external služby a iné prostredia sú hranice.
Exhaustive closure je obmedzená na dodaný Oracle-visible snapshot MC.

Reprodukcia: `python tools/materialize_odb_final.py --bundle <read-only-directory>`
kontroluje všetkých 13 SHA256 položiek pred čítaním XLSX. Raw core source je
zachovaný ako lossless JSON projection s accepted B2 snapshot manifestmi;
originálne XLSX sú TRANSIENT vstupy s pôvodnými hashmi, nie predstierané snapshots.
Phase A dokumentová extrakcia ostáva traceable, nie je náhradou raw Oracle dôkazu.

Overenie: validator, celé unittest discovery, ODB acceptance / SQL safety /
publication testy a `python tools/generate_publication.py all --check`.
Publikácia obsahuje úplné business registre a SQL; veľké graph/API/entity
registre sú explicitne zhrnuté s odkazmi na úplné kanonické YAML.
