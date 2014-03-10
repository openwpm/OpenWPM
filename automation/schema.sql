/* This file is sourced during the initialization
 * of the crawler. Make sure everything is CREATE
 * IF NOT EXISTS, otherwise there will be errors
 */

/* Crawler Tables */

CREATE TABLE IF NOT EXISTS crawl (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    db_location VARCHAR(500) NOT NULL,
    profile VARCHAR(200),
    description TEXT,
    finished BOOLEAN NOT NULL DEFAULT 0);

CREATE TABLE IF NOT EXISTS xpath (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    url VARCHAR(500) NOT NULL,
    xpath VARCHAR(500) NOT NULL,
    absolute_xpath VARCHAR(500),
    ctime DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, url));

/* Proxy Tables */

CREATE TABLE IF NOT EXISTS javascript (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_id INTEGER NOT NULL,
    top_url VARCHAR[500] NOT NULL,
    javascript TEXT NOT NULL);

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


