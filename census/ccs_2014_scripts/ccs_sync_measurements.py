import extract_cookie_ids
import extract_id_knowledge
import census_util

# OVERALL COOKIE SYNC SCRIPT
# prints off the relevant statistics for the cookie syncing studies, given two crawl databases
def output_sync_measurements(db1, db2):
    print "0"
    # extract the cookie ids on a per-database basis
    cookies_db1 = extract_cookie_ids.extract_persistent_ids_from_db(db1)
    cookies_db2 = extract_cookie_ids.extract_persistent_ids_from_db(db2)

    print "1"

    # get the cookies that appear to be consistent ids and extract their values from db1
    id_cookies = extract_cookie_ids.extract_common_id_cookies([cookies_db1, cookies_db2])
    known_ids = extract_cookie_ids.extract_known_cookies_from_db(db1, id_cookies)

    print "2"

    # build the three maps that are most fundamental to the analysis
    id_to_cookie_map = extract_cookie_ids.map_ids_to_cookies(known_ids)
    id_to_cookie_map_pruned = census_util.prune_list_dict(id_to_cookie_map)

    id_to_domain_map = extract_id_knowledge.build_id_knowledge_dictionary(id_to_cookie_map, db1)
    id_to_domain_map = census_util.prune_list_dict(id_to_domain_map)

    domain_to_id_map = extract_id_knowledge.map_domains_to_known_ids(id_to_domain_map)
    domain_to_id_map_pruned = census_util.prune_list_dict(domain_to_id_map)

    # BASIC STATS
    print "NUMBER OF IDS: " + str(len(id_to_cookie_map))
    print "NUMBER OF ID COOKIES: " + str(len(known_ids))
    print "NUMBER OF IDS IN SYNCS: " + str(len(id_to_domain_map))
    print "NUMBER OF ID COOKIES IN SYNC: " + str(sum([len(id_to_cookie_map[key]) for key in id_to_domain_map]))

    id_to_domain_tuples = census_util.sort_tuples([(key, len(id_to_domain_map[key])) for key in id_to_domain_map])
    print id_to_domain_tuples
    domain_to_id_counts = census_util.sort_tuples([(key, len(domain_to_id_map[key])) for key in domain_to_id_map])
    print domain_to_id_counts

if __name__ == "__main__":
    crawl_db1 = "/home/christian/Desktop/alexa_500_1.sqlite"
    crawl_db2 = "/home/christian/Desktop/alexa_500_2.sqlite"
    output_sync_measurements(crawl_db1, crawl_db2)


