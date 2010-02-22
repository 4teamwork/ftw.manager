
import os
import subprocess
import output

from memoize import memoize

FORCE_LOG = False

@memoize
def runcmd(cmd, log=True, respond=False):
    if FORCE_LOG:
        log = True
    if log:
        print '  %', output.colorize(cmd, output.WARNING)
    if respond:
        p = os.popen(cmd, 'r')
        l = p.readlines()
        p.close()
        return l
    else:
        os.system(cmd)

@memoize
def runcmd_with_exitcode(cmd, log=True, respond=False, respond_error=False):
    if FORCE_LOG:
        log = True
    if log:
        print '  %', output.colorize(cmd, output.WARNING)
    p = subprocess.Popen(cmd.split(' '), cwd=os.path.abspath('.'), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    response, response_error = p.communicate()
    exitcode = p.poll()
    if exitcode:
        exitcode = p.wait()
    if not respond and not respond_error:
        return exitcode
    else:
        returned = [exitcode]
        if respond:
            returned.append(response)
        if respond_error:
            returned.append(response_error)
        return returned

def aggressive_decode(value, encoding='utf-8'):
    if isinstance(value, unicode):
        return value
    other_encodings = filter(lambda e:e is not encoding, [
            'utf8',
            'iso-8859-1',
            'latin1',
            ])
    encodings = [encoding] + other_encodings
    if not isinstance(value, str):
        value = str(value)
    for enc in encodings:
        try:
            return value.decode(enc)
        except UnicodeDecodeError:
            pass
    raise
