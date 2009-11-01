#!/usr/bin/env python
# -*- coding: utf-8 -*-

#$HeadURL$
#$LastChangedDate$
#$LastChangedRevision$

# See LICENSE.txt for licensing terms

'''
Copyright (c) 2009,  Patrick Maupin, Austin, Texas

A wrapper around subprocess that performs two functions:

 1) Adds non-blocking I/O
 2) Adds process killability and timeouts

Currently only works under Linux.

'''

import subprocess
import select
import os
import time
import textwrap
from signal import SIGTERM, SIGKILL

class BaseExec(object):
    ''' BaseExec is designed to be subclassed.
        It wraps subprocess.Popen, and adds the
        ability to kill a process and to manage
        timeouts.  By default, it uses pipes for
        the new process, but doesn't do anything
        with them.
    '''
    defaults = dict(
                bufsize=0,
                executable=None,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=None,   # Callable object in child process
                close_fds=False,   
                shell=False,
                cwd=None,
                env=None,
                universal_newlines=False,
                startupinfo=None,
                creationflags=0,
                timeout=500.0,    # Time in seconds before termination
                killdelay=20.0,   # Time in seconds after termination before kill
    )

    def before_init(self, keywords):
        # Replace this in subclass to do more setup
        pass

    def after_init(self):
        # Replace this in subclass to execute code after
        # process creation
        pass

    def __init__(self, *args, **kw):

        # Allow flexible args handling.
        if len(args) < 2:
            try:
                args[0] + ''
            except TypeError:
                args = args[0]
            else:
                args = args[0].split()
        self.args = args

        # Handle defaults
        keywords = self.defaults.copy()
        keywords.update(kw)

        # Get our timeout information, and call
        # subclass to get other parameters
        self.timeout = keywords.pop('timeout') + time.time()
        self.killdelay = keywords.pop('killdelay')
        self.before_init(keywords)

        # Start the process and let subclass execute
        proc = subprocess.Popen(args, **keywords)
        self.proc = proc
        self.after_init()

    def kill(self, force=False):
        action = force and SIGKILL or SIGTERM
        os.kill(self.proc.pid, action)
        return action

    def checktimeout(self):
        # Poll to decide if subprocess needs to be killed
        now = time.time()
        if now < self.timeout:
            return 0

        killdelay, self.killdelay = self.killdelay, 0
        self.timeout = now + killdelay
        return self.kill(not killdelay)


class PipeReader(object):
    ''' PipeReader is an iterator class designed to read from
        the next ready pipe.

        It can handle as many pipes at a time as desired,
        and each call to next() will yield one of the following:

                pipe, data   -- After reading data from pipe
                pipe, None   -- When pipe is closing
                None, None   -- On timeout if no data

        It raises StopIteration if no pipes are still open.

        A logical extension would be to handle output pipes as well,
        such as the subprocess's stdin, but the initial version is
        input pipes only (the subprocess's stdout and stderr).
    '''
    TIMEOUT = 1.0     # Poll interval in seconds
    BUFSIZE = 100000
    def __init__(self, *pipes, **kw):
        self.timeout = kw.pop('timeout', self.TIMEOUT)
        self.bufsize = kw.pop('bufsize', self.BUFSIZE)
        self.by_pipenum = {}  # Dictionary of read functions
        self.ready = []       # List of ready pipes
        assert not kw, kw     # Check for mispelings :)
        for pipe in pipes:
            self.addpipe(pipe)

    def addpipe(self, pipe):
        pipenum = pipe.fileno()
        bufsize = self.bufsize
        by_pipenum = self.by_pipenum

        def getdata():
            chunk = os.read(pipenum, bufsize)
            if chunk:
                return pipe, chunk
            else:
                # Here, we're done.  Remove ourselves from
                # the dictionary and return None as a notification
                del by_pipenum[pipenum]
                return pipe, None

        assert by_pipenum.setdefault(pipenum, getdata) is getdata

    def __iter__(self):
        return self

    def next(self):
        ready = self.ready
        if not ready:
            allpipes = list(self.by_pipenum)
            if not allpipes:
                raise StopIteration
            ready[:] = select.select(allpipes,[],[],self.timeout)[0]
            if not ready:
                return None, None   # Allow code to execute after timeout
        return self.by_pipenum[ready.pop()]()


