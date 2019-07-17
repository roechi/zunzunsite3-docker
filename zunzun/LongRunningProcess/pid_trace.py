import os, sys, settings

# in files to be traced, add:
#import inspect, pid_trace
# to top of file and then call:
# pid_trace.pid_trace(__file__, inspect.currentframe().f_lineno)

def pid_trace(filepath, lineno):
    strpid = str(os.getpid())
    strppid = str(os.getppid())
    tracefilepath = os.path.join(settings.TEMP_FILES_DIR,'ppid_' + strppid + '_pid_' + strpid + '.trace')
    f = open(tracefilepath, 'a')
    f.write(os.path.basename(filepath) + ' line ' + str(lineno) + '\n')
    f.close()

def delete_pid_trace_file():
    strpid = str(os.getpid())
    strppid = str(os.getppid())
    tracefilepath = os.path.join(settings.TEMP_FILES_DIR,'ppid_' + strppid + '_pid_' + strpid + '.trace')
    if os.path.exists(tracefilepath) and os.path.isfile(tracefilepath):
        os.remove(tracefilepath)
