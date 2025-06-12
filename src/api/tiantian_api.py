# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from typing import Any, Dict, List

import cachetools.func
import requests

logger = logging.getLogger(__name__)

TIANTIAN_HEADERS = {
    "Host": "fundcomapi.tiantianfunds.com",
    "User-Agent": "EMProjJijin/6.6.13 (iPhone; iOS 17.4.1; Scale/3.00)",
}


@cachetools.func.ttl_cache(maxsize=128, ttl=timedelta(hours=24).total_seconds())
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


@cachetools.func.ttl_cache(maxsize=128, ttl=timedelta(hours=24).total_seconds())
def get_asset_allocation(fund_code: str) -> dict:
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
    result.update(get_asset_allocation(fund_code))
    return result
