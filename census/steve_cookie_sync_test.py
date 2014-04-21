#Just playing around
import measure_cookie_sync
import extract_cookie_ids

print "extract cookies from 1"
c1 = extract_cookie_ids.extract_cookie_candidates_from_db("/home/sengleha/Desktop/cookie_sync/alexa_basic1.sqlite")

print "extract cookies from 2"
c2 = extract_cookie_ids.extract_cookie_candidates_from_db("/home/sengleha/Desktop/cookie_sync/alexa_basic2.sqlite")

print "find common cookies"
extracted = extract_cookie_ids.extract_common_persistent_ids([c1, c2])

print "build known list"
known = extract_cookie_ids.extract_known_cookies_from_db("/home/sengleha/Desktop/cookie_sync/alexa_basic1.sqlite", extracted)

print "build sync graph"
G = measure_cookie_sync.build_sync_graph("/home/sengleha/Desktop/cookie_sync/alexa_basic1.sqlite", extracted)

import ipdb; ipdb.set_trace()
