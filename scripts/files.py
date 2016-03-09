#!/usr/bin/env python
#
# /proc/sys/fs/file-nr 
# contains 3 numbers: number of open files, free file handles and max open files limit
#

import os
import json
import sys

filenr_file = "/proc/sys/fs/file-nr"

if not os.path.exists(filenr_file):
    print "{} does not exists".format(filenr_file)
    sys.exit(1)

f = open(filenr_file)
line = f.read(40)  # read max 40 bytes
num_open_files, num_free_file_handles, num_max_open_files = line.split()
result = {}
result["num_open_files"] = int(num_open_files)
result["num_free_file_handles"] = int(num_free_file_handles)
result["num_max_open_files"] = int(num_max_open_files)
print json.dumps(result)
