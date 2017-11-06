# coding=utf-8
from selenium import webdriver
from bs4 import BeautifulSoup
import time
import xlrd
from selenium.webdriver import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import pymysql
import uuid
import sys

from selenium.webdriver.common.keys import Keys


def __init__(self):
    self.login_url = 'https://www.tianyancha.com/login'
    self.username = '18002343053'
    self.password = 'george2009'
    self.word = '金科'.decode('utf-8')
    self.detail_url = 'https://www.tianyancha.com/company/334787306'


def login():
    old_driver = webdriver.Chrome()
    old_driver.get("https://www.tianyancha.com/login")

    # 模拟登陆
    old_driver.find_element_by_xpath(
        '//*[@id="web-content"]/div/div/div/div[2]/div/div[2]/div[2]/div[2]/div[2]/input').send_keys("18002343053")
    old_driver.find_element_by_xpath(
        '//*[@id="web-content"]/div/div/div/div[2]/div/div[2]/div[2]/div[2]/div[3]/input').send_keys("george2009")
    old_driver.find_element_by_xpath(
        '//*[@id="web-content"]/div/div/div/div[2]/div/div[2]/div[2]/div[2]/div[5]').click()
    time.sleep(0.14)
    old_driver.refresh()
    return old_driver


def driver_open():
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 5_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Mobile/9B176 MicroMessenger/4.3.2"
    )
    service_args = []
    service_args.append('--load-images=no')  ##关闭图片加载
    service_args.append('--disk-cache=yes')  ##开启缓存
    service_args.append('--ignore-ssl-errors=true')  ##忽略https错误
    driver = webdriver.PhantomJS(executable_path='/usr/local/bin/phantomjs', desired_capabilities=dcap,
                                 service_args=service_args)
    return driver


def get_content(url):
    open_driver = driver_open()
    open_driver.get(url)
    time.sleep(1)
    # 获取网页内容
    content = open_driver.page_source.encode('utf-8')
    # print content
    open_driver.close()
    res_soup = BeautifulSoup(content, 'lxml')
    com_id = url.split('/')[-1]
    if com_id.isdigit():
        return res_soup, com_id
    else:
        return res_soup


def get_basic_info(soup, company):
    result_list = soup.select('div.item-line')
    fddbr = soup.select('div.item-line > span:nth-of-type(2) > a')[0].get_text()
    result = result_list[0] if len(result_list) > 0 else None
    print u'法定代表人：' + fddbr  # 打开工作簿


def open_excel(file):
    try:
        book = xlrd.open_workbook(file)
        return book
    except Exception as e:
        print ('打开工作簿' + file + '出错：' + str(e))


# 读取工作簿中所有工作表
def read_sheets(file):
    try:
        book = open_excel(file)
        sheets = book.sheets()
        return sheets
    except Exception as e:
        print ('读取工作表出错：' + str(e))


# 读取某一工作表中数据某一列的数据
def read_data(sheet, n=0):
    dataset = []
    for r in range(sheet.nrows):
        col = sheet.cell(r, n).value
        dataset.append(col)
    return dataset


def load_excel(logfile, company_file):
    now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    with open(logfile, 'a') as f:
        f.write('\n当前时间：' + now + '\n')
    sheets = read_sheets(company_file)
    cornames = []
    for sheet in sheets:
        dataset = read_data(sheet)
        cornames.extend(dataset)
    return cornames


def crawl(name, driver):
    print '开始》》》》》》》' + name
    # 打开新窗口
    #new_window = 'window.open("https://www.tianyancha.com/");'
    #driver.execute_script(new_window)
    # 切换到新的窗口
    handles = driver.window_handles
    driver.switch_to_window(handles[-1])

    driver.get("https://www.tianyancha.com/")
    driver.find_element_by_xpath('//*[@id="home-main-search"]').send_keys(name)  # 输入名字
    time.sleep(2.34)
    driver.find_element_by_xpath(".//*[@class='input-group-addon search_button']").click()  # 点击搜索
    driver.implicitly_wait(10)
    driver.find_element_by_xpath('//*[@id="searchTogal"]').click()  # 收起
    time.sleep(0.21)
    # 选择相关度最高的搜索结果 第一条搜索框
    tag = driver.find_elements_by_xpath("//div[@class='search_right_item']")
    if len(tag) == 0:
        return None
    tag[0].find_element_by_tag_name('a').click()
    driver.implicitly_wait(5)
    # 转化句柄
    now_handle = driver.current_window_handle
    all_handles = driver.window_handles
    for handle in all_handles:
        if handle != now_handle:
            # 输出待选择的窗口句柄
            print(handle)
            driver.switch_to.window(handle)
    # 解析
    base = driver.find_element_by_xpath("//div[@class='company_header_width ie9Style']/div")
    name = base.text.split('浏览')[0]
    tel = base.text.split('电话：')[1].split('邮箱：')[0]
    liulan = base.text.split('浏览')[1].split('\n')[0]
    email = base.text.split('邮箱：')[1].split('\n')[0]
    web = base.text.split('网址：')[1].split('地址')[0]
    address = base.text.split('地址：')[1]
    # abstract = driver.find_element_by_xpath("//div[@class='sec-c2 over-hide']//script")
    tabs = driver.find_elements_by_tag_name('table')
    rows = tabs[1].find_elements_by_tag_name('tr')
    cols = rows[0].find_elements_by_tag_name('td' and 'th')
    # 工商主策号
    reg_code = rows[0].find_elements_by_tag_name('td')[1].text
    # 注册地址
    reg_address = rows[5].find_elements_by_tag_name('td')[1].text
    # 英文名称
    english_name = rows[5].find_elements_by_tag_name('td')[1].text
    # 经营范围
    ent_range = rows[6].find_elements_by_tag_name('td')[1].text
    # 统一信用代码
    creditcode = rows[1].find_elements_by_tag_name('td')[1].text
    # 纳税人识别号
    tax_code = rows[2].find_elements_by_tag_name('td')[1].text
    # 营业期限
    deadline = rows[3].find_elements_by_tag_name('td')[1].text
    # 企业类型
    ent_type = rows[1].find_elements_by_tag_name('td')[3].text
    idd = str(uuid.uuid1())
    idd.replace('-', '')

    based_info = (idd, name, tel, email, web, address, reg_code, reg_address, english_name, ent_range,
                  creditcode, tax_code, deadline, ent_type, name)
    # 关闭当前标签页
    # driver.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 'w')
    driver.close()
    return based_info


def save_data(table):
    conn = pymysql.connect(host='wentuotuo.com', user='root', passwd='root', db='tianyanchatest', port=3306,
                           charset='utf8')
    cur = conn.cursor()  # 获取一个游标
    sql = "INSERT INTO t1 (id, name, entPhone, entEmail, ent_url, ent_address," \
          " ent_reg_no,ent_reg_address, ent_english_name, ent_range, credit_code, tax_person_code, entDeadline, " \
          "ent_type, raw_name) VALUES ( '%s', '%s', '%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s' )"
    cur.execute(sql % table)
    conn.commit()
    cur.close()  # 关闭游标
    conn.close()  # 释放数据库资源


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    logfile = 'failed_log.txt'
    filename = '/Users/heym/PycharmProjects/tyc_spider/data/list.xlsx'
    # 登录
    old_driver = login()
    # 读取excel
    cornames = load_excel(logfile, filename)
    # 爬取网站
    for i in range(len(cornames)):
        name = cornames[i].strip()
        info = crawl(name, old_driver)
        if info is None:
            continue
        # 判断是否有信息了 todo
        save_data(info)
