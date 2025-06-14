# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from typing import Any, Dict, List

import cachetools.func
import pandas as pd
import requests
from cachetools import cached

from ..utils.cache_utils import FileCache
from .akshare_api import get_fund_info

cache = FileCache(ttl=timedelta(hours=24))

logger = logging.getLogger(__name__)

TIANTIAN_HEADERS = {
    "Host": "fundcomapi.tiantianfunds.com",
    "User-Agent": "EMProjJijin/6.6.13 (iPhone; iOS 17.4.1; Scale/3.00)",
}


@cached(cache=cache, key=lambda fund_code: f"get_bond_investment_distribution__{fund_code}")
def get_bond_investment_distribution(fund_code: str) -> dict:
    """获取债券基金券种分布数据
        {
      'data': [
        {
          'FCODE': '010310',
          'REPORTDATE': '2025-03-31',
          'BONDTYPENEW': '2',
          'PCTNV': '129.95'
        },
        {
          'FCODE': '010310',
          'REPORTDATE': '2025-03-31',
          'BONDTYPENEW': '4',
          'PCTNV': '0.0'
        },
        {
          'FCODE': '010310',
          'REPORTDATE': '2025-03-31',
          'BONDTYPENEW': '1',
          'PCTNV': '0.0'
        },
        {
          'FCODE': '010310',
          'REPORTDATE': '2025-03-31',
          'BONDTYPENEW': '3',
          'PCTNV': '0.0'
        }
      ],
      'errorCode': 0,
      'firstError': None,
      'success': True,
      'hasWrongToken': None,
      'totalCount': 4,
      'expansion': '2025-03-31',
      'jf': 'ali'
    }
    """
    result = {"基金代码": fund_code, "报告日期": "", "信用债": 0, "利率债": 0, "可转债": 0, "其他券种": 0}

    url = "https://fundcomapi.tiantianfunds.com/mm/FundMNewApi/FundBondInvestDistri"
    response = requests.get(url, params={"FCODE": fund_code}, headers=TIANTIAN_HEADERS)
    content = response.json()
    if content.get("totalCount", 0) == 0:
        logger.warning(f"基金{fund_code}券种分布数据缺失.")
        return result

    name_map = {"1": "信用债", "2": "利率债", "3": "可转债", "4": "其他券种"}
    data: List[Dict[str, Any]] = content["data"]
    result["报告日期"] = data[0]["REPORTDATE"]
    for item in data:
        bond_type_name = name_map.get(item["BONDTYPENEW"], "未知")
        result[bond_type_name] = float(item["PCTNV"]) if item["PCTNV"] else 0

    return result


@cached(cache=cache, key=lambda fund_code: f"get_fund_asset_allocation__{fund_code}")
def get_fund_asset_allocation(fund_code: str) -> dict:
    """获取资产分类分布数据
    {
    "data": [
        {
        "FSRQ": "2025-03-31",
        "GP": "19.91", # 股票
        "ZQ": "84.51", # 债券
        "HB": "0.92", # 现金
        "JZC": "60.7198",
        "QT": "0.0", # 其他
        "JJ": "",
        "BZDM": "020020",
        "GP_AVG_BTYPE": "13.6",
        "JJCHGRT": ""
        }
    ],
    "errorCode": 0,
    "firstError": null,
    "success": true,
    "hasWrongToken": null,
    "totalCount": 1,
    "expansion": "2025-03-31",
    "jf": "huawei"
    }
    """
    result = {"基金代码": fund_code, "报告日期": "", "股票": 0, "债券": 0, "现金": 0, "其他资产": 0}

    url = "https://fundcomapi.tiantianfunds.com/mm/FundMNewApi/FundAssetAllocation"
    response = requests.get(url, params={"FCODE": fund_code}, headers=TIANTIAN_HEADERS)
    content = response.json()
    if content.get("totalCount", 0) == 0:
        logger.warning(f"基金{fund_code}资产分类分布数据缺失.")
        return result

    name_map = {"GP": "股票", "ZQ": "债券", "HB": "现金", "QT": "其他资产", "FSRQ": "报告日期"}
    data = content["data"][0]

    for key, value in name_map.items():
        if key == "FSRQ":
            result[value] = data[key]
        else:
            result[value] = float(data[key]) if data[key] else 0
    return result


def get_fund_distribution(fund_code: str) -> dict:
    """获取基金券种分布和资产分类分布数据"""
    result = {"基金代码": fund_code}
    result.update(get_bond_investment_distribution(fund_code))
    result.update(get_fund_asset_allocation(fund_code))
    return result


def _process_money_fund_values(fund_code: str, content: dict):
    """
    处理货币基金净值数据

    Parameters
    ----------
    fund_code : str
        基金代码，例如"004898"
    content : dict
        包含基金净值数据的字典

    Returns
    -------
    pd.DataFrame
        包含基金净值数据的DataFrame
        列包括：基金代码、净值日期、每万份收益、7日年化收益率
    """
    if content.get("totalCount", 0) == 0:
        logger.warning(f"货币型基金{fund_code}数据缺失.")
        df = pd.DataFrame(columns=["基金代码", "净值日期", "每万份收益", "7日年化收益率"])
        df = df.astype({"基金代码": "str", "净值日期": "str", "每万份收益": "float64", "7日年化收益率": "float64"})
        return df

    df = (
        pd.DataFrame(content["data"])[["FSRQ", "DWJZ", "LJJZ"]]
        .rename(columns={"FSRQ": "净值日期", "DWJZ": "每万份收益", "LJJZ": "7日年化收益率"})
        .sort_values(by=["净值日期"], ascending=True)
        .reset_index(drop=True)
    )

    df["每万份收益"] = pd.to_numeric(df["每万份收益"], errors="coerce")
    df["7日年化收益率"] = pd.to_numeric(df["7日年化收益率"], errors="coerce")
    df["净值日期"] = pd.to_datetime(df["净值日期"], errors="coerce")

    df.insert(0, "基金代码", fund_code)
    return df


@cached(cache=cache, key=lambda fund_code: f"get_fund_values__{fund_code}")
def get_fund_values(fund_code: str):
    url = "https://fundcomapi.tiantianfunds.com/mm/newCore/FundVPageDiagram"
    params = {"FCODE": fund_code, "RANGE": "ln"}
    response = requests.get(url, params=params, headers=TIANTIAN_HEADERS)
    content = response.json()

    fund_info = get_fund_info(fund_code)
    fund_type = fund_info["基金类型"]

    if "货币型" in fund_type:
        return _process_money_fund_values(fund_code, content)

    if content.get("totalCount", 0) == 0:
        logger.warning(f"基金{fund_code}净值数据缺失.")
        df = pd.DataFrame(columns=["基金代码", "净值日期", "单位净值", "累计净值"])
        df = df.astype({"基金代码": "str", "净值日期": "str", "单位净值": "float64", "累计净值": "float64"})
        return df

    df = (
        pd.DataFrame(content["data"])[["FSRQ", "DWJZ", "LJJZ"]]
        .rename(columns={"FSRQ": "净值日期", "DWJZ": "单位净值", "LJJZ": "累计净值"})
        .sort_values(by=["净值日期"], ascending=True)
        .reset_index(drop=True)
    )

    df["单位净值"] = pd.to_numeric(df["单位净值"], errors="coerce")
    df["累计净值"] = pd.to_numeric(df["累计净值"], errors="coerce")
    df["净值日期"] = pd.to_datetime(df["净值日期"], errors="coerce")

    df.insert(0, "基金代码", fund_code)

    return df
