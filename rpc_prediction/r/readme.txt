Here, search.py and rpc_prediction1.R are scripts of other experiments. 
The major scripts are : mknfold.py, preprocess.py, preprocess1.py, rpc_prediction_feature_importance.R, rpc_prediction_run.R.

These files can run through run.sh.
 
The installation of R package for xgboost can refer - https://github.com/dmlc/xgboost/tree/master/R-package. Since it’s convenient for implementing and hacking codes, I download the library and build the package locally. If you do so, then just need to copy this folder to path “xgboost/R-package”, and create a folder named “data” with data set danielle_adid_erpc_trn.csv and related file impor_feature.txt in it. Later, run shell script run.sh.    