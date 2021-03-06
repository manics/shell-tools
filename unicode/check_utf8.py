#!/usr/bin/env python
# Check whether a file contains valid UTF-8
# From http://stackoverflow.com/a/3269323

import codecs
import sys


def checkFile(filename):
    try:
        with codecs.open(filename, encoding='utf-8', errors='strict') as f:
            for line in f:
                pass
        return 0
    except IOError as e:
        sys.stderr.write('IO error: %s\n' % e)
        return 2
    except UnicodeDecodeError:
        sys.stdout.write('%s contains invalid UTF-8\n' % filename)
        return 1


if __name__ == '__main__':
    if len(sys.argv) != 2:
        p = sys.argv[0]
        sys.stderr.write('Usage: ' + p[p.rfind('/') + 1:] + ' <filename>\n')
        sys.exit(2)
    r = checkFile(sys.argv[1])
    sys.exit(r)
