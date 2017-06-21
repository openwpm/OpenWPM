#!/usr/bin/env python

import jinja2
import sqlite3

def make_output(headings, rows):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    TEMPLATE_FILE = "./template.jinja"
    OUTPUT_FILE = "./output.html"
    template = templateEnv.get_template( TEMPLATE_FILE)

    new_rows=[]
    for row in rows:
        new_row=[]
        for element in row:
            if isinstance(element, unicode):
                element = element.rstrip()
                if element.startswith("http://") or element.startswith("https://"):
                    element = "<a href='" + element + "'>" + element +"</a>"
            new_row.append(element)
        new_rows.append(new_row)

    templateVars = { "title" : "Mobile JS scripts",
            "headings" : headings,
            "rows" : new_rows,
            "len_rows" : len(new_rows)}
    outputText = template.render( templateVars )
    print outputText
    with open(OUTPUT_FILE, 'w') as f:
        f.write(outputText)

def main():
    SQLITE_FILE = "crawl.sqlite"
    connection = sqlite3.connect(SQLITE_FILE)
    QUERY="SELECT site_visits.visit_id,site_visits.site_url,javascript.script_url,javascript.parameter_value,javascript.symbol " + \
            " FROM site_visits, javascript " + \
            " WHERE javascript.visit_id==site_visits.visit_id " + \
            " AND symbol " + \
            " LIKE 'window.addEventListener' AND parameter_value " + \
            " LIKE '%device%' GROUP BY site_visits.site_url,javascript.script_url " + \
            " ORDER BY javascript.script_url"
    print QUERY
    rows = connection.execute(QUERY)
    headings = list(map(lambda x: x[0], rows.description))
    make_output(headings, rows)


if __name__ == '__main__':
      main()
