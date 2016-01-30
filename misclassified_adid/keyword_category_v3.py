#!/usr/bin/env python
import sys, os, re
import time
import fileinput
import datetime
from datetime import date
from datetime import timedelta
from optparse import OptionParser
import MySQLdb
from MySQLdb import cursors
import subprocess
import math
import get_weight as A
source_id = sys.argv[2]
date = time.strftime("%Y-%m-%d", time.localtime())
if source_id == '2':
    source = 'snapshot_keyword_group_links'
else:
    source = 'snapshot_keyword_group_links_adcenter'

weights = [0, 0, 0]

#add department name to items in daily_revenue and sort the departments by their historical conversion records for each adid
hql1 = "\"DROP TABLE if exists yupeng_tmpa_2%s; CREATE TABLE yupeng_tmpa_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select adid, upper(wm_dept_name) as wm_dept_name, count(upper(wm_dept_name)) as count from daily_revenue inner join wmt_dotcom_items on item_id = catalog_item_id where wm_dept_name is not NULL and wm_dept_name <> '' and upper(wm_dept_name) <> 'UNASSIGNED' and transaction_type = 'auth' and customer_id_p = 1 and channel_id in (0, 1, 20, 21) group by adid, upper(wm_dept_name);\"" %(source_id,source_id)
#retain the top 2 departments for each ad
hql2 = "\"DROP TABLE if exists yupeng_tmpb_2%s;create table yupeng_tmpb_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select * from (select *, ROW_NUMBER() OVER (DISTRIBUTE BY adid SORT BY count DESC) rn from yupeng_tmpa_2%s) tmp where rn <= 2;\"" %(source_id,source_id, source_id)

#find the original category/department for each adid
hql3 = "\"DROP TABLE if exists yupeng_tmpc_2%s;CREATE TABLE yupeng_tmpc_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select A.adid, (CASE WHEN B.wm_dept_name is not NULL and B.wm_dept_name <> '' and upper(B.wm_dept_name) <> 'UNASSIGNED' Then upper(B.wm_dept_name) ELSE NULL END) as wm_dept_name from adid_item_mapping_30d A left join wmt_dotcom_items B on A.catalog_item_id is NOT NULL and A.catalog_item_id >= 0 and A.catalog_item_id = B.catalog_item_id where A.adid is not NULL and A.adid >= 0;\"" %(source_id,source_id)
#add the keyword for each adid
hql4 = "\"DROP TABLE if exists yupeng_tmpd_2%s;CREATE TABLE yupeng_tmpd_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select A.adid, A.wm_dept_name, (CASE WHEN B.keyword is NULL or B.keyword = '' Then NULL ELSE B.keyword END) as keyword, B.match_type, (CASE WHEN B.adid is NULL or B.adid < 0 THEN 1 ELSE 0 END) as is_pla from yupeng_tmpc_2%s A left join(select adid, upper(keyword) as keyword, upper(match_type) as match_type from %s union all select adid, upper(keyword) as keyword, upper(match_type) as match_type from daily_kgl_traffic_revenue where is_pla = 0 and source_id = 2 and customer_id_p = 1) B on A.adid = B.adid where B.match_type <> '' group by A.adid, B.adid, A.wm_dept_name, B.keyword, B.match_type;\""  %(source_id,source_id,source_id, source)

#classify adids according and mark their status(misclassified, correct, unknown)
hql5 = "\"DROP TABLE if exists yupeng_tmpe_2%s;CREATE TABLE yupeng_tmpe_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select A.adid, (CASE WHEN A.is_pla = 1 THEN -12 WHEN A.wm_dept_name is NULL THEN -11 ELSE ceil(SUM(CASE WHEN A.wm_dept_name = B.wm_dept_name THEN 2 * B.rn WHEN B.wm_dept_name is NULL THEN -4 ELSE -1 END) / 2) END) AS status, A.wm_dept_name, max(struct(rn, B.wm_dept_name)).col2 as min_category, max(struct(rn, B.count)).col2 as min_confidence, min(struct(rn, B.wm_dept_name)).col2 as max_category, min(struct(rn, B.count)).col2 as max_confidence, A.keyword, A.match_type from yupeng_tmpd_2%s A left join yupeng_tmpb_2%s B on A.adid = B.adid group by A.adid, A.wm_dept_name, A.is_pla, A.keyword, A.match_type;\"" %(source_id,source_id, source_id, source_id)

