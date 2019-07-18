import os, sys, settings, inspect

# in files to be traced, add:
#
#import pid_trace
#
# to top of file and then call:
#
# pid_trace.pid_trace()  to add a trace line to the file
# or
# delete_pid_trace_file()  to delete the trace file


def pid_trace():

    strpid = str(os.getpid())
    tracefilepath = os.path.join(settings.TEMP_FILES_DIR,'pid_' + strpid + '.trace')

    previous_frame = inspect.currentframe().f_back
    (filename, line_number, function_name, lines, index) = inspect.getframeinfo(previous_frame)

    f = open(tracefilepath, 'a')
    f.write(os.path.basename(filename) + ' line ' + str(line_number) + '\n')
    f.close()


def delete_pid_trace_file():
    strpid = str(os.getpid())
    tracefilepath = os.path.join(settings.TEMP_FILES_DIR,'pid_' + strpid + '.trace')
    if os.path.exists(tracefilepath) and os.path.isfile(tracefilepath):
        os.remove(tracefilepath)
