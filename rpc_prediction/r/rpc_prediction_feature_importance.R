#!/usr/bin/env Rscript
require(xgboost)
require(methods)
require(data.table)
require(magrittr)
library(caret)

#load data
mtrain <- as.matrix(read.table('../data/data.txt.train'))
mtrain_weight <-as.matrix(read.table('../data/data.txt.train.weight'))
mtest <- as.matrix(read.table('../data/data.txt.test'))
mtest_weight <-as.matrix(read.table('../data/data.txt.test.weight'))

train_data <- matrix(as.numeric(mtrain[,-c(1)]), dim(mtrain[,-c(1)]))
train_label <- matrix(as.numeric(mtrain[,1]),nrow(mtrain), 1)
train_weight <- matrix(as.numeric(mtrain_weight[,1]), nrow(mtrain), 1)
test_data <- matrix(as.numeric(mtest[,-c(1)]), dim(mtest[,-c(1)]))
test_label <- matrix(as.numeric(mtest[,1]), nrow(mtest), 1)
test_weight <- matrix(as.numeric(mtest_weight[,1]), nrow(mtest), 1)

portion1 = floor(nrow(train_data) * 0.8)


#run on different sets of parameters in order to have a comprehensive understanding of features
dtrain <- xgb.DMatrix(data = train_data[1:portion1,], label = train_label[1:portion1], weight = train_weight[1:portion1], missing = NA)
dtest <- xgb.DMatrix(data = train_data[(portion1+1):nrow(train_data),], label = train_label[(portion1+1):nrow(train_data)], weight = train_weight[(portion1+1):nrow(train_data)], missing = NA)
best_score = Inf
best_param = list(eta = -1, max_depth = -1, nrounds = -1, subsample = -1)
Feature = c(76, 81, 63, 50, 2, 7874, 3, 75, 7773, 79, 106, 23, 78, 37, 7312, 53, 13, 5689, 10, 1304, 29, 62, 13881, 42, 66)
gain <- data.frame(Feature)
for(max_depth in seq(4, 6, 1)){
	for(eta in seq(0.05, 0.20, 0.02)){
		for(subsample in seq(0.8, 0.95, 0.05)){
			param <- list(max_depth = max_depth, eta = eta, silent = 1, gamma = 15, subsample = subsample, colsample_bytree = 1)
			watchlist = list(test = dtest)
			bst <- xgb.train(param, data = dtrain, nthread = 16, nrounds = 150, watchlist = watchlist, verbose = 0, objective = 'reg:linear', eval_metric = 'rmse', early.stop.round = 20)
			if(best_score > bst$bestScore){
				best_score = bst$bestScore
				best_param$eta <- eta
				best_param$max_depth <- max_depth
				best_param$nrounds <- bst$bestInd 
				best_param$subsample <- subsample
			}
	    	importance <- xgb.importance(model = bst)
	    	gain <- data.frame(gain, importance[order(as.numeric(importance[[1]]), decreasing = F)][['Gain']])
			cat("max_depth :", max_depth, "eta :", eta, "subsample :", subsample, "best score :", bst$bestScore, "best index :", bst$bestInd, "\n")
		}
	}
}

cat(best_score, " ", best_param$eta, " ", best_param$subsample, " ",  best_param$max_depth, " ", best_param$nrounds,"\n")
#3.171921   0.11   0.9   4   40

train_real = xgb.DMatrix(data = train_data, label = train_label, weight = train_weight, missing = NA)
test_real = xgb.DMatrix(data = test_data, label = test_label, weight = test_weight, missing = NA)
watchlist <- list(test = test_real)
param <- list(max_depth = best_param$max_depth, eta = best_param$eta, silent = 1, gamma = 15, subsampe = best_param$subsample, colsample_bytree = 1)
bst <- xgb.train(param, data = train_real, nthread = 16, nrounds = (best_param$nrounds + 40), watchlist = watchlist, verbose = 1, objective = 'reg:linear', eval_metric = 'rmse',early.stop.round = 20 )
#best : 3.270881, 20    40 : 3.383613

#analyze features
measure_t = as.matrix(train_data[1:portion1,])
measure_l = as.matrix(train_label[1:portion1])
missing <- c()
gain_mean <- c()
sd <- c()
for(i in 1:25){
	y <- which(is.na(measure_t[,i]) == TRUE)
	missing <- append(missing, length(y) / portion1)
	gain_mean <- append(gain_mean, mean(as.numeric(gain[i, 2:97])))
	sd <- append(sd, sd(as.numeric(gain[i, 2:97])))
}
measure = data.frame(feature = gain[[1]], gain_mean = gain_mean, sd = sd, missing = missing)
write.table(measure, file = '../data/feature_info.txt', col.names = F, row.names = F)
save.image("myfile")