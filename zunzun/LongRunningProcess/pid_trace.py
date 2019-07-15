import os, sys, settings

# in files to be traced, add:
#import inspect, pid_trace
# to top of file and then call:
#pid_trace.pid_trace(__file__, inspect.currentframe().f_lineno)

def pid_trace(filnename, lineno):
    strpid = str(os.getpid())
    tracefilepath = os.path.join(settings.TEMP_FILES_DIR,'pid_' + strpid + '.trace')
    f = open(tracefilepath, 'wa')
    f.write(filename + ' line ' + str(lineno) + '\n')
    f.close()