#For adid without conversion record, refer to ads, ones with conversion records and same keyword. 
#If the match_type if this adid is 'exact', just consider ad whose match_type is 'broad' or 'phrase';
#If the match_type if this adid is 'broad', just consider ad whose match_type is 'exact' or 'phrase';
#If the match_type if this adid is 'phrase', just consider ad whose match_type is 'exact' or 'broad';
#For different match_types, the # of each department should be mulitiplied by different weights, and here, weights are obtained from conversion record as well  
hql6 = "\"DROP TABLE if exists yupeng_mid_2%s;CREATE TABLE yupeng_mid_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select A.keyword, A.match_type, B.wm_dept_name, (case A.match_type when 'BROAD' then %s * B.count when 'PHRASE' then %s * B.count else 0 end) as exact_case, (case A.match_type when 'EXACT' then %s * B.count when 'PHRASE' then %s * B.count else 0 end) as broad_case, (case A.match_type when 'EXACT' then %s * B.count when 'BROAD' then %s * B.count else 0 end) as phrase_case from (select adid, upper(keyword) as keyword, upper(match_type) as match_type from daily_kgl_traffic_revenue where customer_id_p = 1 and source_id = 2 and is_pla = 0 union all select adid, upper(keyword) as keyword, upper(match_type) as match_type from %s) A inner join yupeng_tmpb_2%s B on A.adid is not null and A.adid >= 0 and A.adid = B.adid where A.match_type <> '' group by A.keyword, A.match_type, B.wm_dept_name, B.count;\""  %(source_id,source_id, str(weights[0]), str(1- weights[0]), str(weights[1]), str(1 - weights[1]), str(weights[2]), str(1 - weights[2]), source, source_id)
hql7 = "\"DROP TABLE if exists yupeng_keyword_2%s;CREATE TABLE yupeng_keyword_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select keyword, wm_dept_name, sum(exact_case) as exact_case_sum, sum(broad_case) as broad_case_sum, sum(phrase_case) as phrase_case_sum from yupeng_mid_2%s group by keyword, wm_dept_name\"" %(source_id, source_id, source_id)

hql8 = "\"DROP TABLE if exists yupeng_keyword_rn_exact_2%s;CREATE TABLE yupeng_keyword_rn_exact_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select * from (select keyword, wm_dept_name, ('EXACT') as type, exact_case_sum as sum, ROW_NUMBER() OVER(DISTRIBUTE BY keyword SORT BY exact_case_sum DESC) as rn from yupeng_keyword_2%s where keyword is not null and keyword <> '' and (keyword like '%sWALMART%sSITE%s') = FALSE) tmp where rn <= 2;\"" %(source_id,source_id, source_id, '%', '%', '%')
hql9 = "\"DROP TABLE if exists yupeng_keyword_rn_broad_2%s;CREATE TABLE yupeng_keyword_rn_broad_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select * from (select keyword, wm_dept_name, ('BROAD') as type, broad_case_sum as sum, ROW_NUMBER() OVER(DISTRIBUTE BY keyword SORT BY broad_case_sum DESC) as rn from yupeng_keyword_2%s where keyword is not null and keyword <> '' and (keyword like '%sWALMART%sSITE%s') = FALSE) tmp where rn <= 2;\"" %(source_id,source_id, source_id, '%', '%', '%')

hql10 = "\"DROP TABLE if exists yupeng_keyword_rn_phrase_2%s;CREATE TABLE yupeng_keyword_rn_phrase_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select * from (select keyword, wm_dept_name, ('PHRASE') as type, phrase_case_sum as sum, ROW_NUMBER() OVER(DISTRIBUTE BY keyword SORT BY phrase_case_sum DESC) as rn from yupeng_keyword_2%s where keyword is not null and keyword <> '' and (keyword like '%sWALMART%sSITE%s') = FALSE) tmp where rn <= 2;\"" %(source_id,source_id, source_id, '%', '%', '%')

