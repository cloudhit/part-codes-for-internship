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

def preprocess(r_path, w_path):
	file = open(r_path) 
	file.readline()
	f = open(w_path, 'w')
	w = open(w_path + ".weight", 'w')
	cnt = 102
	fmap = {4:0, 90:1, 91:2, 92:3, 93:4, 94:5, 95:6, 96:7, 97:8}
	default = {4:"broad", 90:"Home", 91:"BOOKS", 92:"GENERAL BOOKS", 93:"BOOKS GENERAL", 94:"Y", 95:"N", 96:"Generic", 97:"Wal-Mart"}
	map_array = [{} for i in range(9)]
	for line in file.readlines():
		record = line.rstrip('\n').split('\t')
		tmp = ""
		tmp += record[10]
		for i in range(0, len(record)):
			if i in [5,6,8,9,10,89]:
				continue
			elif i == 7:
				w.write(record[i] + '\n')
			elif i in fmap:
				if record[i] == "" or record[i].upper() == "NULL":
					record[i] = default[i]
				if record[i].upper() not in map_array[fmap[i]]:
					map_array[fmap[i]][record[i].upper()] = cnt
					cnt += 1
				tmp += ' %d:%f'%(map_array[fmap[i]][record[i].upper()], 1)
			else:
				if record[i].upper() == "NULL" or record[i] == "":
					continue
				elif float(record[i]) != 0.0:
					tmp += ' %d:%f'%(i, float(record[i]))
		f.write(tmp + '\n')
	f.close()
	w.close()
	file.close()
preprocess(sys.argv[1], sys.argv[2])
 