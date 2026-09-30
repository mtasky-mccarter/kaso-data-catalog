"""Read-only lint and synthetic join regressions; no Oracle execution claim."""
from pathlib import Path
import re
import sqlite3
import unittest
from validate_catalog import load_yaml
ROOT=Path(__file__).resolve().parents[1]
SQL=ROOT/'sql/diagnostic/obchodni-partneri'

def clean(sql):
    return re.sub(r"'(?:''|[^'])*'", "''", re.sub(r'--[^\n]*|/\*.*?\*/',' ',sql,flags=re.S))

class OPSqlSafety(unittest.TestCase):
    def test_read_only_and_conservative_syntax(self):
        for path in SQL.glob('*.sql'):
            text=clean(path.read_text())
            self.assertRegex(text.lstrip(),r'(?i)^SELECT\b')
            self.assertNotRegex(text,r'(?i)\b(INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|COMMIT|ROLLBACK|EXECUTE|BEGIN|DECLARE|INTO|FETCH|OFFSET)\b')
            self.assertEqual(1,text.count(';'))
            for alias in re.findall(r'(?i)\bAS\s+(\w+)',text):self.assertLessEqual(len(alias),30)
            if 'UNION' in text.upper():self.assertRegex(text,r'(?i)ORDER BY 1\s*;')

    def test_no_lookup_current_filter_or_satellite_fanout(self):
        for path in SQL.glob('*.sql'):
            if path.stem.endswith('boundary'):continue
            text=clean(path.read_text()).lower()
            self.assertNotRegex(text,r'\b(miesta_dodania|kontakty|partner_banky)\b')
            self.assertNotRegex(text,r'(?<![\w.])(?:k|m|mk|me|sop|tc|tu|ku|pos|seg|cp|bp|ek|zu|nu|u|s|t)\.s_stamp\s*=')
        search=clean((SQL/'partner-search-ico-dic.sql').read_text())
        self.assertNotRegex(search,r'(?i)\bROWNUM\b')

    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.db.row_factory=sqlite3.Row
        self.db.execute("ATTACH DATABASE ':memory:' AS mc")
        # Minimal synthetic tables contain only fields used by this toolkit.
        tables={
            'obch_partneri':'id,rid,nazov,s_stamp,krajina,id_mesto,mena_p,stav,typ_cis,typ_uhrady,obch_skupina,segment_trhu,zlava,sklad,typ_el_kom,zastupca,nakupca,ico,dic,dic_new',
            'krajiny':'id,nazov,nazov_m,iso_nkod,iso_alpha_3,s_stamp',
            'mesta':'id,nazov,psc,krajina,s_stamp', 'meny':'id,skratka,nazov,s_stamp',
            'stavy_op':'id,nazov,s_stamp','typy_cis':'id,nazov_zoznam,s_stamp',
            'typy_uhrady':'id,nazov,splatnost,sposob_uhr,s_stamp','kasy_sposob_uhrad':'id,nazov',
            'partner_os':'id,nazov,s_stamp','segmenty':'rid,nazov,s_stamp','cenniky_popis':'id,nazov,s_stamp',
            'bartex_pobocky':'id,nazov,s_stamp','el_kom_formaty':'id,nazov,s_stamp',
            'b_users':'id,meno,priezvisko,titul,funkcia,el_mail,tel_mb,s_stamp',
            'miesta_dodania':'rid,id_partner,nazov,dealer,s_stamp'}
        for table,cols in tables.items():self.db.execute('CREATE TABLE mc.'+table+' ('+cols+')')
        self.db.executescript("""
          INSERT INTO mc.obch_partneri (id,rid,nazov,s_stamp,krajina,id_mesto,mena_p,zastupca,nakupca,ico,dic,dic_new)
            VALUES(1,'051A','A','0',1,10,30,7,999,'SAME','DUP','ND');
          INSERT INTO mc.obch_partneri (id,rid,nazov,s_stamp,ico,dic,dic_new) VALUES(2,'051B','B','0','SAME','DUP','ND');
          INSERT INTO mc.obch_partneri (id,rid,nazov,s_stamp,ico) VALUES(3,'051C','C','1','SAME');
          INSERT INTO mc.krajiny (id,nazov,s_stamp) VALUES(1,'Partner country','1'),(2,'City country','0');
          INSERT INTO mc.mesta (id,nazov,krajina,s_stamp) VALUES(10,'City',2,'1');
          INSERT INTO mc.meny (id,skratka,nazov,s_stamp) VALUES(30,'LEG','Legacy description','1');
          INSERT INTO mc.b_users (id,meno,s_stamp) VALUES(7,'Representative','1'),(8,'Dealer','0');
          INSERT INTO mc.miesta_dodania (rid,id_partner,nazov,dealer,s_stamp) VALUES('a',1,'A',8,'0'),('b',1,'B',8,'0'),('c',1,'C',8,'1');
        """)

    def tearDown(self):self.db.close()
    def run_sql(self,name,**params):
        return self.db.execute((SQL/(name+'.sql')).read_text(),params).fetchall()

    def test_one_partner_retains_noncurrent_lookups_and_country_axes(self):
        rows=self.run_sql('partner-current-enriched',partner_id=1)
        self.assertEqual(1,len(rows)); row=rows[0]
        self.assertEqual(('Partner country','City country'),(row['country_name'],row['city_country_name']))
        self.assertEqual(('LEG','1'),(row['currency_code'],row['currency_s_stamp']))
        self.assertEqual(('Representative','1'),(row['rep_first_name'],row['rep_user_s_stamp']))
        self.assertIsNone(row['buyer_user_match_id'])
        self.assertEqual(1,len(self.run_sql('partner-current-enriched',partner_id=2)))
        self.assertEqual(1,len(self.run_sql('partner-current-by-id',partner_id=1)))
        self.assertEqual(1,len(self.run_sql('partner-state-role',partner_id=1)))
        self.assertEqual('Representative',self.run_sql('partner-representative',partner_id=1)[0]['rep_first_name'])

    def test_search_returns_all_current_duplicates(self):
        rows=self.run_sql('partner-search-ico-dic',ico='SAME',dic='DUP',dic_new='ND')
        self.assertEqual([1,2],[r['partner_id'] for r in rows])

    def test_boundary_fanout_is_explicit_and_separate(self):
        rows=self.run_sql('partner-delivery-dealer-boundary',partner_id=1)
        self.assertEqual(['a','b'],[r['delivery_place_rid'] for r in rows])
        self.assertTrue(all(r['dealer_user_id']==8 for r in rows))
        quality=self.run_sql('partner-reference-quality')
        self.assertEqual(4,len(quality))
        self.assertTrue(all(r['src_rows']==3 for r in quality))
        self.assertEqual(1,next(r['no_match'] for r in quality if r['rel_name']=='NAKUPCA_SOFT'))

if __name__=='__main__':unittest.main()
