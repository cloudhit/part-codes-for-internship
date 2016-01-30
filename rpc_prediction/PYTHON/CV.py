#!/usr/bin/python
import numpy as np
import xgboost as xgb

### load data in do training
dtrain = xgb.DMatrix('../data/data.txt.train')
param = {'max_depth':10, 'eta':0.05, 'silent':1, 'objective':'reg:regression'}
num_round = 10

print ('running cross validation')
# do cross validation, this will print result out as
# [iteration]  metric_name:mean_value+std_value
# std_value is standard deviation of the metric
xgb.cv(param, dtrain, num_round, nfold=5, metrics={'error'}, seed = 0, )




