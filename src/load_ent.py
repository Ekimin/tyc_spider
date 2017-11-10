# coding=utf-8
import sys
import uuid
from datetime import datetime
import pymysql
import xlrd


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


def load_excel(company_file):
    sheets = read_sheets(company_file)
    cornames = []
    for sheet in sheets:
        dataset = read_data(sheet)
        cornames.extend(dataset)
    return cornames


def save_data(cornames):
    j = 0
    many_values = []
    status = 'waiting'
    conn = pymysql.connect(host='wentuotuo.com', user='root', passwd='root', db='tianyanchatest', port=3306,
                           charset='utf8')
    cur = conn.cursor()  # 获取一个游标
    sql = "INSERT INTO quest (quest_id, ent_name, status, input_time) VALUES ( %s,%s,%s,%s)"
    for i in range(len(cornames)):
        name = cornames[i].strip()
        now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        idd = str(uuid.uuid1())
        idd.replace('-', '')
        values = (idd, name, status, now_time)
        many_values.append(values)
        j = j + 1
        if j % 1000 == 0:
            print str(i + 1) + ' === ' + str(name)
            cur.executemany(sql, many_values)
            many_values = []
            conn.commit()
            j = 0
    if j != 0:
        cur.executemany(sql, many_values)
        conn.commit()
    cur.close()  # 关闭游标
    conn.close()  # 释放数据库资源


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    filename = 'D:\Workspace\Pyworkspace\\tyc_spider\data\\first3000.xlsx'
    cornames = load_excel(filename)
    save_data(cornames)