class LineSplitter(object):
    ''' LineSplitter takes arbitrary string
        data and splits it into text lines.
        It manages the case where a single
        line of data returned from a pipe is
        split across multiple reads.
    '''
    def __init__(self, prefix):
        self.prefix = prefix
        self.leftovers = ''
        self.lines = []

    def __call__(self, chunk):
        if not chunk:
            if self.leftovers:
                chunk = '\n'
            else:
                return self
        chunk = chunk.replace('\r\n', '\n').replace('\r', '\n')
        chunk = self.leftovers + chunk
        newlines = chunk.split('\n')
        self.leftovers = newlines.pop()
        oldlines = self.lines
        oldlines.reverse()
        oldlines.extend(newlines)
        oldlines.reverse()
        return self

    def __iter__(self):
        return self
    def next(self):
        try:
            return self.prefix, self.lines.pop()
        except IndexError:
            raise StopIteration


class TextOutExec(BaseExec):
    ''' TextOutExec is used for when an executed subprocess's
        stdout and stderr are line-oriented text output.
        This class is its own iterator.  Each line from
        the subprocess is yielded from here, with a prefix:

        '  ' -- line written by subprocess to stdout
        '* ' -- line written by subprocess to stderr
        '** ' -- line represents subprocess exit code

        NB:  Current implementation is probably not that secure,
             in that it assumes that once the pipes are closed,
             the process should be terminating itself shortly.
             If this proves to be a problem in real life, we
             can add timeout checking to the "wait for things
             to finish up" logic.
    '''
    defaults = dict(
                pollinterval=1.0,
                readbufsize=100000,
    )
    defaults.update(BaseExec.defaults)

    def before_init(self, keywords):
        self.pollinterval = keywords.pop('pollinterval')
        self.bufsize = keywords.pop('readbufsize')

    def after_init(self):
        proc = self.proc
        self.pipes = PipeReader(proc.stdout, proc.stderr,
                      timeout=self.pollinterval, bufsize=self.bufsize)
        self.pipedir = {proc.stdout : LineSplitter(' '),
                        proc.stderr : LineSplitter('*')}
        self.lines = []
        self.finished = False

    def __iter__(self):
        return self

    def next(self):
        lines = self.lines
        while not lines:
            self.checktimeout()
            for pipe, data in self.pipes:
                if pipe is not None:
                    lines.extend(self.pipedir[pipe](data))
                    lines.reverse()
                break
            else:
                if self.finished:
                    raise StopIteration
                else:
                    self.finished = True
                    lines.append(('**', str(self.proc.wait())))
        return '%s %s' % lines.pop()

def elapsedtime(when=time.time()):
    mins, secs = divmod(round(time.time() - when, 1), 60)
    hrs, mins = divmod(mins, 60)
    hrs = hrs and ('%02d:' % int(round(hrs))) or ''
    mins = mins and ('%02d:' % int(round(mins))) or ''
    secs = '%04.1f' % secs
    units = hrs and 'hours' or mins and 'minutes' or 'seconds'
    return '%s%s%s %s' % (hrs, mins, secs, units)

def default_logger(resultlist, data=None, data2=None):
    if data is not None:
        resultlist.append(data)
    if data2 is None:
        data2 = data
    print data2

def textexec(*arg, **kw):
    ''' Exec a subprocess, print lines, and also return
        them to caller
    '''
    logger = kw.pop('logger', default_logger)

    formatcmd = textwrap.TextWrapper(initial_indent='        ',
                                    subsequent_indent='        ',
                                    break_long_words=False).fill

    subproc = TextOutExec(*arg, **kw)
    args = subproc.args
    procname = args[0]
    starttime = time.time()
    result = []
    logger(result,
        'Process "%s" started on %s\n\n%s\n\n' % (
         procname, time.asctime(), formatcmd(' '.join(args))))
    for line in subproc:
        if not line.startswith('**'):
            logger(result, line)
            continue
        errcode = int(line.split()[-1])
        status = errcode and 'FAIL' or 'PASS'
        logger(result,
            '\nProgram %s exit code: %s (%d)   elapsed time: %s\n' %
            (procname, status, errcode, elapsedtime(starttime)))
        logger(result, None,
            'Cumulative execution time is %s\n' % elapsedtime())
    return errcode, result

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        print "Starting subprocess"
        sys.stdout.flush()
        for i in range(10):
            time.sleep(0.2)
            print "This is line", i
            sys.stdout.flush()
        print >> sys.stderr, "This is an error message"
        print "Ending subprocess"
        if sys.argv[1] == 'die':
            raise SystemExit('Deliberately croaking')
    else:
        print "Calling myself"
        textexec(__file__, 'subprocess')
        print "Calling myself with kill time"
        textexec(__file__, 'subprocess', timeout=0.8)
        print "Calling myself with forced error exit"
        textexec(__file__, 'die')
