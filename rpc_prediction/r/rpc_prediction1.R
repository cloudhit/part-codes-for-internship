require(xgboost)
require(methods)
require(data.table)
require(magrittr)
library(caret)

#load data
mtrain <- as.matrix(read.table('data/data.txt.train'))
mtrain_weight <-as.matrix(read.table('data/data.txt.train.weight'))
mtest <- as.matrix(read.table('data/data.txt.test'))
mtest_weight <-as.matrix(read.table('data/data.txt.test.weight'))


train_data <- matrix(as.numeric(mtrain[,-c(1)]), dim(mtrain[,-c(1)]))
train_label <- matrix(as.numeric(mtrain[,1]),nrow(mtrain), 1)
train_weight <- matrix(as.numeric(mtrain_weight[,1]), nrow(mtrain), 1)
test_data <- matrix(as.numeric(mtest[,-c(1)]), dim(mtest[,-c(1)]))
test_label <- matrix(as.numeric(mtest[,1]), nrow(mtest), 1)
test_weight <- matrix(as.numeric(mtest_weight[,1]), nrow(mtest), 1)

#have a try on different number of features and different parameters using cv method
best_score  = Inf
best_param = list(fea_num = -1, max_depth = -1, nrounds = -1)
for(fea_num in seq(10, 25, 2)){ 
	for(max_depth in seq(4, 8, 1)){
        trn_data <- train_data[, 1:fea_num]
        trn_label <- train_label
        trn_weight <- train_weight
        dtrain <- xgb.DMatrix(data = trn_data, label = trn_label, weight = trn_weight, missing = NA)
        set.seed(1)
        param <- list(max_depth = max_depth, eta = 0.05, silent = 1, gamma = 15, subsample = 0.95, colsample_bytree = 1)
        result <- xgb.cv(param, data = dtrain, nthread = 16, nrounds = 150, nfold = 5, verbose = 0, objective = 'reg:linear', eval_metric = 'rmse', early.stop.round = 20)
        #bst <- xgb.train(param, data = dtrain, nrounds = 150, watchlist = watchlist, verbose = , objective = 'reg:linear', eval_metric = 'rmse')
        if(best_score > result$score){
        	best_score <- result$score
        	best_param$fea_num <- fea_num
        	best_param$max_depth <- max_depth
        	best_param$nrounds <- result$ind
        }
        cat("feature num :", fea_num, "max_depth :", max_depth, "best score :", result$score, "best index :", result$ind, "\n")
        gc()
   }
}

#observe the result on test set using currect model
cat(best_score,  " ", best_param$fea_num, " ", best_param$max_depth, " ", best_param$nrounds, "\n")
#3.147636   24   5   68
dtrain <- xgb.DMatrix(data = train_data[,1:best_param$fea_num], label = train_label, weight = train_weight, missing = NA)
dtest <- xgb.DMatrix(data = test_data[,1:best_param$fea_num], label = test_label, weight = test_weight, missing = NA)
set.seed(1)
param <- list(max_depth = best_param$max_depth, eta = 0.05, silent = 1, gamma = 15, subsample = 0.95, colsample_bytree = 1)
watchlist = list(test = dtest)
bst <- xgb.train(param, data = dtrain, nthread = 16, nrounds = best_param$nrounds + 20, watchlist = watchlist, verbose = 1, objective = 'reg:linear', eval_metric = 'rmse')



#importance_matrix <- xgb.importance(model = bst)
#print(importance_matrix[,`:=`(Cover=NULL, Frequence=NULL)], 50)
#xgb.plot.importance(importance_matrix)
#x = as.matrix(head(importance_matrix, 50))
#write.table(as.numeric(x[,1]), file = 'data/impor_feature1.txt', col.names = F, row.names = F)
#pred <- predict(bst, dtest)
#label = getinfo(dtest, "label")
#weight = getinfo(dtest, "weight")
#result <- data.frame(weight = weight, label = label, pred = pred)
#result_tmp <- result[which(result$weight >= 300),]
#plot(result_tmp$label, result_tmp$pred)
#write.table(result_tmp, file = 'data/result.txt', col.names = F, row.names = F)
#77 82 51 76 3 73 4 1 64 3175 30 4637 38 47 0 83 109 6569 1510 32 


#pred1 <- predict(bst, dtrain)
#label1 = getinfo(dtrain, "label")
#weight1 = getinfo(dtrain, "weight")
#result1 <- data.frame(weight = weight1, label = label1, pred = pred1)
#result1_tmp <- result1[which(result1$weight >= 500 & result1$label != 0),]
#plot(result1_tmp$label, result1_tmp$pred)