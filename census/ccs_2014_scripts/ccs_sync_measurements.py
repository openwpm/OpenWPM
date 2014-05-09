import extract_cookie_ids
import extract_id_knowledge
import census_util


import Queue


# BFS HOP ANALYSIS
# for a given domain, returns a sorted list of sites within <hops> steps away in the sync graph
def build_hop_neighborhood(seed_domain, hop, domain_to_id, id_to_domain):
    domains_explored = set()  # list of domains we've visited
    search_queue = Queue.Queue()  # list of the sites that we'll be visiting
    search_queue.put((seed_domain, 0))  # seeds the search with the initial domain

    # performs the BFS neighborhood search
    while not search_queue.empty():
        curr_domain, curr_depth = search_queue.get()

        # break the search if the nodes are too far away
        if curr_depth > hop:
            break

        # don't explore the node if we've already seen it
        if curr_domain in domains_explored:
            continue

        domains_explored.add(curr_domain)

        # don't expand out to neighbors if we are at the edge of the neighborhood
        if curr_depth == hop:
            continue

        # update the search queue
        for cookie_id in domain_to_id[curr_domain]:
            for domain in id_to_domain[cookie_id]:
                search_queue.put((domain, curr_depth + 1))

    neighborhood = list(domains_explored)
    neighborhood.sort()
    return neighborhood

# OVERALL COOKIE SYNC SCRIPT
# prints off the relevant statistics for the cookie syncing studies, given two crawl databases
def output_sync_measurements(db1, db2):
    print "0"
    # extract the cookie ids on a per-database basis
    cookies_db1 = extract_cookie_ids.extract_persistent_ids_from_dbs([db1])
    cookies_db2 = extract_cookie_ids.extract_persistent_ids_from_dbs([db2])

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


    id_to_domain_counts = census_util.sort_tuples([(key, len(id_to_domain_map[key])) for key in id_to_domain_map])
    print id_to_domain_counts
    domain_to_id_counts = census_util.sort_tuples([(key, len(domain_to_id_map[key])) for key in domain_to_id_map])
    print domain_to_id_counts

    print "NUMBER OF DOMAINS IN SYNC " + str(len(domain_to_id_map))

    for domain, count in domain_to_id_counts:
        depth1 = len(build_hop_neighborhood(domain, 1, domain_to_id_map, id_to_domain_map))
        depth2 = len(build_hop_neighborhood(domain, 2, domain_to_id_map, id_to_domain_map))
        depth3 = len(build_hop_neighborhood(domain, 3, domain_to_id_map, id_to_domain_map))
        print str(domain) + "\t" + str(count) + "\t" + str(depth1) + "\t" + str(depth2) + "\t" + str(depth3)

# RESPAWN / SYNC SCRIPT
# checks for respawning and syncing of cookie data
# baseline is a list of at least one database used to perform the diffs (but we don't actually care about spawning here)
# pre_clear is the first database of some sort of crawl run before we make a clear command
# post_clear is the second datbase of some crawl after the clear - here we care about the chance of respawning
def perform_respawn_resync_study(baseline_dbs, pre_clear_db, post_clear_db):
    print "Extracting initial set of ID cookies"
    cookies_baseline = extract_cookie_ids.extract_persistent_ids_from_dbs([baseline_dbs])
    cookies_pre_clear = extract_cookie_ids.extract_persistent_ids_from_dbs([pre_clear_db])

    print "Extracting the pre-clear IDs"
    id_cookies = extract_cookie_ids.extract_common_id_cookies([cookies_baseline, cookies_pre_clear])
    pre_clear_ids = extract_cookie_ids.extract_known_cookies_from_db(pre_clear_db, id_cookies)

    print "Build the sync maps on the post_clear db"
    # build the three maps that are most fundamental to the analysis
    id_to_cookie_map = extract_cookie_ids.map_ids_to_cookies(pre_clear_ids)
    id_to_cookie_map_pruned = census_util.prune_list_dict(id_to_cookie_map)

    id_to_domain_map = extract_id_knowledge.build_id_knowledge_dictionary(id_to_cookie_map, post_clear_db)
    id_to_domain_map = census_util.prune_list_dict(id_to_domain_map)

    domain_to_id_map = extract_id_knowledge.map_domains_to_known_ids(id_to_domain_map)
    domain_to_id_map_pruned = census_util.prune_list_dict(domain_to_id_map)
    

if __name__ == "__main__":
    crawl_db1 = "/home/christian/Desktop/alexa10k_1.sqlite"
    crawl_db2 = "/home/christian/Desktop/alexa10k_2.sqlite"
    base1 = "/home/christian/Desktop/alexa500_rocklor_1.sqlite"
    pre_clear = "/home/christian/Desktop/alexa500_satrap_1.sqlite"
    post_clear = "/home/christian/Desktop/alexa500_satrap_2.sqlite"
    perform_respawn_resync_study(base1, pre_clear, post_clear)
    #output_sync_measurements(pre_clear, post_clear)