hql11 = "\"DROP TABLE if exists yupeng_keyword_rn_2%s; CREATE TABLE yupeng_keyword_rn_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select keyword, type, wm_dept_name, sum, rn from (select * from yupeng_keyword_rn_exact_2%s union all select * from yupeng_keyword_rn_broad_2%s union all select * from yupeng_keyword_rn_phrase_2%s) tmp group by keyword, type, wm_dept_name, sum, rn\"" %(source_id, source_id, source_id, source_id, source_id)
#after improvement
hql12 = "\"DROP TABLE if exists yupeng_final_2%s; CREATE TABLE yupeng_final_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n'AS select B.adid, B.keyword, (CASE WHEN B.status > -2 or B.status < -10 THEN B.status WHEN B.keyword is NULL or A.keyword is NULL or A.keyword = '' THEN -2 ELSE ceil(sum(CASE WHEN B.wm_dept_name = A.wm_dept_name THEN 2 * A.rn ELSE -1 END)/2) END) as new_status, B.wm_dept_name, (CASE WHEN B.status > -2 THEN B.min_category WHEN B.status < -10 or B.keyword is NULL THEN NULL ELSE max(struct(A.rn, A.wm_dept_name)).col2 END) as min_category, (CASE WHEN B.status > -2 THEN B.min_confidence WHEN B.keyword is NULL or B.status < -10 THEN NULL ELSE max(struct(A.rn, A.sum)).col2 END) as min_confidence, (CASE WHEN B.status > -2 THEN B.max_category WHEN B.status < -10 or B.keyword is NULL THEN NULL ELSE min(struct(A.rn, A.wm_dept_name)).col2 END) as max_category, (CASE WHEN B.status > -2 THEN B.max_confidence WHEN B.keyword is NULL or B.status < -10 THEN NULL ELSE min(struct(A.rn, A.sum)).col2 END) as max_confidence from yupeng_keyword_rn_2%s A right join yupeng_tmpe_2%s B on B.keyword = A.keyword where B.match_type = A.type or A.type is NULL group by B.adid, B.status, B.wm_dept_name, B.keyword, B.min_category, B.min_confidence, B.max_category, B.max_confidence, A.keyword;\"" %(source_id,source_id, source_id, source_id)

#hql9 = "\"CREATE TABLE yupeng_test ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select A.adid, A.new_status, B.wm_dept_id as wm_dept_id_new, A.wm_dept_id as wm_dept_id_old, A.status from yupeng_final A left join yupeng_keyword_rn B on B.keyword = A.keyword where A.new_status = 0 or A.status <> 0 or B.rn = 1 group by A.adid, A.new_status, A.wm_dept_id, A.status, B.wm_dept_id;\""

#update#hql10 = "\"DROP TABLE if exists yupeng_update;CREATE TABLE yupeng_update ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select tmp.adid, tmp.new_status, (CASE WHEN tmp.new_status >= 0 THEN tmp.wm_dept_id_old WHEN tmp.new_status < 0 and tmp.status = 0 THEN tmp.wm_dept_id_new WHEN tmp.status < 0 THEN C.wm_dept_id END) as new_wm_dept_id from (select A.adid, A.new_status, B.wm_dept_id as wm_dept_id_new, A.wm_dept_id as wm_dept_id_old, A.status from yupeng_final A left join yupeng_keyword_rn B on B.keyword = A.keyword where A.new_status = 0 or (A.status <> 0 and (B.rn is null or B.rn = 1)) or B.rn = 1 group by A.adid, A.new_status, A.wm_dept_id, A.status, B.wm_dept_id) tmp left join yupeng_tmpb C on tmp.adid = C.adid where C.rn is null or C.rn <= 0 or C.rn = 1 group by tmp.adid, tmp.new_status, tmp.status, tmp.wm_dept_id_old, tmp.wm_dept_id_new, C.wm_dept_id;\""

