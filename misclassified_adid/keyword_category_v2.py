#!/usr/bin/env python
import sys, os, re
import time
import fileinput
import datetime
from datetime import date
from datetime import timedelta
from optparse import OptionParser
#import smtplib
#from email.mime.text import MIMEText
import MySQLdb
from MySQLdb import cursors
import subprocess
import math

source_id = sys.argv[2]
date = time.strftime("%Y-%m-%d", time.localtime())
if source_id == '2':
    source = 'snapshot_keyword_group_links'
else:
    source = "snapshot_keyword_group_links_adcenter"

hql1 = "\"DROP TABLE if exists yupeng_tmpa_2%s; CREATE TABLE yupeng_tmpa_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select adid, upper(wm_dept_name) as wm_dept_name, count(upper(wm_dept_name)) as count from daily_revenue inner join wmt_dotcom_items on item_id = catalog_item_id where wm_dept_name is not NULL and wm_dept_name <> '' and upper(wm_dept_name) <> 'UNASSIGNED' and transaction_type = 'auth' and customer_id_p = 1 and channel_id in (0, 1, 20, 21) group by adid, upper(wm_dept_name);\"" %(source_id,source_id)

hql2 = "\"DROP TABLE if exists yupeng_tmpb_2%s;create table yupeng_tmpb_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select * from (select *, ROW_NUMBER() OVER (DISTRIBUTE BY adid SORT BY count DESC) rn from yupeng_tmpa_2%s) tmp where rn <= 2;\"" %(source_id,source_id, source_id)

hql3 = "\"DROP TABLE if exists yupeng_tmpc_2%s;CREATE TABLE yupeng_tmpc_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select A.adid, (CASE WHEN B.wm_dept_name is not NULL and B.wm_dept_name <> '' and upper(B.wm_dept_name) <> 'UNASSIGNED' Then upper(B.wm_dept_name) ELSE NULL END) as wm_dept_name from adid_item_mapping_30d A left join wmt_dotcom_items B on A.catalog_item_id is NOT NULL and A.catalog_item_id >= 0 and A.catalog_item_id = B.catalog_item_id where A.adid is not NULL and A.adid >= 0;\"" %(source_id,source_id)

hql4 = "\"DROP TABLE if exists yupeng_tmpd_2%s;CREATE TABLE yupeng_tmpd_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select A.adid, A.wm_dept_name, (CASE WHEN upper(B.keyword) is NULL or upper(B.keyword) = '' Then NULL ELSE upper(B.keyword) END) as keyword, (CASE upper(B.match_type) WHEN NULL THEN NULL WHEN ' ' THEN NULL WHEN 'EXACT' THEN 1 WHEN 'BROAD' THEN 0.75 ELSE 0.5 END) as confidence_score,(CASE WHEN B.adid is NULL or B.adid < 0 THEN 1 ELSE 0 END) as is_pla from yupeng_tmpc_2%s A left join(select adid, keyword, match_type from %s union all select adid, keyword, match_type from daily_kgl_traffic_revenue where is_pla = 0 and source_id = 2 and customer_id_p = 1) B on A.adid = B.adid group by A.adid, B.adid, A.wm_dept_name, upper(B.keyword), upper(B.match_type);\""  %(source_id,source_id,source_id, source)

#select * from (select adid, upper(keyword) as keyword from daily_kgl_traffic_revenue union all select adid, upper(keyword) as keyword from snapshot_keyword_group_links) tmp order by adid limit 500;
#before improvement
#status = -11:no wm_dept_id -12:is pla 0 or -1:misclassified <= -2: no match #status contains the info concerning the ranks of matching adids' category among the top 5 categories 
hql5 = "\"DROP TABLE if exists yupeng_tmpe_2%s;CREATE TABLE yupeng_tmpe_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select A.adid, (CASE WHEN A.is_pla = 1 THEN -12 WHEN A.wm_dept_name is NULL THEN -11 ELSE ceil(SUM(CASE WHEN A.wm_dept_name = B.wm_dept_name THEN 2 * B.rn WHEN B.wm_dept_name is NULL THEN -4 ELSE -1 END) / 2) END) AS status, A.wm_dept_name, max(struct(rn, B.wm_dept_name)).col2 as min_category, max(struct(rn, B.count)).col2 as min_confidence, min(struct(rn, B.wm_dept_name)).col2 as max_category, min(struct(rn, B.count)).col2 as max_confidence, A.keyword, A.confidence_score from yupeng_tmpd_2%s A left join yupeng_tmpb_2%s B on A.adid = B.adid group by A.adid, A.wm_dept_name, A.is_pla, A.keyword, A.confidence_score;\"" %(source_id,source_id, source_id, source_id)

