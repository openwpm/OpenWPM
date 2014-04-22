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
    fourthparty VARCHAR(200),
    debugging VARCHAR(200),
    timeout INTEGER,
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
    top_url VARCHAR[500] NOT NULL);

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
    top_url VARCHAR[500] NOT NULL);


CREATE TABLE IF NOT EXISTS cookies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER NOT NULL,
    domain VARCHAR[500] NOT NULL,
    name VARCHAR[500] NOT NULL,
    value VARCHAR[500] NOT NULL,
    expiry VARCHAR[500] NOT NULL,
    accessed VARCHAR[500] NOT NULL,
    referrer VARCHAR[500] NOT NULL,
    top_url VARCHAR[500] NOT NULL);

/* Crawl History table */
CREATE TABLE IF NOT EXISTS CrawlHistory (
    crawl_id INTEGER,
    command TEXT,
    arguments TEXT,
    bool_success INTEGER,
    dtg DATETIME DEFAULT (CURRENT_TIMESTAMP),
    FOREIGN KEY(crawl_id) REFERENCES crawl(id));
