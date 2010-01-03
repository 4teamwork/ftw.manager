
import os
import subprocess
import output

from memoize import memoize

@memoize
def runcmd(cmd, log=True, respond=False):
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
    if log:
        print '  %', output.colorize(cmd, output.WARNING)
    p = subprocess.Popen(cmd.split(' '), cwd=os.path.abspath('.'), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    exitcode = p.wait()
    if not respond and not respond_error:
        return exitcode
    else:
        returned = [exitcode]
        if respond:
            returned.append(p.stdout.read())
        if respond_error:
            returned.append(p.stderr.read())
        return returned