#hql5 = "\"DROP TABLE if exists yupeng_tmpe;CREATE TABLE yupeng_tmpe ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select A.adid, A.status, A.wm_dept_id, (CASE WHEN B.keyword is NULL or B.keyword = '' Then NULL ELSE B.keyword END) as keyword from yupeng_tmpd A left join daily_kgl_traffic_revenue B on A.adid = B.adid group by A.adid, A.status, A.wm_dept_id, B.keyword;\""

hql6 = "\"DROP TABLE if exists yupeng_mid_2%s;CREATE TABLE yupeng_mid_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select A.keyword, B.wm_dept_name, sum(case upper(A.match_type) when 'EXACT' THEN B.count WHEN 'BROAD' THEN 0.75 * B.count ELSE 0.5 * B.count END) as cnt from (select adid, upper(keyword) as keyword, match_type from daily_kgl_traffic_revenue where customer_id_p = 1 and source_id = 2 and is_pla = 0 union all select adid, upper(keyword) as keyword, match_type from %s) A inner join yupeng_tmpb_2%s B on A.adid is not null and A.adid >= 0 and A.adid = B.adid group by A.keyword, B.wm_dept_name;\""  %(source_id,source_id,source, source_id)

hql7 = "\"DROP TABLE if exists yupeng_keyword_rn_2%s;CREATE TABLE yupeng_keyword_rn_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select * from (select *, ROW_NUMBER() OVER(DISTRIBUTE BY keyword SORT BY cnt DESC) as rn from yupeng_mid_2%s where keyword is not null and keyword <> '' and (upper(keyword) like '%sWALMART%sSITE%s') = FALSE) tmp where rn <= 2;\"" %(source_id,source_id, source_id, '%', '%', '%')
#after improvement
hql8 = "\"DROP TABLE if exists yupeng_final_2%s; CREATE TABLE yupeng_final_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n'AS select B.adid, B.keyword, (CASE WHEN B.status > -2 or B.status < -10 THEN B.status ELSE (CASE WHEN B.keyword is NULL THEN -2 WHEN upper(A.keyword)is not null and upper(A.keyword) <> '' THEN ceil(sum(CASE WHEN B.wm_dept_name = A.wm_dept_name THEN 2 * A.rn ELSE -1 END)/2) ELSE -2 END) END) as new_status, B.wm_dept_name, (CASE WHEN B.status > -2 THEN B.min_category WHEN B.status < -10 or B.keyword is NULL THEN NULL ELSE max(struct(A.rn, A.wm_dept_name)).col2 END) as min_category, (CASE WHEN B.status > -2 THEN B.min_confidence WHEN B.keyword is NULL or B.status < -10 THEN NULL ELSE max(struct(A.rn, A.cnt)).col2 * B.confidence_score END) as min_confidence, (CASE WHEN B.status > -2 THEN B.max_category WHEN B.status < -10 or B.keyword is NULL THEN NULL ELSE min(struct(A.rn, A.wm_dept_name)).col2 END) as max_category, (CASE WHEN B.status > -2 THEN B.max_confidence WHEN B.keyword is NULL or B.status < -10 THEN NULL ELSE min(struct(A.rn, A.cnt)).col2 * B.confidence_score END) as max_confidence from yupeng_keyword_rn_2%s A right join yupeng_tmpe_2%s B on B.keyword = upper(A.keyword) group by B.adid, B.status, B.wm_dept_name, B.keyword, B.min_category, B.min_confidence, B.max_category, B.max_confidence, B.confidence_score, upper(A.keyword);\"" %(source_id,source_id, source_id, source_id)

#hql9 = "\"CREATE TABLE yupeng_test ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select A.adid, A.new_status, B.wm_dept_id as wm_dept_id_new, A.wm_dept_id as wm_dept_id_old, A.status from yupeng_final A left join yupeng_keyword_rn B on B.keyword = A.keyword where A.new_status = 0 or A.status <> 0 or B.rn = 1 group by A.adid, A.new_status, A.wm_dept_id, A.status, B.wm_dept_id;\""

