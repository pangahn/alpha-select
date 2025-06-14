# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from typing import Dict

import akshare as ak
import pandas as pd
from cachetools import cached

from ..utils.cache_utils import FileCache

cache = FileCache(ttl=timedelta(hours=24))

logger = logging.getLogger(__name__)


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


def get_fund_info(fund_code: str) -> Dict[str, str]:
    """获取指定基金基本信息

    Parameters
    ----------
    fund_code : str
        基金代码，例如"004898"

    Returns
    -------
    Dict[str, str]
        包含基金基本信息的字典，包括：
        - 基金代码, 基金简称, 基金类型, 申购状态, 赎回状态
    """
    fund_df = get_fund_list()
    fund_info = fund_df[fund_df["基金代码"] == fund_code]

    if fund_info.empty:
        return {
            "基金代码": fund_code,
            "基金简称": "未查询到",
            "基金类型": "未查询到",
            "申购状态": "未查询到",
            "赎回状态": "未查询到",
        }

    return fund_info.to_dict(orient="records")[0]
