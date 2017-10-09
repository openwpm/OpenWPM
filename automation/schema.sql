/* This file is sourced during the initialization
 * of the crawler. Make sure everything is CREATE
 * IF NOT EXISTS, otherwise there will be errors
 */

/* Crawler Tables */

CREATE TABLE IF NOT EXISTS task (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    manager_params TEXT NOT NULL,
    openwpm_version TEXT NOT NULL,
    browser_version TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS crawl (
    crawl_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    browser_params TEXT NOT NULL,
    screen_res TEXT,
    ua_string TEXT,
    finished BOOLEAN NOT NULL DEFAULT 0,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(task_id) REFERENCES task(task_id));

CREATE TABLE IF NOT EXISTS xpath (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    url VARCHAR(500) NOT NULL,
    xpath VARCHAR(500) NOT NULL,
    absolute_xpath VARCHAR(500),
    ctime DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, url));

CREATE TABLE IF NOT EXISTS site_visits (
    visit_id INTEGER PRIMARY KEY,
    crawl_id INTEGER NOT NULL,
    site_url VARCHAR(500) NOT NULL,
    FOREIGN KEY(crawl_id) REFERENCES crawl(id));

/* Firefox Storage Vector Dumps */

CREATE TABLE IF NOT EXISTS flash_cookies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER NOT NULL,
    visit_id INTEGER NOT NULL,
    domain VARCHAR(500),
    filename VARCHAR(500),
    local_path VARCHAR(1000),
    key TEXT,
    content TEXT,
    FOREIGN KEY(crawl_id) REFERENCES crawl(id),
    FOREIGN KEY(visit_id) REFERENCES site_visits(id));

CREATE TABLE IF NOT EXISTS profile_cookies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER NOT NULL,
    visit_id INTEGER NOT NULL,
    baseDomain TEXT,
    name TEXT,
    value TEXT,
    host TEXT,
    path TEXT,
    expiry INTEGER,
    accessed INTEGER,
    creationTime INTEGER,
    isSecure INTEGER,
    isHttpOnly INTEGER,
    FOREIGN KEY(crawl_id) REFERENCES crawl(id),
    FOREIGN KEY(visit_id) REFERENCES site_visits(id));

CREATE TABLE IF NOT EXISTS localStorage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER NOT NULL,
    page_url VARCHAR(500) NOT NULL,
    scope TEXT,
    KEY TEXT,
    value TEXT,
    FOREIGN KEY(crawl_id) REFERENCES crawl(id));

/* Crawl History table */
CREATE TABLE IF NOT EXISTS CrawlHistory (
    crawl_id INTEGER,
    command TEXT,
    arguments TEXT,
    bool_success INTEGER,
    dtg DATETIME DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY(crawl_id) REFERENCES crawl(id));