#update
#hql10 = "\"DROP TABLE if exists yupeng_update;CREATE TABLE yupeng_update ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select tmp.adid, tmp.new_status, (CASE WHEN tmp.new_status >= 0 THEN tmp.wm_dept_id_old WHEN tmp.new_status < 0 and tmp.status = 0 THEN tmp.wm_dept_id_new WHEN tmp.status < 0 THEN C.wm_dept_id END) as new_wm_dept_id from (select A.adid, A.new_status, B.wm_dept_id as wm_dept_id_new, A.wm_dept_id as wm_dept_id_old, A.status from yupeng_final A left join yupeng_keyword_rn B on B.keyword = A.keyword where A.new_status = 0 or (A.status <> 0 and (B.rn is null or B.rn = 1)) or B.rn = 1 group by A.adid, A.new_status, A.wm_dept_id, A.status, B.wm_dept_id) tmp left join yupeng_tmpb C on tmp.adid = C.adid where C.rn is null or C.rn <= 0 or C.rn = 1 group by tmp.adid, tmp.new_status, tmp.status, tmp.wm_dept_id_old, tmp.wm_dept_id_new, C.wm_dept_id;\""

hql9 = "\"DROP TABLE if exists yupeng_add_2%s;CREATE TABLE yupeng_add_2%s ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select A.adid, A.keyword, A.new_status, A.wm_dept_name, A.min_category, A.min_confidence, A.max_category, A.max_confidence, sum(case when B.date_string is null THEN 0 WHEN datediff('%s', B.date_string) <= 90 and B.customer_id_p = 1 and B.source_id = 2 and B.is_pla = 0 THEN B.orders ELSE 0 END) as orders_3m from yupeng_final_2%s A left join daily_kgl_traffic_revenue B on A.adid = B.adid group by A.adid, A.keyword, A.new_status, A.wm_dept_name, A.min_category, A.min_confidence, A.max_category, A.max_confidence\"" %(source_id,source_id,date, source_id)

hql10 = "\"select sum(case when new_status >= 1 THEN 1 ELSE 0 END) as num_correct, sum(case when new_status = -11 THEN 1 ELSE 0 END) as num_no_id, sum(case when new_status = -12 THEN 1 ELSE 0 END) as num_pla, sum(case when new_status = 0 or new_status = -1 THEN 1 ELSE 0 END) as num_wrong, sum(case when new_status <= -2 and new_status >= -10 THEN 1 ELSE 0 END) as num_unknown from yupeng_add_2%s\" > result_2%s.txt" %(source_id, source_id)
r1 = "\"select wm_dept_name, sum(case when new_status > 0 then 1 else 0 end) /sum(case when new_status >= -1 then 1 else 0 end) as accuracy, count(*) as cnt from yupeng_add_2%s where new_status >= -10 group by wm_dept_name order by cnt desc;\" > summary_department_2%s.txt" %(source_id, source_id)

r2 = "\"select adid, wm_dept_name, min_category, min_confidence, max_category, max_confidence from yupeng_add_2%s where new_status in (-1, 0)\"> mis_categorized_adids_2%s" %(source_id, source_id)

get_high_clicks = "\"select A.adid, A.keyword, A.wm_dept_name, A.min_category, A.min_confidence, A.max_category, A.max_confidence, sum(B.clicks) as click_1m, sum(B.adspend) as spend_1m, sum(B.revenue) as revenue_1m from yupeng_add_2%s A inner join daily_kgl_traffic_revenue B on A.adid = B.adid where A.new_status in (-1, 0) and datediff('2015-08-08', B.date_string) <= 30 group by A.adid, A.keyword, A.wm_dept_name, A.min_category, A.min_confidence, A.max_category, A.max_confidence sort by click_1m DESC, spend_1m DESC, revenue_1m DESC\" > mis_highclick_adids_2%s" %(source_id, source_id)
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
#a -> b -> mid -> rn
#c -> d -> e
#e + rn -> final
#test is useless
#final + rn + b -> update
seq = sys.argv[1].split(",")
hqls = [hql1, hql2, hql3, hql4, hql5, hql6, hql7, hql8, hql9, hql10, r1, r2, get_high_clicks]
for i in range(0, len(seq)):
    cmd_d = "hive -e" +  hqls[int(seq[i]) - 1]
    run(cmd_d)
