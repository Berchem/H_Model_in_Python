# -*- coding: utf-8 -*-
import warnings
import functools
import csv
import abc
from abc import ABC


def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)  # turn off filter
        warnings.warn("Call to deprecated function {}.".format(func.__name__),
                      category=DeprecationWarning,
                      stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning)  # reset filter
        return func(*args, **kwargs)
    return new_func


def read_csv(filename, with_header=True):
    with open(filename) as f:
        csv_reader = csv.reader(f)
        if with_header:
            next(csv_reader)
        data = [row for row in csv_reader]
    return data


def time_to_num(time):
    '''
    :param  time: <str>, format: HHMMSSss
    :return: num: <int>
    '''
    time = time.zfill(8)
    time_list = [int(time[i:i+2]) for i in range(0, 8, 2)]
    unit_list = ["HH", "MM", "SS", "ss"]
    hash_map = dict(zip(unit_list, time_list))
    hash_map["HH"] *= 360000
    hash_map["MM"] *= 6000
    hash_map["SS"] *= 100
    return sum(val for val in hash_map.values())  # num


def num_to_time(num):
    '''
    :param   num: <int>
    :return time: <str>, format: HHMMSSss
    '''
    ss = "%02d" % (num % 100)
    time = num // 100
    SS = "%02d" % (time % 60)
    time //= 60
    MM = "%02d" % (time % 60)
    time //= 60
    HH = "%02d" % (time % 60)
    return HH + MM + SS + ss


class _TechnicalIndicators(ABC):
    def __init__(self):
        self._time = None

    def _is_out_of_order(self, timestamp):
        if timestamp < time_to_num(self._time):
            raise Exception("timestamp is out of order")

    @abc.abstractmethod
    def update(self, *args):
        pass

    @abc.abstractmethod
    def get(self, *args):
        pass


class _Batched(_TechnicalIndicators, ABC):
    def __init__(self, initial_time, period):
        """
        :param initial_time: <str>, start time, e.g., "08450000"
        :param period      : <int>, period for updating sequence, e.g., 6000 for 1 minute
        """
        super().__init__()
        self._time = initial_time
        self._timestamp = time_to_num(initial_time)
        self._period = period


class _Continuous(_TechnicalIndicators, ABC):
    def _initialize_time(self, time):
        if self._time is None:
            self._time = time


class MovingAverage(_Batched):
    def __init__(self, initial_time, period, interval):
        """
        :param interval    : <int>, sequence of n values, e.g., 10
        :param period      : <int>, period for updating sequence, e.g., 6000 for 1 minute
        :param initial_time: <str>, start time, e.g., "08450000"
        """
        _Batched.__init__(self, initial_time, period)
        self.__interval = interval
        # price
        self.__ma_price_array = []
        self.__ma_price_value = None
        # volume
        self.__latest_volume = 0
        self.__ma_volume_array = []
        self.__ma_volume_value = None

    def update(self, time, price, volume):
        """
        :param   time: <str> info_time
        :param  price: <int> or <float> price
        :param volume: <int> or <float> volume (or amount)
        :return: void
        """
        timestamp = time_to_num(time)

        # initialized attributes
        if len(self.__ma_price_array) == 0:
            self.__latest_volume = volume
            self.__ma_volume_array.append(volume - self.__latest_volume)
            self.__ma_price_array.append(price)

        # throw exception
        self._is_out_of_order(timestamp)

        # updating
        if timestamp < self._timestamp + self._period:
            self.__ma_price_array[-1] = price
            self.__ma_volume_array[-1] = volume - self.__latest_volume

        else:
            self._timestamp += self._period
            self.__latest_volume = volume

            if len(self.__ma_price_array) == self.__interval:
                self.__ma_price_array = self.__ma_price_array[1:] + [price]
                self.__ma_volume_array = self.__ma_volume_array[1:] + [0]

            else:
                self.__ma_price_array.append(price)
                self.__ma_volume_array.append(0)

        self._time = time
        self.__ma_price_value = float(sum(self.__ma_price_array)) / len(self.__ma_price_array)
        self.__ma_volume_value = float(sum(self.__ma_volume_array)) / len(self.__ma_volume_array)

    def get(self, info):
        """
        :param info: <string> price or volume
        :return: (str raw_time, float ma_value)
        """
        key = info.lower()
        if key == "price":
            return self._time, self.__ma_price_value

        elif key == "volume":
            return self._time, self.__ma_volume_value


