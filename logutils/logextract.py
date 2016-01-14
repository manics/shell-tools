#!/usr/bin/env python
"""
Extract partial logs by timestamp
"""

from datetime import datetime, timedelta
import os
import re
import sys


datereparts = (
    '(?P<year>\d{4})[-/]?',
    '(?P<month>\d{2})[-/]?',
    '(?P<day>\d{2})',
    '[Tt\s]+(?P<hour>\d{1,2})[:]?',
    '(?P<minute>\d{2})[:]?',
    '(?P<second>\d{2})[,\.]?',
    '(?P<fracsecond>\d*)',
    )


dateunits = (
    'year', 'month', 'day', 'hour', 'minute', 'second', 'fracsecond')


def _redict_to_date(redict):
    parts = {}
    for k, v in redict.iteritems():
        parts[k] = int(v) if v else 0
    try:
        if len(redict['fracsecond']) < 4:
            # Assume milliseconds
            parts['fracsecond'] *= 1000
    except TypeError:
        pass
    return datetime(*(parts[u] for u in dateunits))


def _starts_with_date(s):
    datere = ''.join(datereparts)
    m = re.match(datere, s)
    if m:
        return _redict_to_date(m.groupdict())


def _parse_partial_date(s):
    """
    Parse a date from largest unit (year) to smallest. Any number of
    rightmost units can be omitted
    """
    optionaldatere = reduce(
        lambda a, b: '%s(%s)?' % (b, a), reversed(datereparts)) + '$'
    m = re.match(optionaldatere, s.strip())
    if not m:
        raise ValueError('Invalid datetime: %s' % s)
    return _redict_to_date(m.groupdict())


def _parse_duration(d):
    args = {'days': None, 'hours': None, 'minutes': None, 'seconds': None}
    s = d.strip()
    while s:
        m = re.match('(\d+)(\w)\s*', s)
        if m:
            n, u = m.groups()
            for k in args.iterkeys():
                if u == k[0]:
                    if args[k] is not None:
                        raise ValueError(
                            'Invalid duration (repeated unit): %s' % d)
                    args[k] = int(n)
            s = s[m.end():]
        else:
            raise ValueError('Invalid duration: %s' % d)

    for k, v in args.iteritems():
        if v is None:
            args[k] = 0
    return timedelta(**args)


def _get_range(startdt, enddt=None, duration=None):
    start = _parse_partial_date(startdt)
    if enddt:
        end = _parse_partial_date(enddt)
    elif duration:
        d = _parse_duration(duration)
        end = start + d
    else:
        end = datetime(9999, 1, 1)
    return start, end


class LogExtractor(object):

    def __init__(self, logfilename, start, end):
        self.logfile = open(logfilename, 'rU')
        self.start = start
        self.end = end
        self.bufferdate = None
        self.buffer = ''

    def __iter__(self):
        return self

    def next(self):
        d, m = self._next_message()
        while m and (d < self.start):
            d, m = self._next_message()
        if m and (d < self.end):
            return m
        raise StopIteration

    def _next_message(self):
        line = True
        while line:
            line = self.logfile.readline()
            if not line:
                logdate = self.bufferdate
                logmessage = self.buffer
                self.bufferdate = None
                self.buffer = None
                return logdate, logmessage

            linedate = _starts_with_date(line)
            if linedate:
                if self.bufferdate:
                    logdate = self.bufferdate
                    logmessage = self.buffer
                    self.bufferdate = linedate
                    self.buffer = line
                    return logdate, logmessage
                else:
                    # Start of first complete log message so discard existing
                    self.bufferdate = linedate
                    self.buffer = line
            else:
                self.buffer += line


def main(args):
    if len(args) == 3:
        start, end = _get_range(args[2])
    elif len(args) == 4:
        start, end = _get_range(args[2], duration=args[3])
    else:
        raise ValueError('Invalid arguments')
    # print 'start:%s end:%s' % (start, end)
    logextractor = LogExtractor(args[1], start, end)
    for log in iter(logextractor):
        print log
    return 0

if __name__ == '__main__':
    try:
        main(sys.argv)
    except ValueError as e:
        sys.stderr.write(e.message)
        sys.stderr.write("""
USAGE: {0} logfile.log start [duration]
    start should be an isodatetime with optional right-hand parts omitted
        e.g. "2015-01-01 01:23:34" "2015-01-01 01" "2015-01"
    duration should be comprised of units [d]ay, [h]our [m]inute, [s]econd
        e.g. "1d2h3m" "65m" "2d98s"
    e.g. {0} input.log 2015-01-02
         {0} input.log "2015-01-02 14:30" 2h
         {0} input.log "2015-01-02 14:45:52" 3m20s
""".format(os.path.basename(sys.argv[0])))
        sys.exit(1)
