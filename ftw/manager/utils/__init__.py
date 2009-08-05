
import os
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