class OpenHighLowClose(_Batched, _Continuous):
    def __init__(self, initial_time=None, period=None, ticks=None):
        """
        :param initial_time: <str> start time, e.g. "08450000"
        :param period      : <int> period for refresh attributes
        :param ticks       : <int> number of ticks, e.g. 200
        """
        if ticks:
            _Continuous.__init__(self)
        else:  # by time
            _Batched.__init__(self, initial_time, period)

        self.__open = None
        self.__high = None
        self.__low = None
        self.__close = None
        self.__ticks = ticks
        self.__count = 0

    @classmethod
    def ticks(cls, ticks):
        return cls(ticks=ticks)

    def __initialize_prices(self, price):
        if self.__high is None:
            self.__high = price

        if self.__low is None:
            self.__low = price

        if self.__open is None:
            self.__open = price

        if self.__close is None:
            self.__close = price

    def __update_cache(self, price):
        if price > self.__high:
            self.__high = price

        if price < self.__low:
            self.__low = price

        self.__close = price

    def __update_new_one(self, price):
        self.__open = price
        self.__high = price
        self.__low = price
        self.__close = price

    def __updated_by_time(self, timestamp, price):
        if timestamp < self._timestamp + self._period:
            self.__update_cache(price)

        else:
            self.__update_new_one(price)
            self._timestamp += self._period

    def __updated_by_tick(self, price):
        if self.__count < self.__ticks:
            self.__update_cache(price)
            self.__count += 1

        else:
            self.__update_new_one(price)
            self.__count = 1

    def update(self, time, price):
        """
        :param time : <str> info_time
        :param price: <int> or <float> price
        :return: void
        """
        timestamp = time_to_num(time)

        # initialized attributes
        self._initialize_time(time)
        self.__initialize_prices(price)

        # throws exception
        self._is_out_of_order(timestamp)

        # updating
        if self.__ticks:  # <int>
            self.__updated_by_tick(price)

        else:  # <NoneType>
            self.__updated_by_time(timestamp, price)

        self._time = time

    def get(self):
        """
        timestamp : (start time) + n * period
        open      : opening price to current timestamp
        high      : highest price to current timestamp
        low       : lowest price to current timestamp
        close     : latest price to current timestamp
        :return: (str timestamp , int open, int, high, int low, int close)
        """
        time = self._time if self.__ticks else num_to_time(self._timestamp)
        return time, self.__open, self.__high, self.__low, self.__close


class VolumeCount(_Batched):
    def __init__(self, initial_time, period):
        """
        estimating the trading volume per period
        :param initial_time: <str> initial time, e.g., "8450000"
        :param period      : <int> period for estimating trading volume
        """
        _Batched.__init__(self, initial_time, period)
        self.__quantity = None
        self.__last_amount = None

    def update(self, time, amount):
        """
        :param time  : <str> time, e.g., "08450010"
        :param amount: <int> current trading volume
        :return: void
        """
        timestamp = time_to_num(time)

        if self.__quantity is None:
            self.__quantity = 0

        if self.__last_amount is None:
            self.__last_amount = amount

        self._is_out_of_order(timestamp)

        if timestamp < self._timestamp + self._period:
            self.__quantity = amount - self.__last_amount

        else:
            self._timestamp += self._period
            self.__quantity = 0
            self.__last_amount = amount

    def get(self):
        """
        :return: (<str> timestamp, <int> volume in current period)
        """
        time = num_to_time(self._timestamp)
        return time, self.__quantity


