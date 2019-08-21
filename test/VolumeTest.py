# -*- coding: utf-8 -*-

from Futures.Config import Config
from Futures.DataUtil import DataUtil
import os

conf = Config("test-conf.ini")

BASE_DIR = conf.prop.get("VOLUME", "BASE_DIR")
RESOURCE_DIR = conf.prop.get("VOLUME", "RESOURCE_DIR")
filename = os.path.join(BASE_DIR, RESOURCE_DIR, "history_data_for_h_model.csv")

data_util = DataUtil()
data = data_util.get_data_from_file(filename, 1)
print(data.limit(5))

