﻿# coding=utf-8
import os

from selenium import webdriver
import time
import json
import requests
import pymysql
import uuid
import sys
from datetime import datetime
import logging
from selenium.common.exceptions import NoSuchElementException

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='myapp.log',
                    filemode='w')

#################################################################################################
# 定义一个StreamHandler，将INFO级别或更高的日志信息打印到标准错误，并将其添加到当前的日志处理对象#
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


#################################################################################################


def login():
    old_driver = webdriver.Chrome()
    old_driver.get("https://www.tianyancha.com/login")
    time.sleep(1.3)
    old_driver.implicitly_wait(10)
    # 模拟登陆
    old_driver.find_element_by_xpath(
        '//*[@id="web-content"]/div/div/div/div[2]/div/div[2]/div[2]/div[2]/div[2]/input').send_keys("18761671816")
    old_driver.find_element_by_xpath(
        '//*[@id="web-content"]/div/div/div/div[2]/div/div[2]/div[2]/div[2]/div[3]/input').send_keys("123456abc")
    time.sleep(2.3)
    old_driver.find_element_by_xpath(
        '//*[@id="web-content"]/div/div/div/div[2]/div/div[2]/div[2]/div[2]/div[5]').click()
    time.sleep(0.14)
    old_driver.refresh()
    old_driver.get('https://www.tianyancha.com/company/11480443')
    return old_driver


