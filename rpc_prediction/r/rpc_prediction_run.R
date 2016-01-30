#!/usr/bin/env Rscript
require(xgboost)
require(methods)
require(data.table)
require(magrittr)
library(caret)
load("myfile")

#feature set1:
c1 = c(1:25)
#feature set2: 
c2 = c(1,2,3,4,5,6,8,9,10,11,12,14,15,16,17,18,19,20,23,25)
#feature set3: 
c3 = c(1,2,3,4,5,6,8,9,11,15,18,20,23)
c3 <- list(c1 = c1, c2 = c2, c3 = c3)
#try these sets using CV, have a comparsion of the mean RMSE and test it on the real test set. Finally, do experiments using random forest instead.  
df = c()
for(i in 1:3){
dtrain <- xgb.DMatrix(data = train_data[,c3[[i]]], label = train_label, weight = train_weight, missing = NA)
best_score = Inf
best_param = list(eta = -1, max_depth = -1, nrounds = -1, subsample = -1)
for(max_depth in seq(4, 6, 1)){
	for(eta in seq(0.05, 0.2, 0.03)){
		for(subsample in seq(0.80, 0.95, 0.05)){
		    param <- list(max_depth = max_depth, eta = eta, silent = 1, gamma = 15, subsample = subsample, colsample_bytree = 1)
			result <- xgb.cv(param, data = dtrain, nthread = 16, nrounds = 150, nfold = 5, verbose = 0, objective = 'reg:linear', eval_metric = 'rmse', early.stop.round = 20)
			if(best_score > result$score){
				best_score = result$score
				best_param$eta <- eta
				best_param$max_depth <- max_depth
				best_param$nrounds <- result$ind
				best_param$subsample <- subsample 
			}
		df = rbind(df, c(max_depth, eta, subsample, result$score, result$ind))
		cat("max_depth :", max_depth, "eta :", eta, "subsample :", subsample, "best score :", result$score, "best index :", result$ind, "\n")
		}
	}
}

cat(best_score, " ", best_param$eta, " ", best_param$subsample," ", best_param$max_depth, " ", best_param$nrounds,"\n")
#3.173886   0.07   4   81 

#test
dtest = xgb.DMatrix(data = test_data[,c3[[i]]], label = test_label, weight = test_weight, missing = NA)
watchlist <- list(test = dtest)
param <- list(max_depth = best_param$max_depth, eta = best_param$eta, silent = 1, gamma = 15, subsampe = best_param$subsample, colsample_bytree = 1)
bst <- xgb.train(param, data = dtrain, nthread = 16, nrounds = (best_param$nrounds + 40), watchlist = watchlist, verbose = 1, objective = 'reg:linear', eval_metric = 'rmse', early.stop.round = 20)


#randomforest
for(depth in 4:6){
	bst <- xgb.train(data = dtrain, max.depth = depth, num_parallel_tree = 500, subsample = 0.5,verbose = 1, colsample_bytree = 0.5, watchlist = watchlist, nround = 1, objective = "reg:linear", eval_metric = 'rmse')
    }
}
#1 :  3.139777   0.05   0.8   6    68, test 68 : 3.225092   57 :  3.222696 rf : 3.494274, 3.485103, 3.479792
#2 ： 3.148969   0.05   0.85   6   62， test 62 :  3.234939  76 ： 3.231894  rf : 3.498655, 3.491865, 3.488223

#1: 3.147103 0.14 0.9 5 28, test 28: 3.249571   19: 3.218816    rf: 3.492900, 3.485096, 3.477423
#2: 3.145536 0.08 0.9 6 41, test 41: 3.232677   38: 3.229628    rf: 3.494091, 3.484418, 3.479666
#3: 3.150892 0.17 0.8 5 17, test 17: 3.243496   16: 3.241147    rf: 3.497428, 3.492058, 3.486412

#plot curves of results using different features
x <- c(1:72)
df.a <- df[1:72,4]
df.b <- df[73:144, 4]
df.c <- df[145:216,4]
cat("all features mean : ", mean(df.a) ,"feature set 1 mean : ", mean(df.b),  "feature set 2 mean : ", mean(df.c))
ylim = range(df.a, df.b, df.c)
plot.new()
plot.window(xlab = "different parameters", ylab = "RMSE", xlim = c(0,80), ylim = c(2.5, 4))
lines(x, df.a, lty = "11", lwd = 2, col = 'red')
lines(x, df.b, lty = "11", lwd = 2, col = 'blue')
lines(x, df.c, lty = "11", lwd = 2, col = 'yellow')
legend(50, 4, legend = c("All Features", "Feature set 1", "Feature set 2"), lty = c("11", "11", "11"), col = c("red", "blue", "yellow"))
axis(1); axis(2, las = 1); box()

#plot the best result 
pred <- predict(bst, dtest)
label = getinfo(dtest, "label")
weight = getinfo(dtest, "weight")
data <- data.frame(pred = pred, label = label, weight = weight)
tmp1 <- which(weight >= 0 & weight < 300)
tmp2 <- which(weight >= 300 & weight < 600)
tmp3 <- which(weight >= 600 & weight < 900)
tmp4 <- which(weight >= 900)
library("devtools")
install_github("ropensci/plotly")
library(plotly)
py <- plot_ly(username = "r_user_guide", key = "mw5isa4yqp")
subplot(
	plot_ly(data, x = data$label[tmp1], y = data$pred[tmp1], filename = "r-docs/pred"),
	plot_ly(data, x = data$label[tmp2], y = data$pred[tmp2]),
	plot_ly(data, x = data$label[tmp3], y = data$pred[tmp3]),
	plot_ly(data, x = data$label[tmp4], y = data$pred[tmp4]),
	margin = 0.05
)%>% layout(showlegend = FALSE)

#write results into file
write.table(data, file = '../data/result.txt', col.names = F, row.names = F)


#colnames(measure_t) <- c("1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25")
#importanceRaw <- xgb.importance(colnames(measure_t), model = bst, data = measure_t, label = measure_l)
#importanceClean <- importanceRaw[,`:=`(Cover=NULL, Frequence=NULL)]
#head(importanceClean,50)

