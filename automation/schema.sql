/* This file is sourced during the initialization
 * of the crawler. Make sure everything is CREATE
 * IF NOT EXISTS, otherwise there will be errors
 */

/* Crawler Tables */
CREATE TABLE IF NOT EXISTS task (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT);

CREATE TABLE IF NOT EXISTS crawl (
    crawl_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    profile VARCHAR(200),
    browser VARCHAR(200),
    headless VARCHAR(200),
    proxy VARCHAR(200),
    debugging VARCHAR(200),
    timeout INTEGER,
    disable_flash VARCHAR(200),
    extensions VARCHAR(200),
    screen_res VARCHAR(50),
    ua_string VARCHAR(200),
    finished BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY(task_id) REFERENCES task(task_id));

CREATE TABLE IF NOT EXISTS xpath (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    url VARCHAR(500) NOT NULL,
    xpath VARCHAR(500) NOT NULL,
    absolute_xpath VARCHAR(500),
    ctime DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, url));

/* Proxy Tables */

/* TODO: add publix_suffix to db structure */
/* TODO: link with headers */
CREATE TABLE IF NOT EXISTS http_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER NOT NULL,
    url VARCHAR(500) NOT NULL,
    method VARCHAR(500) NOT NULL,
    referrer VARCHAR(500) NOT NULL,
    headers VARCHAR(500) NOT NULL,
    top_url VARCHAR(500) NOT NULL,
    time_stamp VARCHAR(500) NOT NULL);

/* TODO: add publix_suffix to db structure */
/* TODO: link with headers */
/* TODO: link with requests */
CREATE TABLE IF NOT EXISTS http_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER NOT NULL,
    url VARCHAR(500) NOT NULL,
    method VARCHAR(500) NOT NULL,
    referrer VARCHAR(500) NOT NULL,
    response_status INTEGER NOT NULL,
    response_status_text VARCHAR(500) NOT NULL,
    headers VARCHAR(500) NOT NULL,
    location VARCHAR(500) NOT NULL,
    top_url VARCHAR(500) NOT NULL,
    time_stamp VARCHAR(500) NOT NULL);

/* Firefox Storage Vector Dumps */

CREATE TABLE IF NOT EXISTS flash_cookies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER NOT NULL,
    page_url VARCHAR(500) NOT NULL,
    domain VARCHAR(500),
    filename VARCHAR(500),
    local_path VARCHAR(1000),
    key TEXT,
    content TEXT,
    FOREIGN KEY(crawl_id) REFERENCES crawl(id));

CREATE TABLE IF NOT EXISTS profile_cookies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER NOT NULL,
    page_url VARCHAR(500) NOT NULL,
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
    FOREIGN KEY(crawl_id) REFERENCES crawl(id));

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
