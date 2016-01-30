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

hql1 = "\"DROP TABLE if exists yupeng_pre1;CREATE TABLE yupeng_pre1 ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select A.keyword, A.adid, A.match_type, B.wm_dept_name, B.rn from (select adid, upper(keyword) as keyword, upper(match_type) as match_type from daily_kgl_traffic_revenue where customer_id_p = 1 and source_id = 2 and is_pla = 0 union all select adid, upper(keyword) as keyword, upper(match_type) as match_type from snapshot_keyword_group_links) A inner join (select *, ROW_NUMBER() OVER (DISTRIBUTE BY adid SORT BY count DESC) rn from yupeng_tmpa_22) B on B.adid = A.adid where A.keyword is not NULL and A.keyword <> '' and (upper(keyword) like '%sWALMART%sSITE%s') = FALSE and match_type <> '' group by A.keyword, A.adid, A.match_type, B.wm_dept_name, B.rn\"" %('%', '%', '%')

hql2 = "\"DROP TABLE if exists yupeng_pre2;CREATE TABLE yupeng_pre2 ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select keyword, match_type, wm_dept_name from yupeng_pre1 where rn = 1\""

hql3 = "\"DROP TABLE if exists yupeng_exact1;CREATE TABLE yupeng_exact1 ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select A.keyword, A.match_type, sum(case A.wm_dept_name when B.wm_dept_name then A.rn ELSE 0 END) as rn_com from yupeng_pre1 A left join yupeng_pre2 B on A.keyword = B.keyword where B.match_type = 'EXACT' and A.match_type <> 'EXACT' group by A.keyword, A.match_type\""

hql4 = "\"DROP TABLE if exists yupeng_exact2;CREATE TABLE yupeng_exact2 ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select keyword, sum(case match_type when 'BROAD' then rn_com when 'PHRASE' then -1 * rn_com else 0 end) as measure from yupeng_exact1 group by keyword\""

hql5 = "\"DROP TABLE if exists yupeng_broad1;CREATE TABLE yupeng_broad1 ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select A.keyword, A.match_type, sum(case A.wm_dept_name when B.wm_dept_name then A.rn ELSE 0 END) as rn_com from yupeng_pre1 A left join yupeng_pre2 B on A.keyword = B.keyword where B.match_type = 'BROAD' and A.match_type <> 'BROAD' group by A.keyword, A.match_type\""

hql6 = "\"DROP TABLE if exists yupeng_broad2;CREATE TABLE yupeng_broad2 ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select keyword, sum(case match_type when 'EXACT' then rn_com when 'PHRASE' then -1 * rn_com else 0 end) as measure from yupeng_broad1 group by keyword\""

hql7 = "\"DROP TABLE if exists yupeng_phrase1;CREATE TABLE yupeng_phrase1 ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select A.keyword, A.match_type, sum(case A.wm_dept_name when B.wm_dept_name then A.rn ELSE 0 END) as rn_com from yupeng_pre1 A left join yupeng_pre2 B on A.keyword = B.keyword where B.match_type = 'PHRASE' and A.match_type <> 'PHRASE' group by A.keyword, A.match_type\""

hql8 = "\"DROP TABLE if exists yupeng_phrase2;CREATE TABLE yupeng_phrase2 ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' AS select keyword, sum(case match_type when 'EXACT' then rn_com when 'BROAD' then -1 * rn_com else 0 end) as measure from yupeng_phrase1 group by keyword\""


get_weight1 = "\"select sum(case when measure > 0 then 1 else 0 end) as broad_cnt, sum(case when measure < 0 then 1 else 0 end) as phrase_cnt from yupeng_exact2\""
get_weight2 = "\"select sum(case when measure > 0 then 1 else 0 end) as exact_cnt, sum(case when measure < 0 then 1 else 0 end) as phrase_cnt from yupeng_broad2\""
get_weight3 = "\"select sum(case when measure > 0 then 1 else 0 end) as exact_cnt, sum(case when measure < 0 then 1 else 0 end) as broad_cnt from yupeng_phrase2\""
#exact : 1845 / 5201 broad : 917 / 5576 phrase : 954 / 2361
clear = "\"DROP TABLE if exists yupeng_pre1; DROP TABLE if exists yupeng_pre2; DROP TABLE if exists yupeng_exact1;  DROP TABLE if exists yupeng_exact2;  DROP TABLE if exists yupeng_broad1;  DROP TABLE if exists yupeng_broad2;  DROP TABLE if exists yupeng_phrase1;  DROP TABLE if exists yupeng_phrase2;\""
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
#weight_info = open('weight_info', 'w')
def get_info():
    weight_info = open('weight_info', 'w')
    hqls = [hql1, hql2, hql3, hql4, hql5, hql6, hql7, hql8, get_weight1, get_weight2, get_weight3, clear]
   # hqls = [get_weight1, get_weight2, get_weight3]
    for i in range(0, len(hqls)):
        cmd_d = "hive -e" +  hqls[i]
        result = run(cmd_d)
        if hqls[i] in [get_weight1, get_weight2, get_weight3]:
                result = result.split('\t')
                weight_info.write(str(float(result[1]) / (float(result[0]) + float(result[1]))) + '\n')
    weight_info.close()
                                                                                                                     60,5          Bot

