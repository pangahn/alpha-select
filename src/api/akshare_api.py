# -*- coding: utf-8 -*-
from datetime import timedelta

import akshare as ak
import pandas as pd
from cachetools import cached

from ..utils.cache_utils import FileCache

cache = FileCache(ttl=timedelta(hours=24))


@cached(cache=cache, key=lambda: "get_fund_list")
def get_fund_list() -> pd.DataFrame:
    """获取所有公募基金数据

    Returns:
        pd.DataFrame: 包含所有公募基金数据的DataFrame
            columns: 基金代码、基金简称、基金类型、申购状态、赎回状态
    """
    fund_name_df = ak.fund_name_em()[["基金代码", "基金简称", "基金类型"]]
    fund_purchase_df = ak.fund_purchase_em()[["基金代码", "申购状态", "赎回状态"]]
    fund_df = pd.merge(fund_name_df, fund_purchase_df, on="基金代码", how="outer")

    return fund_df
