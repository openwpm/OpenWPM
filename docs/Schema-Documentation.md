# Schema Documentation

- [Schema Documentation](#schema-documentation)
  - [site_visits](#site_visits)
  - [crawl_history](#crawl_history)
  - [http_requests](#http_requests)
  - [http_responses](#http_responses)
  - [http_redirects](#http_redirects)
  - [javascript](#javascript)
  - [javascript_cookies](#javascript_cookies)
  - [navigations](#navigations)
  - [callstacks](#callstacks)
  - [incomplete_visits](#incomplete_visits)

This is an overview of all tables currently existing in OpenWPM. Over time we want to add
a description for all fields and tables here.
If you have any questions on any field, please file an issue or ask in the [OpenWPM riot channel](https://matrix.to/#/#OpenWPM:mozilla.org?via=mozilla.org) and we'll
update the description of the field here.

## site_visits

| Column Name | Type   | nullable | Description |
| ----------- | ------ | -------- | ----------- |
| visit_id    | int64  | False    |             |
| crawl_id    | uint32 | False    |             |
| instance_id | uint32 | False    |             |
| site_url    | string | False    |             |
| site_rank   | uint32 |          |

## crawl_history

| Column Name    | Type   | nullable | Description |
| -------------- | ------ | -------- | ----------- |
| crawl_id       | uint32 | False    |
| visit_id       | int64  | False    |             |
| instance_id    | uint32 | False    |             |
| command        | string |          |
| arguments      | string |          |
| retry_number   | int8   |          |             |
| command_status | string |          |             |
| error          | string |          |             |
| traceback      | string |          |
| duration       | int64  |          | A timer that logs how long a command took (in milliseconds)|

## http_requests

| Column Name                  | Type   | nullable | Description |
| ---------------------------- | ------ | -------- | ----------- |
| incognito                    | int32  |          |             |
| crawl_id                     | uint32 |          |             |
| visit_id                     | int64  |          |             |
| instance_id                  | uint32 | False    |             |
| extension_session_uuid       | string |          |             |
| event_ordinal                | int64  |          |             |
| window_id                    | int64  |          |             |
| tab_id                       | int64  |          |             |
| frame_id                     | int64  |          |             |
| url                          | string | False    |             |
| top_level_url                | string |          |             |
| parent_frame_id              | int64  |          |             |
| frame_ancestors              | string |          |             |
| method                       | string | False    |             |
| referrer                     | string | False    |             |
| headers                      | string | False    |             |
| request_id                   | string | False    |             |
| is_XHR                       | bool   |          |             |
| is_third_party_channel       | bool   |          |             |
| is_third_party_to_top_window | bool   |          |             |
| triggering_origin            | string |          |             |
| loading_origin               | string |          |             |
| loading_href                 | string |          |             |
| req_call_stack               | string |          |             |
| resource_type                | string | False    |             |
| post_body                    | string |          |             |
| post_body_raw                | string |          |             |
| time_stamp                   | string | False    |             |

## http_responses

| Column Name            | Type   | nullable | Description |
| ---------------------- | ------ | -------- | ----------- |
| incognito              | int32  |          |             |
| crawl_id               | uint32 |          |             |
| visit_id               | int64  |          |             |
| instance_id            | uint32 | False    |             |
| extension_session_uuid | string |          |             |
| event_ordinal          | int64  |          |             |
| window_id              | int64  |          |             |
| tab_id                 | int64  |          |             |
| frame_id               | int64  |          |             |
| url                    | string | False    |             |
| method                 | string | False    |             |
| response_status        | int64  |          |             |
| response_status_text   | string | False    |             |
| is_cached              | bool   | False    |             |
| headers                | string | False    |             |
| request_id             | string | False    |             |
| location               | string | False    |             |
| time_stamp             | string | False    |             |
| content_hash           | string |          |

## http_redirects

| Column Name            | Type   | nullable | Description |
| ---------------------- | ------ | -------- | ----------- |
| incognito              | int32  |          |             |
| crawl_id               | uint32 |          |             |
| visit_id               | int64  |          |             |
| instance_id            | uint32 | False    |             |
| old_request_url        | string |          |             |
| old_request_id         | string |          |             |
| new_request_url        | string |          |             |
| new_request_id         | string |          |             |
| extension_session_uuid | string |          |             |
| event_ordinal          | int64  |          |             |
| window_id              | int64  |          |             |
| tab_id                 | int64  |          |             |
| frame_id               | int64  |          |             |
| response_status        | int64  |          |             |
| response_status_text   | string | False    |             |
| headers                | string |          |             |
| time_stamp             | string | False    |

## javascript

| Column Name               | Type   | nullable | Description |
| ------------------------- | ------ | -------- | ----------- |
| incognito                 | int32  |          |             |
| crawl_id                  | uint32 |          |             |
| visit_id                  | int64  |          |             |
| instance_id               | uint32 | False    |             |
| extension_session_uuid    | string |          |             |
| event_ordinal             | int64  |          |             |
| page_scoped_event_ordinal | int64  |          |             |
| window_id                 | int64  |          |             |
| tab_id                    | int64  |          |             |
| frame_id                  | int64  |          |             |
| script_url                | string |          |             |
| script_line               | string |          |             |
| script_col                | string |          |             |
| func_name                 | string |          |             |
| script_loc_eval           | string |          |             |
| document_url              | string |          |             |
| top_level_url             | string |          |             |
| call_stack                | string |          |             |
| symbol                    | string |          |             |
| operation                 | string |          |             |
| value                     | string |          |             |
| arguments                 | string |          |             |
| time_stamp                | string | False    |

## javascript_cookies

| Column Name            | Type   | nullable | Description |
| ---------------------- | ------ | -------- | ----------- |
| crawl_id               | uint32 |          |             |
| visit_id               | int64  |          |             |
| instance_id            | uint32 | False    |             |
| extension_session_uuid | string |          |             |
| event_ordinal          | int64  |          |             |
| record_type            | string |          |             |
| change_cause           | string |          |             |
| expiry                 | string |          |             |
| is_http_only           | bool   |          |             |
| is_host_only           | bool   |          |             |
| is_session             | bool   |          |             |
| host                   | string |          |             |
| is_secure              | bool   |          |             |
| name                   | string |          |             |
| path                   | string |          |             |
| value                  | string |          |             |
| same_site              | string |          |             |
| first_party_domain     | string |          |             |
| store_id               | string |          |             |
| time_stamp             | string |          |

## navigations

| Column Name                   | Type   | nullable | Description |
| ----------------------------- | ------ | -------- | ----------- |
| incognito                     | int32  |          |             |
| crawl_id                      | uint32 |          |             |
| visit_id                      | int64  |          |             |
| instance_id                   | uint32 | False    |             |
| extension_session_uuid        | string |          |             |
| process_id                    | int64  |          |             |
| window_id                     | int64  |          |             |
| tab_id                        | int64  |          |             |
| tab_opener_tab_id             | int64  |          |             |
| frame_id                      | int64  |          |             |
| parent_frame_id               | int64  |          |             |
| window_width                  | int64  |          |             |
| window_height                 | int64  |          |             |
| window_type                   | string |          |             |
| tab_width                     | int64  |          |             |
| tab_height                    | int64  |          |             |
| tab_cookie_store_id           | string |          |             |
| uuid                          | string |          |             |
| url                           | string |          |             |
| transition_qualifiers         | string |          |             |
| transition_type               | string |          |             |
| before_navigate_event_ordinal | int64  |          |             |
| before_navigate_time_stamp    | string |          |             |
| committed_event_ordinal       | int64  |          |             |
| time_stamp                    | string |          |

## callstacks

| Column Name | Type   | nullable | Description |
| ----------- | ------ | -------- | ----------- |
| visit_id    | int64  | False    |             |
| request_id  | int64  | False    |             |
| crawl_id    | uint32 | False    |             |
| instance_id | uint32 | False    |             |
| call_stack  | string |          |

## incomplete_visits

| Column Name | Type   | nullable | Description |
| ----------- | ------ | -------- | ----------- |
| visit_id    | int64  | False    |             |
| instance_id | uint32 | False    |