def crawl(name, driver, quest_id):
    logging.info('开始》》》》》》》' + name)
    try:
        try:
            driver.find_element_by_xpath('//*[@id="header-company-search"]').clear()  # 清除文本
        except:
            logging.error("----出验证码了，请处理-------")
            os._exit(0)
        driver.find_element_by_xpath('//*[@id="header-company-search"]').send_keys(name.decode('utf-8'))  # 输入名字

        # driver.find_element_by_xpath('//*[@id="header-company-search"]').send_keys('中国建材检验认证集团股份有限公司'.decode('utf-8'))  # 输入名字
        time.sleep(3.54)
        driver.find_element_by_xpath('//*[@id="web-header"]/div/div/div[1]/div[2]/div[2]/div[1]/div').click()  # 点击搜索
        driver.implicitly_wait(15)
        time.sleep(1.12)
        # driver.find_element_by_xpath('//*[@id="searchTogal"]').click()  # 收起
        time.sleep(0.21)
        # 提取列表
        try:
            detail_tag = driver.find_elements_by_xpath(
                '//div[@class="search_right_item"]/div/a/span')
            if len(detail_tag) == 0:
                no_result_match(quest_id)
                logging.info('没有匹配信息')
                return None
        except NoSuchElementException, e:
            error_quest(quest_id, 'errored')
            return None
        # 判断是否有完全匹配项
        count = 0
        full_match_status = 0
        match_item = None
        cym_full_text = ''
        for list_ent in detail_tag:
            count = count + 1
            if list_ent.text == name:
                full_match_status = 1
                break
        if full_match_status == 1:  # 有完全匹配项
            # 构造xpath
            detail_tag = driver.find_elements_by_xpath('//div[@class="search_right_item"]/div/a')
            match_item = detail_tag[count - 1]
        else:
            # 看曾用名中是否有完全匹配项
            try:
                cym_tag = driver.find_elements_by_xpath('//div[@class="search_row_new pt20"]')
            except:
                error_quest(quest_id, 'errored')
                return None
            cym_count = 3  # 为了我效率 只判断前2个
            count = 0
            cym_match_status = 0
            for cym_ent in cym_tag:
                count = count + 1
                cym_count = cym_count - 1
                if cym_count == 0:
                    break
                try:
                    cym_full_text = cym_ent.text.split('历史名称：')[-1].split("\\n")[0]
                    if cym_full_text == name:
                        cym_match_status = 1
                        break
                except:
                    continue
            if cym_match_status == 1: # 曾用名中有匹配项
                # 构造xpath
                detail_tag = driver.find_elements_by_xpath('//div[@class="search_right_item"]/div/a')
                match_item = detail_tag[count - 1]
            else: # 默认取第一条
                default_tag = driver.find_elements_by_xpath(
                    '//div[@class="search_right_item"]/div/a')
                match_item = default_tag[0]
        real_name = match_item.text  # 真实名字
        detail_url = match_item.get_attribute('href')
        driver.implicitly_wait(5)
        time.sleep(2.12)
        driver.get(detail_url)  # 获取详情页面
        driver.implicitly_wait(5)
        time.sleep(0.09)

        # 解析
        # 排除事业单位
        try:
            is_sydw = driver.find_element_by_xpath('//*[@id="company_web_top"]/div[2]/div[2]/div/p/span').text
            if is_sydw == '事业单位':
                logging.info('事业单位，跳过！')
                error_quest(quest_id, '事业单位')
                return None
            elif is_sydw == '香港企业':
                logging.info('香港企业，跳过！')
                error_quest(quest_id, '香港企业')
                return None
            elif is_sydw == '律所':
                logging.info('律所，跳过！')
                error_quest(quest_id, '律所')
                return None
        except:
            is_sydw = False
        # 基本信息
        base = driver.find_element_by_xpath("//div[@class='company_header_width ie9Style']/div")
        tel = base.text.split('电话：')[1].split('邮箱：')[0]
        email = base.text.split('邮箱：')[1].split('\n')[0]
        web = base.text.split('网址：')[1].split('地址')[0]
        address = base.text.split('地址：')[1]
        # tabs = driver.find_elements_by_tag_name('table')
        # rows = tabs[1].find_elements_by_tag_name('tr')

        # 企业背景table
        info_table = driver.find_element_by_xpath(
            '//*[@id="nav-main-backgroundItem"]/following-sibling::div[1]/div[2]/div/div[3]/table')
        info_rows = info_table.find_elements_by_tag_name('tr')
        # 工商注册号
        try:
            reg_code = info_rows[0].find_elements_by_tag_name('td')[1].text
        except:
            try:
                reg_code = driver.find_element_by_xpath(
                    '//*[@id="_container_baseInfo"]/div/div[3]/table/tbody/tr[1]/td[2]').text
            except:
                reg_code = 'null'
                logging.error('工商注册号 error')
        # 注册地址
        try:
            reg_address = info_rows[5].find_elements_by_tag_name('td')[1].text
        except:
            reg_address = 'null'
            logging.error('zhucedizhi error')
        # 经营范围
        try:
            ent_range = info_rows[6].find_elements_by_tag_name('td')[1].text
        except:
            ent_range = 'null'
            logging.error('经营范围 error')
        # 统一信用代码
        creditcode = info_rows[1].find_elements_by_tag_name('td')[1].text
        # 纳税人识别号
        tax_code = info_rows[2].find_elements_by_tag_name('td')[1].text
        # 营业期限
        try:
            deadline = info_rows[3].find_elements_by_tag_name('td')[1].text
        except:
            deadline = 'null'
            logging.error('营业期限 error')
        # 企业类型
        try:
            ent_type = info_rows[1].find_elements_by_tag_name('td')[3].text
        except:
            ent_type = 'null'
            logging.info('qiyeleixing error')
        idd = str(uuid.uuid1())
        idd.replace('-', '')

        # 法人代表
        try:
            frdb = driver.find_element_by_xpath('//*[@class="f18 overflow-width sec-c3"]/a').text
        except:
            frdb = driver.find_element_by_xpath('//*[@id="_container_baseInfo"]/div/div/table/tbody/tr/td[1]').text
        # 注册资本
        try:
            zczb = driver.find_element_by_xpath(
                '//*[@id="_container_baseInfo"]/div/div[2]/table/tbody/tr/td[2]/div[1]/div[2]/div').text
        except:
            zczb = 'null'
            logging.error('注册资本 error')
        # 企业状态
        try:
            ent_status = driver.find_element_by_xpath('//*[@class="baseinfo-module-content-value statusType1"]').text
        except:
            try:
                ent_status = driver.find_element_by_xpath(
                    '//*[@id="_container_baseInfo"]/div/div[2]/table/tbody/tr/td[2]/div[3]/div[2]/div').text
            except:
                try:
                    ent_status = driver.find_element_by_xpath(
                        '//*[@id="_container_baseInfo"]/div/div/table/tbody/tr/td[4]').text
                except:
                    ent_status = 'null'
                    logging.error('企业状态 error')
        # 注册时间
        try:
            regi_date = driver.find_element_by_xpath('//*[@class="new-border-bottom pt10"]/div[2]').text
        except:
            regi_date = 'null'
            logging.error('注册时间 error')
        # 核准日期
        try:
            hz_date = driver.find_element_by_xpath(
                '//*[@id="_container_baseInfo"]/div/div[3]/table/tbody/tr[4]/td[4]').text
        except:
            hz_date = 'null'
            logging.error('核准日期 error')
        # 登记机关
        try:
            regi_unit = driver.find_element_by_xpath(
                '//*[@id="_container_baseInfo"]/div/div[3]/table/tbody/tr[5]/td[2]').text
        except:
            regi_unit = 'null'
            logging.error('登记机关 error')
        now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if real_name == name:
            is_match = 'Y'
        elif cym_full_text == name:
            is_match = 'C'
        else:
            is_match = 'N'
        based_info = (real_name, name, quest_id, tel, email, web, address, reg_code, reg_address, ent_range,
                      creditcode, tax_code, deadline, ent_type, frdb, zczb, ent_status, regi_date, hz_date,
                      regi_unit, is_match, now_time)
    except Exception, e:
        logging.error(e.message)
        error_quest(quest_id, 'errored')
        return None
    return based_info