class HighLowPrice(_Continuous):
    def __init__(self):
        """
        :param: void
        """
        _Continuous.__init__(self)
        self.__high = None
        self.__low = None

    def _initialize_high_low(self, price):
        """
        initilaized high & low price
        :param price: <int> or <float> price
        :return: void
        """
        if self.__high is None or self.__low is None:
            self.__high = price
            self.__low = price

    def update(self, time, price):
        """
        :param time : <str> info_time
        :param price: <int> or <float> price
        :return: void
        """
        timestamp = time_to_num(time)

        # initialized attributes
        self._initialize_time(time)
        self._initialize_high_low(price)

        # throw exception
        self._is_out_of_order(timestamp)

        # updating
        if price > self.__high:
            self.__high = price

        if price < self.__low:
            self.__low = price

        self._time = time

    def get(self):
        """
        :return: (str raw_time, int high, int low)
        """
        return self._time, self.__high, self.__low


class AverageVolume(_Continuous):
    def __init__(self):
        """
        :param: void
        """
        _Continuous.__init__(self)
        self.__avg_buy = None
        self.__avg_sell = None

    def update(self, time, volume, buy_count, sell_count):
        timestamp = time_to_num(time)

        # initialized attributes
        self._initialize_time(time)

        # throw exception
        self._is_out_of_order(timestamp)

        # updating
        __volume = float(volume)
        self.__avg_buy = __volume / buy_count
        self.__avg_sell = __volume / sell_count
        self._time = time

    def get(self):
        return self._time, self.__avg_buy, self.__avg_sell


class SimpleSellBuyVolume(_Continuous):
    def __init__(self):
        """
        current price  --> next price
        sell: next price < current price 內盤
        buy : next price > current price 外盤
        """
        _Continuous.__init__(self)
        self.__last_price = None
        self.__sell = 0
        self.__buy = 0

    def _initialize_last_price(self, price):
        """
        initialized last price
        :param price: <int> or <float> price
        :return: void
        """
        if self.__last_price is None:
            self.__last_price = price

    def update(self, time, price, volume):
        """
        :param   time: <str> info_time
        :param  price: <int> or <float> price
        :param volume: <int> or <float> qty
        :return: void
        """
        timestamp = time_to_num(time)

        # initialized attributes
        self._initialize_time(time)
        self._initialize_last_price(price)

        # throw exception
        self._is_out_of_order(timestamp)

        # updating
        if price < self.__last_price:
            self.__sell += volume

        if price > self.__last_price:
            self.__buy += volume

        self.__last_price = price
        self._time = time

    def get(self):
        """
        :return: (<str> raw_time, <int> current_price, <int> volume of sell, <int> volume of buy)
        """
        return self._time, self.__last_price, self.__sell, self.__buy


class SellBuy(_Continuous):
    def __init__(self):
        _Continuous.__init__(self)
        self.__price = None
        self.__value = None
        self.__sell_price_1 = None
        self.__buy_price_1 = None
        self.__sell_value = 0
        self.__sell_count = 0
        self.__buy_value = 0
        self.__buy_count = 0

    def update(self, time, price, up1, down1, volume):
        timestamp = time_to_num(time)

        # initialized attributes
        self._initialize_time(time)

        # throw exception
        self._is_out_of_order(timestamp)

        self.__price = price
        self.__sell_price_1 = down1
        self.__buy_price_1 = up1
        self.__value = volume

        if self.__price < self.__sell_price_1:
            self.__sell_value += self.__value
            self.__sell_count += 1

        if self.__price > self.__buy_price_1:
            self.__buy_value += self.__value
            self.__buy_count += 1

        self._time = time

    def __get_volume(self):
        return self._time, self.__buy_value, self.__sell_value

    def __get_ratio(self):
        return self._time, self.__buy_value / float(self.__sell_value + self.__buy_value)

    def __get_count(self):
        return self._time, self.__buy_count, self.__sell_count

    def get(self, info):
        key = info.lower()
        if key == "volume":
            return self.__get_volume()

        elif key == "count":
            return self.__get_count()

        elif key == "ratio":
            return self.__get_ratio()

        else:
            raise Exception("given key: volume, count or ratio. ")


