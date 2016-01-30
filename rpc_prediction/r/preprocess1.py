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

def preprocess1(r_path, w_path,dict_path):
        file = open(r_path)
        file.readline()
        f = open(w_path, 'w')
        w = open(w_path + ".weight", 'w')
        dict = open(dict_path, 'w')
        map_array = [{} for i in range(9)]
        fmap = {4:0, 89:1, 90:2, 91:3, 92:4, 93:5, 94:6, 95:7, 96:8}
        #fmap = {4:0, 93:1, 94:2}
        #default = {4:"broad", 90:"Home", 91:"BOOKS", 92:"GENERAL BOOKS", 93:"BOOKS GENERAL", 94:"Y", 95:"N", 96:"Generic", 97:"Wal-Mart"}
        cnt = 83
        flag = 1
        for line in file.readlines():
                record = line.rstrip('\n').split('\t')
                tmp = record[9]
                cur = -1
                if record[1] != '1':
                    continue 
                for i in range(0, len(record)):
                        if i in [1,5,7,8,9,88]:
                                continue
                        elif i == 6:
                                w.write(record[i] + '\n')
                        elif i in fmap:
                                if record[i] == "" or record[i].upper() == "NULL":
                                        continue
                                if record[i].upper() not in map_array[fmap[i]]:
                                        map_array[fmap[i]][record[i].upper()] = cnt
                                        dict_tmp = '%d:%d:%s\n'%(cnt,i, record[i].upper())
                                        cnt += 1
                                        dict.write(dict_tmp)
                                tmp += ' %d:%f'%(map_array[fmap[i]][record[i].upper()], 1) 
                        else:
                                cur += 1
                                if flag == 1:
                                    dict_tmp = '%d:%d\n'%(cur, i)
                                    dict.write(dict_tmp)
                                if record[i].upper() == "NULL" or record[i] == "":
                                        continue
                                elif float(record[i]) != 0.0:
                                        tmp += ' %d:%f'%(cur, float(record[i]))
                flag = 2
                f.write(tmp + '\n')
        f.close()
        w.close()
        file.close()
        dict.close()
        print cnt
preprocess1(sys.argv[1], sys.argv[2], sys.argv[3])
