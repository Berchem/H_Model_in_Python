# -*- coding: utf-8 -*-

from Futures.Config import Config
from Futures.DataUtil import DataUtil
import os
import datetime as dt

conf = Config("test-conf.ini")

BASE_DIR = conf.prop.get("VOLUME", "BASE_DIR")
RESOURCE_DIR = conf.prop.get("VOLUME", "RESOURCE_DIR")
filename = os.path.join(BASE_DIR, RESOURCE_DIR, "history_data_for_h_model.csv")

data_util = DataUtil()
data = data_util.get_data_from_file(filename, 1)
print(data.limit(5))

t = dt.datetime.strptime("2017-08-15 09:01:35.17", "%Y-%m-%d %H:%M:%S.%f")
t_i = dt.datetime.strptime("2017-08-15 09:01:35.7", "%Y-%m-%d %H:%M:%S.%f")

print(t_i - t)

print("%12s: %d" % ("year", t.year))
print("%12s: %d" % ("month", t.month))
print("%12s: %d" % ("day", t.day))
print("%12s: %d" % ("hour", t.hour))
print("%12s: %d" % ("minute", t.minute))
print("%12s: %d" % ("second", t.second))
print("%12s: %d" % ("microsecond", t.microsecond))
