# XPathUtil.py
# A collecton of utilities to extract and parse
# XPaths encountered while scraping.
#
# Steven Englehardt (github.com/englehardt)


import re

import bs4
from bs4 import BeautifulSoup as bs


def is_clickable(xpath):
    # We consider any xpath that has an 'a', 'button',
    # or 'input' tag to be clickable as it most likely
    # contains a link. It may make sense to see check
    # <input type="button"> or other tags...
    index_regex = re.compile(r'\[[^\]]*\]')  # match index and id brackets
    # check xpath for necessary tags
    temp = re.sub(index_regex, '', xpath)
    temp = temp.split('/')
    if 'a' in temp or 'button' in temp or 'input' in temp:
        return True
    return False

# ExtractXPath(element, use_id)
# - element: a bs4 tag node
# - use_id: defaults True
#
# Traverses up the tag tree of a Beautiful Soup node
# to return the XPath of that node.
#
# Use of ids is preferred when the xpath will be used
# outside of BeautifulSoup. Since an id is unique to
# all elements of the tree, it allows the use of a
# wildcard for all parent nodes. This minimizes the
# chances of incorrect indexing (which can occur if
# javascript changes a page during processing).


class ExtractXPathError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def check_previous_tags(node, use_id=True):
    # index of node
    counter = 1
    for tag in node.previous_siblings:
        if type(tag) != bs4.element.Tag:
            continue
        elif tag.name == node.name:
            counter += 1

    # XPath name
    if counter > 1:
        xpath = node.name + '[%d]' % counter
    else:
        xpath = node.name

    return xpath


def ExtractXPath(element, use_id=True):
    # Check that element is a tag node
    if type(element) != bs4.element.Tag:
        raise ExtractXPathError(
            '%s is not a supported data type. '
            'Only tag nodes from the tag tree are accepted.'
            % type(element)
        )

    # Starting node
    # Check id first
    if use_id and element.get('id') is not None:
        return '//*/' + element.name + '[@id="' + element.get('id') + '"]'

    xpath = check_previous_tags(element)

    # Parent Nodes
    for parent in element.parents:
        # End of XPath - exclude from string
        if parent.name == '[document]':
            break

        # Check id first
        if use_id and parent.get('id') is not None:
            return '//*/' + parent.name + '[@id="' + parent.get('id') + '"]/' + xpath  # noqa

        xpath = check_previous_tags(parent) + '/' + xpath

    xpath = '/' + xpath
    return xpath

# xp1_wildcard adds wildcard functionality to XPath 1.0
# strings using the limited function set supported by the 1.0
# implementation.
#
# xp1_lowercase likewise adds lowercase functionality
#
# Hopefully you never need these...


def xp1_lowercase(string):
    return 'translate(' + string + ", 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"  # noqa

# Converts a string with a wildcard in it to an XPath 1.0
# compatible string *** ONLY SUPPORTS 1 WILDCARD ***
# string: string w/ wildcard that you are searching for
# attr: tag attribute you are searching for (e.g. 'text()' or '@id' or ...)


def xp1_wildcard(attr, string, normalize=True):
    parts = string.split('*')

    if normalize:
        attr = 'normalize-space(' + attr + ')'

    if len(parts) != 2:
        print("ERROR: This function is meant to support 1 wildcard")
        return '[' + attr + '=' + string + ']'
    else:
        pt1 = ''
        pt2 = ''

        if parts[0] != '':
            pt1 = 'starts-with(' + attr + ", '" + parts[0] + "')"
        if parts[1] != '':
            pt2 = 'contains(substring(' + attr + \
                  ', string-length(' + attr + ')-' + \
                  str(len(parts[1]) - 1) + "), '" + parts[1] + "')"

        if pt1 == '' and pt2 != '':
            return '[' + pt2 + ']'
        elif pt1 != '' and pt2 == '':
            return '[' + pt1 + ']'
        elif pt1 != '' and pt2 != '':
            return ('[' + pt1 + ' and ' + pt2 + ']')
        else:
            print("ERROR: The string is empty")
            return '[' + attr + '=' + string + ']'


def main():
    # Output some sample XPaths
    print("--- Sample XPaths ---")
    from urllib.request import urlopen
    import re
    from random import choice
    rsp = urlopen('http://www.reddit.com/')
    if rsp.getcode() == 200:
        soup = bs(rsp.read(), 'lxml')
        elements = soup.findAll(text=re.compile('[A-Za-z0-9]{10,}'))
        for i in range(0, 5):
            element = choice(elements).parent
            print("HTML")
            print(element)
            print("XPath")
            print(ExtractXPath(element))
            print("**************")


if __name__ == '__main__':
    main()
