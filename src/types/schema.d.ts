type DateTime = string;

export interface Task {
  task_id: number;
  start_time: DateTime;
  manager_params: string;
  openwpm_version: string;
  browser_version: string;
}

export interface Crawl {
  crawl_id: number;
  task_id: number;
  browser_params: string;
  start_time: DateTime;
  // FOREIGN KEY(task_id) REFERENCES task(task_id)
}

export interface SiteVisit {
  visit_id: number;
  crawl_id: number;
  site_url: string;
  // FOREIGN KEY(crawl_id) REFERENCES crawl(id)
}

export interface FlashCookie {
  id?: number;
  crawl_id?: number;
  visit_id?: number;
  domain?: string;
  filename?: string;
  local_path?: string;
  key?: string;
  content?: string;
  // FOREIGN KEY(crawl_id) REFERENCES crawl(id);
  // FOREIGN KEY(visit_id) REFERENCES site_visits(id)
}

export interface ProfileCookie {
  id?: number;
  crawl_id?: number;
  visit_id?: number;
  baseDomain?: string;
  name?: string;
  value?: string;
  host?: string;
  path?: string;
  expiry?: number;
  lastAccessed?: number;
  creationTime?: number;
  isSecure?: number;
  isHttpOnly?: number;
  // FOREIGN KEY(crawl_id) REFERENCES crawl(id);
  // FOREIGN KEY(visit_id) REFERENCES site_visits(id)
}

export interface CrawlHistoryEntry {
  crawl_id?: number;
  visit_id?: number;
  command?: string;
  arguments?: string;
  bool_success?: number;
  dtg?: DateTime; //  DEFAULT (CURRENT_TIMESTAMP)
  // FOREIGN KEY(crawl_id) REFERENCES crawl(id)
}

export interface HttpRequest {
  id?: number;
  crawl_id?: number;
  visit_id?: number;
  url: string;
  top_level_url?: string;
  method: string;
  referrer: string;
  headers: string;
  channel_id: string;
  is_XHR?: boolean;
  is_frame_load?: boolean;
  is_full_page?: boolean;
  is_third_party_channel?: boolean;
  is_third_party_to_top_window?: boolean;
  triggering_origin?: string;
  loading_origin?: string;
  loading_href?: string;
  req_call_stack?: string;
  resource_type: string;
  post_body?: string;
  time_stamp: string;
}

export interface HttpResponse {
  id?: number;
  crawl_id?: number;
  visit_id?: number;
  url: string;
  method: string;
  referrer: string;
  response_status: number;
  response_status_text: string;
  is_cached: boolean;
  headers: string;
  channel_id: string;
  location: string;
  time_stamp: string;
  content_hash?: string;
}

export interface HttpRedirect {
  id?: number;
  crawl_id?: number;
  visit_id?: number;
  old_channel_id?: string;
  new_channel_id?: string;
  is_temporary: boolean;
  is_permanent: boolean;
  is_internal: boolean;
  is_sts_upgrade: boolean;
  time_stamp: string;
}

export interface JavascriptOperation {
  id?: number;
  crawl_id?: number;
  visit_id?: number;
  script_url?: string;
  script_line?: string;
  script_col?: string;
  func_name?: string;
  script_loc_eval?: string;
  document_url?: string;
  top_level_url?: string;
  call_stack?: string;
  symbol?: string;
  operation?: string;
  value?: string;
  arguments?: string;
  time_stamp: string;
}

export interface JavascriptCookieChange {
  id?: number;
  crawl_id?: number;
  visit_id?: number;
  change?: "deleted" | "added" | "changed";
  creationTime?: DateTime;
  expiry?: DateTime;
  is_http_only?: number;
  is_host_only?: number;
  is_session?: number;
  last_accessed?: DateTime;
  raw_host?: string;
  expires?: number;
  host?: string;
  is_domain?: number;
  is_secure?: number;
  name?: string;
  path?: string;
  policy?: number;
  status?: number;
  value?: string;
  same_site?: string;
  first_party_domain?: string;
}