def save_data(table, quest_id):
    conn = pymysql.connect(host='wentuotuo.com', user='root', passwd='root', db='tianyanchatest', port=3306,
                           charset='utf8')
    cur = conn.cursor()  # 获取一个游标
    sql = "INSERT INTO ent_info (real_name, raw_name, quest_id, entPhone," \
          " entEmail,ent_url, ent_address, ent_reg_no, ent_reg_address, ent_range, credit_code, tax_person_code, entDeadline, " \
          "ent_type, ent_represent, regi_capital, ent_status, regi_date, hz_date, regi_unit, is_match, input_time) VALUES ( '%s','%s','%s','%s','%s','%s','%s', '%s', '%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s' )"
    cur.execute(sql % table)
    sql2 = "update quest set status='finished' where quest_id='" + quest_id + "'"
    cur.execute(sql2)
    conn.commit()
    cur.close()  # 关闭游标
    conn.close()  # 释放数据库资源


def error_quest(questid, error_info):
    conn = pymysql.connect(host='wentuotuo.com', user='root', passwd='root', db='tianyanchatest', port=3306,
                           charset='utf8')
    cur = conn.cursor()  # 获取一个游标
    sql = "update quest set status='" + error_info + "' where quest_id='" + questid + "'"  # 没匹配到
    cur.execute(sql)
    conn.commit()
    cur.close()  # 关闭游标
    conn.close()  # 释放数据库资源


def no_result_match(questid):
    conn = pymysql.connect(host='wentuotuo.com', user='root', passwd='root', db='tianyanchatest', port=3306,
                           charset='utf8')
    cur = conn.cursor()  # 获取一个游标
    sql = "update quest set status='nmfinished' where quest_id='" + questid + "'"  # 没匹配到
    cur.execute(sql)
    conn.commit()
    cur.close()  # 关闭游标
    conn.close()  # 释放数据库资源


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    logfile = 'failed_log.txt'
    try:
        # 登录
        logging.info("======开始登录=====")
        old_driver = login()
    except Exception:
        logging.error('登录出错')
    while 1:
        # test
        #crawl('北京德恒（重庆）律师事务所', old_driver, '103228e1-c5d8-11e7-af0d-a81e84e538c2')
        # 获取任务
        try:
            r = requests.get("http://pubvip.org:8011/getquest").text
        except:
            logging.error('获取任务出错,等待重试')
            time.sleep(10)
            continue
        req = r.encode('utf-8')
        quest_list = json.loads(r, encoding='utf-8')
        # quest = "43shiu2872834;万达;陈仁飞;大神;王老吉"
        if len(quest_list) == 0:
            logging.info('没有任务,休眠10秒')
            time.sleep(10)
        for quest in quest_list:
            quest_id = quest["quest_id"]
            ent_name = quest["ent_name"]
            # 爬取网站
            info = crawl(ent_name, old_driver, quest_id)
            if info is None:
                continue
            # 判断是否有信息了 todo
            try:
                save_data(info, quest_id)
            except:
                logging.error('存储结果失败,添加任务进error')
                try:
                    error_quest(quest_id, '入库失败')
                except:
                    logging.error('添加任务进error表也失败了，停止程序！')
                    os._exit(0)
        time.sleep(3)