class CommissionInfo(_Continuous):
    def __init__(self):
        _Continuous.__init__(self)
        # sell
        self.__sell_volume_latest = None
        self.__sell_volume = None
        self.__sell_count = None

        # buy
        self.__buy_volume_latest = None
        self.__buy_volume = None
        self.__buy_count = None

        # current
        self.__diff_sell_volume = None
        self.__diff_buy_volume = None

        # diff volume of buy - sell
        self.__diff_order = None

        # average
        self.__avg_sell = None
        self.__avg_buy = None

    def _initialize_latest_sell_vol(self, sell_volume):
        if self.__sell_volume_latest is None:
            self.__sell_volume_latest = float(sell_volume)

    def _initialize_latest_buy_vol(self, buy_volume):
        if self.__buy_volume_latest is None:
            self.__buy_volume_latest = float(buy_volume)

    def update(self, time, sell_volume, sell_count, buy_volume, buy_count):
        timestamp = time_to_num(time)

        # initialized attributes
        self._initialize_time(time)
        self._initialize_latest_sell_vol(sell_volume)
        self._initialize_latest_buy_vol(buy_volume)

        # throw exception
        self._is_out_of_order(timestamp)

        # ===== raw info =====
        self._time = time
        self.__sell_volume = float(sell_volume)
        self.__sell_count = float(sell_count)
        self.__buy_volume = float(buy_volume)
        self.__buy_count = float(buy_count)

        # ==== indicators ====
        # difference of volume: buy - sell
        self.__diff_order = self.__buy_volume - self.__sell_volume
        # cumulative average volume: <action> volume / count
        self.__avg_sell = self.__sell_volume / self.__sell_count
        self.__avg_buy = self.__buy_volume / self.__buy_count
        # current difference
        self.__diff_sell_volume = self.__sell_volume - self.__sell_volume_latest
        self.__diff_buy_volume = self.__buy_volume - self.__buy_volume_latest
        # update
        self.__sell_volume_latest = self.__sell_volume
        self.__buy_volume_latest = self.__buy_volume

    def get(self, info):
        key = info.lower()
        if key == "diff":
            return self._time, self.__diff_order

        elif key == "avg":
            return self._time, self.__avg_sell, self.__avg_buy

        elif key == "current":
            return self._time, self.__diff_sell_volume, self.__diff_buy_volume

        else:
            raise Exception("given key: volume, count or ratio. ")


class WeightedAveragePrice(_Continuous):
    def __init__(self):
        _Continuous.__init__(self)
        self.__avg_sell_price = None
        self.__avg_buy_price = None

    def update(self, time, sell_pairs, buy_pairs):
        timestamp = time_to_num(time)

        # initialized attributes
        self._initialize_time(time)

        # throws exception
        self._is_out_of_order(timestamp)

        # updating
        self._time = time
        self.__avg_sell_price = sum(_[0] * _[1] for _ in sell_pairs) / sum(_[1] for _ in sell_pairs)
        self.__avg_buy_price = sum(_[0] * _[1] for _ in buy_pairs) / sum(_[1] for _ in buy_pairs)

    def get(self):
        return self._time, self.__avg_sell_price, self.__avg_buy_price


class InstitutionalPosition(_Continuous):
    def __init__(self):
        _Continuous.__init__(self)
        self.price = 0
        self.last_buy_cnt = 0
        self.last_sell_cnt = 0
        self.acc_buy = 0
        self.acc_sell = 0

    def update(self, time, price, current_volume, sell_count, buy_count):
        timestamp = time_to_num(time)
        self._initialize_time(time)
        if self.last_buy_cnt == 0 and self.last_sell_cnt == 0:
            self.last_buy_cnt = buy_count
            self.last_sell_cnt = sell_count

        self._is_out_of_order(timestamp)

        diff_buy_cnt = buy_count - self.last_buy_cnt
        diff_sell_cnt = sell_count - self.last_sell_cnt
        if current_volume >= 10:
            if diff_buy_cnt == 1 and diff_sell_cnt > 1:
                self.acc_buy += current_volume
                # print(match_time, match_price, match_qty, 0, acc_buy, acc_sell)

            elif diff_sell_cnt == 1 and diff_buy_cnt > 1:
                self.acc_sell += current_volume
                # print(match_time, match_price, 0, match_qty, acc_buy, acc_sell)

        self.last_buy_cnt = buy_count
        self.last_sell_cnt = sell_count
        self._time = time
        self.price = price

    def get(self, *args):
        return self._time, self.price, self.last_sell_cnt
