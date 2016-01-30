#!/usr/bin/python
import numpy as np
import scipy.sparse
import pickle
import xgboost as xgb

file = open('../data/danielle_adid_erpc_trn.csv')
w = open('../data/partData.csv', 'w')
cnt = 0
for line in file.readlines():
    cnt += 1
    if cnt > 1000000:
        break
    w.write(line)
file.close()
w.close()


