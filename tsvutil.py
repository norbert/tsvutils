"""
Miscellaneous utilities to support some of the ``tsvutils`` scripts.
"""

from __future__ import print_function

import sys
import re
import codecs
import csv
from cStringIO import StringIO


WHITESPACE = re.compile(r'\s')


##########################################################################


def warning(s):
    pass


def cell_text_clean(text):
    s = text
    # um i can't remember what subclasses which
    if isinstance(s, str) and not isinstance(s, unicode):
        s = unicode(s, 'utf8', 'replace')
    if '\t' in s:
        warning("Clobbering embedded tab")
    if '\n' in s:
        warning("Clobbering embedded newline")
    if '\r' in s:
        warning("Clobbering embedded carriage return")
    s = s.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
    s = s.encode('utf-8')
    return s


def fix_stdio():
    sys.stdout = IOWrapper(sys.stdout)


class IOWrapper:
    # I like to press Ctrl-C; why is Python yelling at me?

    def __init__(self, fp):
        self.fp = fp

    def write(self, *args, **kwargs):
        try:
            self.fp.write(*args, **kwargs)
        except IOError as error:
            if error.errno == 32:  # broken pipe
                sys.exit(0)
            raise error


class UTF8Recoder:

    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8.
    """

    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode('utf-8')


class UnicodeReader:

    """
    A CSV reader which will iterate over lines in the CSV file `f`,
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwargs):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwargs)

    def next(self):
        row = self.reader.next()
        return [unicode(s, 'utf-8') for s in row]

    def __iter__(self):
        return self


class UnicodeWriter:

    """
    A CSV writer which will write rows to CSV file `f`,
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding='utf-8', **kwargs):
        # Redirect output to a queue
        self.queue = StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwargs)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode('utf-8') for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode('utf-8')
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
