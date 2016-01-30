#!/usr/bin/env python
import sys, os, re
import time
import fileinput
import datetime
from datetime import date
from datetime import timedelta
from optparse import OptionParser
import subprocess
import math
import csv

def search(r_path, w_path):
        file = open(r_path)
        f = open(w_path, 'w')
        line = file.readline()
        record = line.rstrip('\n').split('\t')
        cur = -1
        str = ''
        for i in range(0, len(record)):
            if i in [4,5,6,7,8,9,88,89,90,91,92,93,94,95,96]:
                    continue
            else:
            	cur += 1
                tmp = '%d:%s:%d\n'%(cur, record[i], i)
                f.write(tmp)
                str += '%d:%d,'%(cur,i)
        f.close()
        file.close()
        print str
search(sys.argv[1], sys.argv[2])

