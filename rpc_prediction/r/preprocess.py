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

def preprocess(r_path, w_path, dict_path, fea_path):
        file = open(r_path)
        file.readline()
        f = open(w_path, 'w')
        dict = open(dict_path)
        fea = open(fea_path)
        w = open(w_path + ".weight", 'w')
        map_array = [[] for i in range(9)]
        feature_map = {}
        fmap = {4:0, 89:1, 90:2, 91:3, 92:4, 93:5, 94:6, 95:7, 96:8}
        for line in dict.readlines():
            record = line.rstrip('\n').split(':')
            if int(record[0]) <= 82:
                feature_map[int(record[0])] = record[1]
            else:
                feature_map[int(record[0])] = record[1] + ':' + record[2]
        #print feature_map
        #num = 0
        feature = []
        const = 25
        count = const
        impro_map = {}
        for line in fea.readlines():
            if count == 0:
                break
            no = int(line.rstrip('\n'))
            if no > 82:
                context = feature_map[no].split(':')
                map_array[fmap[int(context[0])]].append(context[1])
                #print '1 %d:%d\n'%(num, no)
               # num += 1
                impro_map[context[1]] = const - count
            else:
                impro_map[feature_map[no]] = const - count
            feature.append(no)
            count -= 1
        print feature
        #fmap = {4:0, 93:1, 94:2}
        #default = {4:"broad", 90:"Home", 91:"BOOKS", 92:"GENERAL BOOKS", 93:"BOOKS GENERAL", 94:"Y", 95:"N", 96:"Generic", 97:"Wal-Mart"}
        feature_real = [int(feature_map[i]) for i in feature if i <= 82]
        feature_cate = [int(feature_map[i].split(':')[0]) for i in feature if i > 82]
        cnt = len(feature_real)
        print cnt
        flag = 1
        for line in file.readlines():
                record = line.rstrip('\n').split('\t')
                tmp = record[9]
                cache = {}
                #cur = num - 1
                if record[1] != '1':
                    continue
                for i in range(0, len(record)):
                    if i in [1,5,7,8,9,88]:
                            continue
                    elif i == 6:
                            w.write(record[i] + '\n')
                    elif i in feature_cate:
                            for text in map_array[fmap[i]]:
                                if record[i].upper() == 'NULL' or record[i].upper() == "":
                                    cache[impro_map[text]] = "NULL" 
                                    continue
                                if text == record[i].upper():
                                #tmp += ' %d:%f'%(map_array[fmap[i]][record[i].upper()], 1) 
                                    cache[impro_map[text]] = "1.0"
                                else:
                                    cache[impro_map[text]] = "0.0"
                    elif i in feature_real:
                            #cur += 1
                            #if flag == 1:
                             #   print '2 %d:%d\n'%(cur, i)
                            if record[i].upper() == "NULL" or record[i] == "":
                                    cache[impro_map[str(i)]] = "NULL"
                            else:
                                    cache[impro_map[str(i)]] = str(record[i]) 
                sorted(cache.items(), lambda x, y: cmp(x[1], y[1]))
                for key, value in cache.items():
                    tmp += (' ' + value)                                
                f.write(tmp + '\n')
                flag = 2
        f.close()
        w.close()
        file.close()
        dict.close()
        fea.close()
        print cnt
preprocess(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
