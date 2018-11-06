import OnChangedCause = browser.cookies.OnChangedCause;

export type DateTime = string;

export interface Navigation {
  id?: number;
  incognito?: number;
  crawl_id?: number;
  visit_id?: number;
  extension_session_uuid?: string;
  process_id?: number;
  window_id?: number;
  tab_id?: number;
  tab_opener_tab_id?: number;
  frame_id?: number;
  parent_frame_id?: number;
  window_width?: number;
  window_height?: number;
  window_type?: string;
  tab_width?: number;
  tab_height?: number;
  tab_cookie_store_id?: string;
  uuid?: string;
  url?: string;
  transition_qualifiers?: string;
  transition_type?: string;
  committed_time_stamp?: DateTime;
}

export interface HttpRequest {
  id?: number;
  incognito?: number;
  crawl_id?: number;
  visit_id?: number;
  extension_session_uuid?: string;
  window_id?: number;
  tab_id?: number;
  frame_id?: number;
  url: string;
  top_level_url?: string;
  parent_frame_id?: number;
  frame_ancestors?: string;
  method: string;
  referrer: string;
  headers: string;
  request_id: string;
  is_XHR?: number;
  is_frame_load?: number;
  is_full_page?: number;
  is_third_party_channel?: number;
  is_third_party_to_top_window?: number;
  triggering_origin?: string;
  loading_origin?: string;
  loading_href?: string;
  req_call_stack?: string;
  resource_type: string;
  post_body?: string;
  time_stamp: DateTime;
}

export interface HttpResponse {
  id?: number;
  incognito?: number;
  crawl_id?: number;
  visit_id?: number;
  extension_session_uuid?: string;
  window_id?: number;
  tab_id?: number;
  frame_id?: number;
  url: string;
  method: string;
  referrer: string;
  response_status: number;
  response_status_text: string;
  is_cached: number;
  headers: string;
  request_id: string;
  location: string;
  time_stamp: DateTime;
  content_hash?: string;
}

export interface HttpRedirect {
  id?: number;
  incognito?: number;
  crawl_id?: number;
  visit_id?: number;
  old_request_id?: string;
  new_request_id?: string;
  extension_session_uuid?: string;
  window_id?: number;
  tab_id?: number;
  frame_id?: number;
  response_status?: number;
  response_status_text?: string;
  time_stamp: DateTime;
}

export interface JavascriptOperation {
  id?: number;
  incognito?: number;
  crawl_id?: number;
  visit_id?: number;
  extension_session_uuid?: string;
  window_id?: number;
  tab_id?: number;
  frame_id?: number;
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
  time_stamp: DateTime;
}

export interface JavascriptCookie {
  expiry?: DateTime;
  is_http_only?: number;
  is_host_only?: number;
  is_session?: number;
  host?: string;
  is_secure?: number;
  name?: string;
  path?: string;
  value?: string;
  same_site?: string;
  first_party_domain?: string;
  store_id?: string;
  time_stamp: DateTime;
}

export interface JavascriptCookieRecord extends JavascriptCookie {
  id?: number;
  crawl_id?: number;
  visit_id?: number;
  extension_session_uuid?: string;
  record_type?: "deleted" | "added-or-changed" | "manual-export";
  change_cause?: OnChangedCause;
}
