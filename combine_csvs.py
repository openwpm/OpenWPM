import sys
import argparse
import csv


def get_dataset(f):
    return set(map(tuple, csv.reader(f)))


def main(f1, f2, outfile, sorting_column):
    f1 
    set1 = get_dataset(f1)
    set2 = get_dataset(f2)
    # print(set1)
    different = set1 ^ set2

    output = csv.writer(outfile)

    for row in sorted(different, key=lambda x: x[sorting_column], reverse=True):
        output.writerow(row)
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('infile', nargs=2, type=argparse.FileType('r'))
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('-sc', '--sorting-column', nargs='?', type=int, default=0)

    args = parser.parse_args()

    main(*args.infile, args.outfile, args.sorting_column)