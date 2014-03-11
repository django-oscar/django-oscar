# -*- coding: utf-8 -*-
import codecs
import csv
import six
from warnings import warn
from six.moves import cStringIO


# These classes are copied from http://docs.python.org/2/library/csv.html


class CsvUnicodeWriter(object):
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def cast_to_bytes(self, obj):
        if isinstance(obj, six.text_type):
            return obj.encode('utf-8')
        elif isinstance(obj, six.binary_type):
            return obj
        elif hasattr(obj, '__unicode__'):
            return six.text_type(obj).encode('utf-8')
        elif hasattr(obj, '__str__'):
            return str(obj)
        else:
            raise TypeError('Expecting unicode, str, or object castable'
                            ' to unicode or string, got: %r' % type(obj))

    def cast_to_str(self, obj):
        warn('cast_to_str deprecated, please use cast_to_bytes instead')
        return self.cast_to_bytes(obj)

    def writerow(self, row):
        self.writer.writerow([self.cast_to_bytes(s) for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class UTF8Recoder(object):
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """

    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")


class CsvUnicodeReader(object):
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwargs):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwargs)

    def next(self):
        row = six.advance_iterator(self.reader)
        return [six.text_type(s).encode("utf-8") for s in row]

    def __iter__(self):
        return self
