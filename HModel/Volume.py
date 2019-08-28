# -*- coding: utf-8 -*-

from Futures.Config import Config
from Futures.DataUtil import DataUtil
import abc
from abc import ABC


class _VolumeIndicator(ABC):
    def __init__(self, conf):
        self._conf = conf
        self._interval = int(conf.prop.get("VOLUME", "INTERVAL"))
        self._data = None
        self._volume_indicator = None
        self._delta_of_target = None
        self._income_by_volume_indicator = None
        self._reserve = 0
        self._open_contract = 0
        self._traded_contract = 0

    def _load_data(self):
        pass

    def _calc_ma(self):
        pass

    def _calc_volume_indicator(self):
        pass

    def _calc_delta_of_target(self):
        pass

    def _calc_income_by_volume_indicator(self):
        pass

    def _calc_reserve(self):
        pass

    def _calc_open_contract(self):
        pass

    def _calc_traded_contract(self):
        pass

    @abc.abstractmethod
    def get(self):
        pass

    @abc.abstractmethod
    def set(self):
        pass


class WeightedIndex:
    pass


class FuturesPrice:
    pass
