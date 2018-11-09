import calendar
import psycopg2
import os

GCSQL_PWD = os.environ["GCSQL_PWD"]


def get_last_inspect(inspector="OpenWPM"):
    """Get the last time urls were scanned by OpenWPM

    Because we are using Google CloudSQL, in order for this to work,
    you must first run "./cloud_sql_proxy \
    -instances=sports-streaming-security:us-west1:cs356-streams=tcp:6543 \
    -credential_file=sports-streaming-security-64e6f13735d5.json" in another
    terminal to set up port forwarding as required. Note that the second argument
    in this command is the authentication file containing the private key for the
    GCP instance, which you must get from Hudson.
    More information can be found in db_setup.txt, in this directory.


    :param inspector: The name of the inspector scanning these urls
    :rtype: int
    """

    # TODO: Return errors if this fails
    conn = psycopg2.connect(
        host="localhost",
        port="6543",
        dbname="postgres",
        user="postgres",
        password=GCSQL_PWD,
    )
    cur = conn.cursor()
    select_cmd = "SELECT scanned FROM last_inspect WHERE inspector = '" + inspector + "'"
    cur.execute(select_cmd)
    rows = cur.fetchall()
    last_time = rows[0][0]
    cur.close()
    conn.close()
    return calendar.timegm(last_time.timetuple())


def update_last_scanned(scan_time, inspector="OpenWPM"):
    """Save the last time urls were added to the postgres database.

    Because we are using Google CloudSQL, in order for this to work,
    you must first run "./cloud_sql_proxy \
    -instances=sports-streaming-security:us-west1:cs356-streams=tcp:6543 \
    -credential_file=sports-streaming-security-64e6f13735d5.json" in another
    terminal to set up port forwarding as required. Note that the second argument
    in this command is the authentication file containing the private key for the
    GCP instance, which you must get from Hudson.
    More information can be found in db_setup.txt, in this directory.

    This function returns positive on success, negative on failure

    :param inspector: The name of the inspector that scanned
    :param time: Unix timestamp of the last scan
    :rtype: int
    """

    # TODO: Return errors if this fails
    conn = psycopg2.connect(
        host="localhost",
        port="6543",
        dbname="postgres",
        user="postgres",
        password=GCSQL_PWD,
    )
    cur = conn.cursor()
    update_cmd = (
        "UPDATE last_inspect SET " "(scanned)" "= (%s) WHERE inspector = '" + inspector + "'"
    )
    cur.execute(update_cmd, (psycopg2.TimestampFromTicks(scan_time),))
    conn.commit()
    cur.close()
    conn.close()
    return 0

def get_urls_to_inspect():
    """Get all new URLS since the last successful inspection

    :rtype: List of Strings
    """

    last_inspect_time = get_last_inspect()
    conn = psycopg2.connect(
        host="localhost",
        port="6543",
        dbname="postgres",
        user="postgres",
        password=GCSQL_PWD,
    )
    cur = conn.cursor()
    get_urls_cmd = (
        "SELECT url FROM stream_urls WHERE (last_access) > (%s)"
    )
    cur.execute(get_urls_cmd, (psycopg2.TimestampFromTicks(last_inspect_time),))
    rows = cur.fetchall()
    sites = []
    for row in rows:
        sites.append(row[0])
    print("num_urls: " + str(len(sites)))
    return sites
