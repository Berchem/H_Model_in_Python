import os
import requests
from MypseudoSQL import Table


class PriceVolumeInfo:
    def __init__(self):
        self.base_uri = "https://www.twse.com.tw/exchangeReport/FMTQIK?response=csv&date={year}{month}01"
        self.header = None
        self.data = None
        self.proxies = {'https': "172.18.212.222:3128"}

    def get(self, year, month):
        url = self.base_uri.format(year=year, month="%02d" % month)
        try:
            res = requests.get(url)
        except requests.exceptions.ProxyError:
            res = requests.get(url, proxies={'https': "172.18.212.222:3128"})
        return res.text

    @staticmethod
    def __strip(string, chars):
        s = string.strip()
        for char in chars:
            s = s.strip(char)
        return s

    def __cleaning(self, text):
        res_list = [self.__strip(row, ',"').split('","') for row in text.split("\n")]
        self.header = res_list[1]
        self.data = res_list[2:-6]

    def map_to_table(self, text):
        self.__cleaning(text)
        table = Table(self.header)
        for row in self.data:
            for j, col in enumerate(self.header):
                if col != "日期":
                    row[j] = float(row[j].replace(",", ""))
            table.insert(row)
        return table


def concat_tables(tables):
    for i, table in enumerate(tables):
        if i == 0:
            tb = table
        else:
            tb.rows += table.rows
    return tb


if "cache.csv" in os.listdir():
    data = []
    for i, line in enumerate(open("cache.csv")):
        line = line.split(",")
        if i == 0:
            table = Table(line)
        else:
            table.insert(line)

else:
    years = [2018, 2019]
    months = [i + 1 for i in range(12)]
    obj = PriceVolumeInfo()

    tables = []
    for year in years:
        for month in months:
            print("downloading", year, month)
            text = obj.get(year, month)
            table = obj.map_to_table(text)
            tables += [table]

    table = concat_tables(tables)
    table.to_csv("cache.csv")


print(table)
