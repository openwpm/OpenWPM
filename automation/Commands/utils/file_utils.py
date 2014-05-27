### This is code from Gunes Acar KU Leuven ###
import re
import os
import fnmatch

from time import strftime
import distutils.dir_util as du


def create_dir(dir_path):
    """Create a dir if it doesn't exist."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path


def append_timestamp(_str):
    """Append a timestamp and return it."""
    return _str + strftime('%y%m%d_%H%M%S')


def clone_dir_with_timestap(orig_dir_path, suffix=""):
    '''
    Creates a new directory including timestamp in name
    and copies `orig_directory` into it

    :Return: the path to the directory copy.

    '''
    new_dir = create_dir(append_timestamp(orig_dir_path + suffix))
    try:
        du.copy_tree(orig_dir_path, new_dir)
    except Exception, e:
        print(str(e))
    finally:
        return new_dir


def read_file(path):
    """Read and return file content."""
    with open(path, 'rU') as f:
        content = f.read()
        f.close()
        return content


def write_to_file(file_path, data):
    """Write data to file and close."""
    f = open(file_path, 'w')
    f.write(data)
    f.close()


def append_to_file(file_path, data):
    """Write data to file and close."""
    with open(file_path, 'a') as ofile:
        ofile.write(data)


def add_symlink(linkname, src_file):
    """Create a symbolic link pointing to src_file"""
    if os.path.lexists(linkname):   # check and remove if link exists
        try:
            os.unlink(linkname)
        except:
            pass
    try:
        os.symlink(src_file, linkname)
    except:
        pass


def gen_find_files(filepat, top):
    """ http://www.dabeaz.com/generators/
    returns filenames that matches the given pattern under() a given dir
    """
    for path, _, filelist in os.walk(top):
        for name in fnmatch.filter(filelist, filepat):
            yield os.path.join(path, name)


def gen_grep_in_dir(top_dir, pattern, unix_file_pattern):
    """Grep for a pattern in files matching the file patterns in a directory.

    Then return an iterator for (match, filename) tuples found.
    Note that: unix_file_pattern is not a python regular expression

    """
    filenames = gen_find_files(unix_file_pattern, top_dir)

    for filename in filenames:
        fileobj = open(filename)
        lines = gen_cat([fileobj])

        for match in gen_grep_in_lines(pattern, lines):
            yield (filename, match.rstrip())


def gen_grep_in_file(filename, pattern):
    fileobj = open(filename)
    lines = gen_cat([fileobj])

    for match in gen_grep_in_lines(pattern, lines):
        yield (filename, match.rstrip())


def gen_cat(sources):
    """http://www.dabeaz.com/generators/
    yields items in sources, like unix cat -> pipes the items via generator
    e.g. yields lines from a list of files """
    for s in sources:
        for item in s:
            yield item


def gen_cat_file(filename):
    """yields lines in a file via a generator"""
    f = open(filename, 'rU')
    for line in f:
        yield line


def gen_open(filenames):
    """ http://www.dabeaz.com/generators
    takes a list of filenames and returns
    an iterator that traverses opened files  """

    for name in filenames:
        yield open(name)


def gen_grep_in_lines(pattern, lines):
    """http://www.dabeaz.com/generators/
    returns an iterator(generator) for lines with the regexp pattern (pat)  """
    regex = re.compile(pattern)
    for line in lines:
        if regex.search(line):
            yield line


def gen_grep_in(path, pattern, file_pattern='*'):
    """Grep a pattern in either a file or in files
    under a directory (including subdirs)

    Note that  file_pattern is a unix shell wildcard, not a regexp
    Return a generator for (match, filename) tuples

    """
    gen = ()
    if os.path.isdir(path):
        gen = gen_grep_in_dir(path, pattern, file_pattern)
    elif os.path.isfile(path):
        gen = gen_grep_in_file(path, pattern)

    for (match, fname) in gen:
        yield (match, fname)


def grep_all_in_file(filename, pat):
    """Read file and find all occurrences of regexp pattern."""
    file_content = read_file(filename)
    return re.findall(pat, file_content)


def file_occurence_vector(filename, patterns):
    """Read file, call text_occurence_vector and return it."""
    from utils.genutils import occurence_vector  # @UnresolvedImport
    text = read_file(filename)
    return occurence_vector(text, patterns)


def hash_file(filepath, algo='sha1'):
    """Return the hash value for the file content."""
    from utils.genutils import hash_text  # @UnresolvedImport
    return hash_text(read_file(filepath), algo)


def get_out_filename_from_url(url, prefix, suffix='.txt'):
    """Replace all non-word characters with -."""
    return get_base_filename_from_url(url, prefix) + suffix


def get_base_filename_from_url(url, prefix):
    """Return base filename for the url."""
    dashed = re.sub(r'[\W]', '-', url)
    return prefix + '-' + re.sub(r'-+', '-', dashed)


def gen_read_urls_from_csv_file(filename):
    """Return lines from a CSV file (e.g. Alexa Top 1M )."""
    for line in open(filename).readlines():
        yield line.split(',', 1)[-1].rstrip()
