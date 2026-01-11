import sqlite3
from pymongo import MongoClient
from collections import defaultdict

# SQLite- und MongoDB-Verbindung
sqlite_path = "datadir/crawl-data-2025-08-27.sqlite"
mongo_client = MongoClient("mongodb://root:examplepassword@localhost:27017/", authSource="admin")
db = mongo_client["crawler_analysis"]

conn = sqlite3.connect(sqlite_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Helper: komplette Tabelle laden
def load_table(name):
    cur.execute(f"SELECT * FROM {name}")
    return [dict(row) for row in cur.fetchall()]

# Tabellen laden
tasks = load_table("task")
crawls = load_table("crawl")
site_visits = load_table("site_visits")
http_requests = load_table("http_requests")
http_responses = load_table("http_responses")
javascript = load_table("javascript")
javascript_cookies = load_table("javascript_cookies")
navigations = load_table("navigations")
http_redirects = load_table("http_redirects")
crawl_history = load_table("crawl_history")
callstacks = load_table("callstacks")
dns_responses = load_table("dns_responses")
incomplete_visits = load_table("incomplete_visits")

# Index-Dictionaries vorbereiten
tasks_by_id = {t["task_id"]: t for t in tasks}
crawls_by_id = {c["browser_id"]: c for c in crawls}

req_by_visit = defaultdict(list)
for r in http_requests:
    req_by_visit[r["visit_id"]].append(r)

res_by_visit = defaultdict(list)
for r in http_responses:
    res_by_visit[r["visit_id"]].append(r)

js_by_visit = defaultdict(list)
for j in javascript:
    js_by_visit[j["visit_id"]].append(j)

cookies_by_visit = defaultdict(list)
for c in javascript_cookies:
    cookies_by_visit[c["visit_id"]].append(c)

nav_by_visit = defaultdict(list)
for n in navigations:
    nav_by_visit[n["visit_id"]].append(n)

redirect_by_visit = defaultdict(list)
for rd in http_redirects:
    redirect_by_visit[rd["visit_id"]].append(rd)

history_by_visit = defaultdict(list)
for h in crawl_history:
    history_by_visit[h["visit_id"]].append(h)

callstack_by_visit = defaultdict(list)
for cs in callstacks:
    callstack_by_visit[cs["visit_id"]].append(cs)

dns_by_visit = defaultdict(list)
for dns in dns_responses:
    dns_by_visit[dns["visit_id"]].append(dns)

# Jede site_visit einzeln als Dokument speichern
for visit in site_visits:
    visit_id = visit["visit_id"]
    browser_id = visit["browser_id"]
    crawl = crawls_by_id.get(browser_id)
    task = tasks_by_id.get(crawl["task_id"]) if crawl else None

    doc = {
        "task": task,
        "crawl": crawl,
        "visit": visit,
        "http_requests": req_by_visit[visit_id],
        "http_responses": res_by_visit[visit_id],
        "javascript": js_by_visit[visit_id],
        "javascript_cookies": cookies_by_visit[visit_id],
        "navigations": nav_by_visit[visit_id],
        "http_redirects": redirect_by_visit[visit_id],
        "crawl_history": history_by_visit[visit_id],
        "callstacks": callstack_by_visit[visit_id],
        "dns_responses": dns_by_visit[visit_id]
    }

    db.site_visits.insert_one(doc)

print(f"{len(site_visits)} Dokumente erfolgreich nach MongoDB übertragen.")
