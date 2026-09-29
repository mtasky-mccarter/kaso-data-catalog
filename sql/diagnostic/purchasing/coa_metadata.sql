-- CoA údaje riadka nákupnej objednávky; read-only MC diagnostika.
-- Grain: jeden OBJD_O riadok identifikovaný RID_O a ID_R.
-- ID_R_V=0: UI query condition; business meaning not established.
-- RID_O zo zachyteného formulára je nahradené parametrom, nie business pravidlom.
-- Raw U1 kódy Nie/Áno nie sú známe. Prázdny decode nie je dôkazom 'Nie'.
-- Skalárny lookup zachová grain; pri duplicitnom CIS_X kóde môže zlyhať ORA-01427.
-- História XML tagov ani fyzické receipt údaje sa nerekonštruujú.
SELECT C.RID_O,
       C.ID_R,
       C.KOD_ID,
       c_xml_tags.GetTagValueNumT(C.XML_DATA,'U1', -2020, NULL) AS coa_certificate_status_raw,
       (SELECT pck_multilang.DecodeTextX(27, NAZOV)
          FROM CIS_X
         WHERE ID_CIS = -1006
           AND HODNOTA = c_xml_tags.GetTagValueNumT(C.XML_DATA,'U1', -2020, NULL)) AS coa_certificate_status,
       c_xml_tags.GetTagValueT(C.XML_DATA,'U2', -2020, NULL) AS coa_batch,
       c_xml_tags.GetTagValueDateT(C.XML_DATA,'U3', -2020, NULL) AS coa_expiry_date
  FROM OBJD_O C
 WHERE C.RID_O = :p_rid_o
   AND C.ID_R = :p_id_r
   AND C.ID_R_V = 0;
