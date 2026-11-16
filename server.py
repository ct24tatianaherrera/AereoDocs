#!/usr/bin/env python3
"""AeroDocs shared repository: Python 3.10+ standard library, SQLite."""
import hmac
import json
import os
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get('AERODOCS_DB', str(ROOT / 'aerodocs.sqlite3')))
TOKEN = os.environ.get('AERODOCS_EDIT_TOKEN', '')
HOST = os.environ.get('AERODOCS_HOST', '127.0.0.1')
PORT = int(os.environ.get('PORT', '8080'))
LOCK = threading.Lock()

def valid_data(d):
    return (isinstance(d, dict) and d.get('version') == 2
            and isinstance(d.get('docs'), list) and len(d['docs']) <= 300
            and all(isinstance(x,str) and len(x)<2000 for x in d['docs'])
            and isinstance(d.get('countries'), dict) and len(d['countries']) <= 300
            and all(isinstance(n, str) and len(n)<=90 and isinstance(c, dict)
                    and isinstance(c.get('name'),str) and c.get('name') == n
                    and isinstance(c.get('extraDocs',[]),list)
                    and all(isinstance(x,str) for x in c.get('extraDocs',[]))
                    for n,c in d['countries'].items())
            and isinstance(d.get('history',[]),list) and len(d.get('history',[]))<=200)

def connect():
    con = sqlite3.connect(str(DB_PATH), timeout=5)
    con.execute('PRAGMA journal_mode=WAL')
    return con

def init_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as con:
        con.execute('CREATE TABLE IF NOT EXISTS repository (id INTEGER PRIMARY KEY CHECK(id = 1), revision INTEGER NOT NULL, content TEXT NOT NULL)')
        if not con.execute('SELECT 1 FROM repository WHERE id=1').fetchone():
            seed = json.loads((ROOT / 'seed.json').read_text(encoding='utf-8'))
            assert valid_data(seed), 'Invalid seed.json'
            con.execute('INSERT INTO repository(id,revision,content) VALUES(1,1,?)', (json.dumps(seed, ensure_ascii=False),))

def get_current():
    with connect() as con:
        row = con.execute('SELECT revision,content FROM repository WHERE id=1').fetchone()
        return {'revision': row[0], 'data': json.loads(row[1])}

class Handler(BaseHTTPRequestHandler):
    server_version='AeroDocs/1.0'
    def send_body(self, status, body, typ='application/json; charset=utf-8'):
        self.send_response(status)
        self.send_header('Content-Type',typ)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','no-referrer')
        self.end_headers()
        self.wfile.write(body)
    def send_json(self,status,d):
        self.send_body(status,json.dumps(d,ensure_ascii=False).encode('utf-8'))
    def do_GET(self):
        p=urlsplit(self.path).path
        if p=='/api/data': return self.send_json(200,get_current())
        if p in ('/','/index.html'):
            return self.send_body(200,(ROOT/'index.html').read_bytes(),'text/html; charset=utf-8')
        if p=='/health': return self.send_json(200,{'ok':True})
        return self.send_json(404,{'error':'No encontrado'})
    def do_PUT(self):
        if urlsplit(self.path).path!='/api/data': return self.send_json(404,{'error':'No encontrado'})
        key=self.headers.get('X-AeroDocs-Edit-Token','')
        if not TOKEN or not hmac.compare_digest(key,TOKEN): return self.send_json(401,{'error':'Clave de edición incorrecta'})
        if self.headers.get('Content-Type','').split(';')[0].strip().lower()!='application/json': return self.send_json(415,{'error':'Content-Type inválido'})
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<1 or n>2_000_000: return self.send_json(413,{'error':'Contenido demasiado grande'})
            payload=json.loads(self.rfile.read(n))
            data=payload['data']; revision=payload['expectedRevision']
            if type(revision)!=int or not valid_data(data): return self.send_json(422,{'error':'Datos inválidos'})
        except (ValueError,KeyError,TypeError,json.JSONDecodeError):return self.send_json(400,{'error':'Solicitud inválida'})
        with LOCK:
            with connect() as con:
                current=con.execute('SELECT revision FROM repository WHERE id=1').fetchone()[0]
                if current!=revision:return self.send_json(409,{'error':'Hay una actualización más reciente','revision':current})
                next_revision=current+1
                con.execute('UPDATE repository SET revision=?,content=? WHERE id=1',(next_revision,json.dumps(data,ensure_ascii=False)))
        return self.send_json(200,{'revision':next_revision})

def main():
    if not TOKEN or len(TOKEN)<16:
        raise SystemExit('Configura AERODOCS_EDIT_TOKEN con una clave de al menos 16 caracteres antes de iniciar el servidor.')
    init_database()
    print(f'AeroDocs en http://{HOST}:{PORT}/ (publicar con HTTPS y autenticación corporativa antes de exponerlo)')
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()

if __name__=='__main__':main()