#hql13 = "\"DROP TABLE if exists yupeng_add_2%s;CREATE TABLE yupeng_add_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select A.adid, A.keyword, A.new_status, A.wm_dept_name, A.min_category, A.min_confidence, A.max_category, A.max_confidence, sum(case when B.date_string is null THEN 0 WHEN datediff('%s', B.date_string) <= 90 and B.customer_id_p = 1 and B.source_id = 2 and B.is_pla = 0 THEN B.orders ELSE 0 END) as orders_3m from yupeng_final_2%s A left join daily_kgl_traffic_revenue B on A.adid = B.adid group by A.adid, A.keyword, A.new_status, A.wm_dept_name, A.min_category, A.min_confidence, A.max_category, A.max_confidence\"" %(source_id,source_id,date, source_id)

#count misclassified ads, correctly classified ads, unknown ads and so on respectively
hql13 = "\"select sum(case when new_status >= 1 THEN 1 ELSE 0 END) as num_correct, sum(case when new_status = -11 THEN 1 ELSE 0 END) as num_no_id, sum(case when new_status = -12 THEN 1 ELSE 0 END) as num_pla, sum(case when new_status = 0 or new_status = -1 THEN 1 ELSE 0 END) as num_wrong, sum(case when new_status <= -2 and new_status >= -10 THEN 1 ELSE 0 END) as num_unknown from yupeng_final_2%s\" > result_2%s.txt" %(source_id, source_id)
#make a summary of accuracy of each department 
r1 = "\"select wm_dept_name, sum(case when new_status > 0 then 1 else 0 end) /sum(case when new_status >= -1 then 1 else 0 end) as accuracy, count(*) as cnt from yupeng_final_2%s where new_status >= -10 group by wm_dept_name order by cnt desc;\" > summary_department_2%s.txt" %(source_id, source_id)
#make a summary of misclassified ads with high clicks within one month 
r2 = "\"select adid, wm_dept_name, min_category, min_confidence, max_category, max_confidence from yupeng_final_2%s where new_status in (-1, 0)\"> mis_categorized_adids_2%s" %(source_id, source_id)

get_high_clicks = "\"select A.adid, A.keyword, A.wm_dept_name, A.min_category, A.min_confidence, A.max_category, A.max_confidence, sum(B.clicks) as click_1m, sum(B.adspend) as spend_1m, sum(B.revenue) as revenue_1m from yupeng_final_2%s A inner join daily_kgl_traffic_revenue B on A.adid = B.adid where A.new_status in (-1, 0) and datediff('%s', B.date_string) <= 31 group by A.adid, A.keyword, A.wm_dept_name, A.min_category, A.min_confidence, A.max_category, A.max_confidence sort by click_1m DESC, spend_1m DESC, revenue_1m DESC\" > mis_highclick_adids_2%s" %(source_id, date, source_id)
def die_on_failure(exit_status):
    if(exit_status != 0):
        print 'Error during execution. Terminating process now'
        time.sleep(1200)
        exit(1)

def run(command):

    print "Running command: %s" % (command)
    proc = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    die_on_failure(proc.returncode)
    return out
#After running hql1, weights infomation should be updated and saved, otherwise, weights info should be read first
seq = sys.argv[1].split(",")
hqls = [hql1, hql2, hql3, hql4, hql5, hql6, hql7, hql8, hql9, hql10, hql11, hql12, hql13, r1, r2, get_high_clicks]
for i in range(0, len(seq)):
    if int(seq[i]) == 1:
        cmd_d = "hive -e" +  hqls[int(seq[i]) - 1]
        run(cmd_d)
        print 'x'
        A.get_info()
    else:
        f = open("weight_info")
        cur = 0
        for line in f.readlines():
            weights[cur] = float(line.rstrip('\n'))
            cur += 1
        f.close()
        cmd_d = "hive -e" +  hqls[int(seq[i]) - 1]
        run(cmd_d)
                                                                                                                     97,1-8        87%

