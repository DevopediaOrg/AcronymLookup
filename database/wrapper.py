import sqlite3
import json
import os
import os.path
import pandas as pd
from collections import Counter


class AcronymDatabase:
    def __init__(self, fname="../data/acronyms.sqlite"):
        path = os.path.dirname(os.path.abspath(__file__))
        fname = "{}/{}".format(path, fname)
        create_tables = not os.path.exists(fname)
        conn = sqlite3.connect(fname)

        self.conn = conn
        self.cur = conn.cursor()

        if create_tables:
            with open("{}/schema.sql".format(path), "r") as f:
                schema = f.read()
            self.cur.executescript(schema)

    def addAcronym(self, acronym):
        self.cur.execute("INSERT INTO acronyms (acronym) VALUES (?)", (acronym,))
        return self.cur.lastrowid

    def getAcronym(self, acronym):
        self.cur.execute("SELECT aid FROM acronyms WHERE acronym=?", (acronym,))
        result = self.cur.fetchone()
        return result[0] if result else None

    def addDefinition(self, definition, context, url, aid = False):
        self.cur.execute("INSERT INTO definitions (definition, context, url) VALUES (?, ?, ?)", (definition,context,url))
        did = self.cur.lastrowid
        if aid:
            self.cur.execute("INSERT INTO acronyms_definitions (aid, did) VALUES (?, ?)", (aid, did))        
        return did

    def addTrueDefinition(self, acronym, truedef, url):
        self.cur.execute("SELECT true_definition FROM true_definitions WHERE acronym=? AND url=?", (acronym,url))
        result = self.cur.fetchone()
        result = None if not result else result[0]
        if result is None:
            self.cur.execute("INSERT INTO true_definitions (acronym, true_definition, url) VALUES (?, ?, ?)", (acronym,truedef,url))

    def getTrueDefinition(self, acronym, url):
        self.cur.execute("SELECT true_definition FROM true_definitions WHERE acronym=? AND url=?", (acronym,url))
        result = self.cur.fetchone()
        return result[0] if result else None
    
    def acronymHasDefinition(self,aid, definition):
        self.cur.execute("SELECT definitions.did from definitions JOIN acronyms_definitions ON acronyms_definitions.did = definitions.did WHERE definitions.definition = ? AND acronyms_definitions.aid = ?", (definition,aid))
        result = self.cur.fetchone()
        return result[0] if result else None

    def updateContext(self, definition_id, context):
        self.cur.execute("SELECT context FROM definitions JOIN context ON definitions.CID = context.CID WHERE did = ? LIMIT 1", (definition_id,))
        oldContextJSON = self.cur.fetchone()[0]
        oldContext = Counter(json.loads(oldContextJSON))
        newContext = oldContext + context
        newContextJSON = json.dumps(newContext)
        self.cur.execute("UPDATE context SET context=? FROM definitions WHERE did=?", (newContextJSON,definition_id))

    def getContextAcronymList(self):
        self.cur.execute("""
            SELECT acronym, context, definition FROM definitions, acronyms, acronyms_definitions
            WHERE definitions.did=acronyms_definitions.did AND acronyms.aid=acronyms_definitions.aid""")
        result = self.cur.fetchall()
        ret = []
        for elem in result:
            ret.append((elem[0], elem[1], elem[2]))
        return ret

    def clearTrueDefTable(self):
        self.cur.execute("DELETE FROM true_definitions")

    def clearAcronymTables(self):
        self.cur.execute("DELETE FROM definitions")
        self.cur.execute("DELETE FROM acronyms")
        self.cur.execute("DELETE FROM acronyms_definitions")

    def close(self):
        self.conn.commit()
        self.cur.close()
        self.conn.close()

    def export_tables(self):
        path = os.path.dirname(os.path.abspath(__file__))
        os.makedirs('{}/../data/db'.format(path), exist_ok=True)
        for tbl in ('acronyms', 'definitions', 'acronyms_definitions', 'true_definitions'):
            df = pd.read_sql_query("SELECT * FROM {}".format(tbl), self.conn)
            df.to_csv('data/db/{}.csv'.format(tbl))
