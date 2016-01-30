chmod 775 ./preprocess1.py
./preprocess1.py ../data/danielle_adid_erpc_trn.csv ../data/data.txt ../data/dict.txt
chmod 775 ./preprocess.py
./preprocess.py ../data/danielle_adid_erpc_trn.csv ../data/data.txt ../data/dict.txt ../impor_feature.txt
chmod 775 ./mknfold.py
./mknfold.py ../data/data.txt 3 5

chmod 775 ./rpc_prediction_feature_importance.R
./rpc_prediction_feature_importance.R
#Here you need select features manually. 
chmod 775 ./rpc_prediction_run.R
./rpc_prediction_run.R