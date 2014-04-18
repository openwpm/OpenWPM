from automation import TaskManager
import sys
from os.path import expanduser
import sqlite3
import time

def sitecrawler(d, user, db_loc, db_name, desc):
    """
    Takes as input a dict with publisher, category, URLs, user number, entry_id (key)
    Database located locally on user's desktop as rss.sqlite
    Tracks URLs successfully traversed in DB table CrawlHistory
    Tries to load a preexisting profile located at profile_dump_loc on DropBox
        If successful, adds to the profile and overwrites the profile on DropBox
    Saves the profile to the Dropbox location corresponding to the profile_dump_loc
    """
    # Unpack the input dictionary
    pub = None
    cat = None
    for k in d.keys():
        pub = d[k]['publisher']
        cat = d[k]['category']
        break


    # Pull out all the URLs, store as tuple of (URL, entry_id)
    urls = list()
    for key in d:
        urls.append((d[key]['url'], key))

    profile_dump_loc = db_loc + 'profiles/news/' + pub + '/' + cat + '/' + str(user) + '/'
    write_profile = False
    profile_saved = False
    prof_load_successful = False
    profile = None

    # initialize crawler
    manager = TaskManager.TaskManager(db_loc, db_name, profile=profile_dump_loc,
                                      headless=False, description=desc, num_browsers=1)

    # Traverse the category links
    traversed_list = list()
    for link in urls:
        try:
            manager.get(link[0])
        except:
            print("Couldn't navigate to %s" % (link[0]))
            continue
        time.sleep(3)
        traversed_list.append(link)
        #if len(traversed_list) >= 20:
        #   break

    import ipdb; ipdb.set_trace()
    # Make sure we actually traversed some URLs before writing the profile
    # This prevents us from writing the profile or DB when we are debugging
    if len(traversed_list) > 10:
        write_profile = True

    if write_profile == True:
        print("Saving profile: %s to %s" % (category, profile_dump_loc) )
        print profile
        print manager.profile_path
        #manager.dump_profile(profile_dump_loc)
        import ipdb; ipdb.set_trace()
        try:
            manager.dump_profile(profile_dump_loc, index=0)
            # log completed creation of publisher and category
            print("Completed Creation of Profile: %s %s" % (publisher, category))
        except:
            print("Error in crawl, did not create new profile for: %s" % (profile_dump_loc))
            print("URLs for %s: %s" % (profile_dump_loc, str(urls)))

    # Close the crawler
    manager.close()

if __name__ == '__main__':
    # Take user number as input
    # Read from RSSEntries table in DB
    # Extract information into a dict
    # Execute crawl
    pub_list = ['FN', 'CNN', 'HP', 'DM', 'BBC', 'GUARDIAN', 'NBC', 'USA', 'TIME']
    category_list = ['arts, culture and entertainment',
                     'crime, law and justice',
                     'disaster and accident',
                     'economy, business and finance',
                     'education',
                     'environmental issue',
                     'health',
                     'human interest',
                     'labour',
                     'lifestyle and leisure',
                     'politics',
                     'religion and belief',
                     'science and technology',
                     'social issue',
                     'sport',
                     'unrest, conflicts and war',
                     'weather'
                     ]

    # Pull CL arguments
    if len(sys.argv) >= 1:
        user_num = int(sys.argv[1])

    # Get links from DB for this publisher:category pair
    home = expanduser("~")
    db_loc = home + '/Desktop/'
    db_name = 'profile_generator.sqlite'
    desc = 'profile generation'
    conn = sqlite3.connect(db_loc + db_name)
    cur = conn.cursor()

    for publisher in pub_list:
        for category in category_list:
            url_dict = dict()
            cur.execute('SELECT publisher, article_url, entry_id, article_topic FROM RSSEntries as r, \
            ArticleCategories as a WHERE r.publisher = ? AND r.article_topic=1 AND \
            a.article_id = r.entry_id AND a.category = ?', (publisher, category,))
            data = cur.fetchall()
            # data[x][0] is publisher
            # data[x][1] is URL
            # data[x][2] is entry_id
            url_crawl_limit = 0
            for item in data:
                if url_crawl_limit == 11:
                    break
                url_dict[item[2]] = {
                    'publisher': item[0],
                    'url': item[1],
                    'category': category
                }
                url_crawl_limit += 1
            #import ipdb; ipdb.set_trace()
            sitecrawler(url_dict, user_num, db_loc, db_name, desc)
            #import ipdb; ipdb.set_trace()
            break
        break