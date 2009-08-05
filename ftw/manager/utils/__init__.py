
import os
import subprocess
import output

def runcmd(cmd, log=True, respond=False):
    if log:
        print '  %', output.ColorString(cmd, output.YELLOW)
    if respond:
        p = os.popen(cmd, 'r')
        l = p.readlines()
        p.close()
        return l
    else:
        os.system(cmd)

def runcmd_with_exitcode(cmd, log=True):
    if log:
        print '  %', output.ColorString(cmd, output.YELLOW)
    p = subprocess.Popen(cmd.split(' '), cwd=os.path.abspath('.'), stderr=None)
    return p.wait()

