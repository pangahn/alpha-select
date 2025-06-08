# -*- coding: utf-8 -*-
import json
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import akshare as ak
import pandas as pd
from dateutil.relativedelta import relativedelta

if os.getenv("VERCEL_ENV", "development") == "development":
    CACHE_DIR = Path(__file__).parent.parent / "cache"
else:
    CACHE_DIR = Path("/tmp/cache")
CACHE_DIR.mkdir(exist_ok=True)

FUND_CACHE_INDEX = CACHE_DIR / "fund_cache_index.json"
MAX_FUND_CACHE = int(os.getenv("MAX_FUND_CACHE", 100))


def get_cached_fund_info() -> Optional[pd.DataFrame]:
    """获取缓存的基金数据，如果缓存不存在或已过期则重新获取

    Returns
    -------
    pandas.DataFrame or None
        包含基金基本信息的DataFrame，字段包括：基金代码、基金简称、基金类型等
        如果获取失败则返回None
    """
    cache_file = CACHE_DIR / "fund_info_cache.pkl"

    today = datetime.now().date()
    if cache_file.exists():
        try:
            with cache_file.open("rb") as f:
                cache_data = pickle.load(f)
                cache_date = cache_data.get("date")

                # 如果缓存是今天的，直接返回
                if cache_date == today:
                    print("使用缓存的基金数据")
                    return cache_data.get("data")
        except Exception as e:
            print(f"读取缓存文件出错: {e}")

    # 缓存不存在或已过期，重新获取数据
    try:
        print("获取新的基金数据并缓存")
        fund_data = ak.fund_name_em()

        # 保存到缓存
        cache_data = {"date": today, "data": fund_data}
        with cache_file.open("wb") as f:
            pickle.dump(cache_data, f)

        return fund_data
    except Exception as e:
        print(f"获取基金数据出错: {e}")

        # 如果获取新数据失败但有旧缓存，尝试使用旧缓存
        if cache_file.exists():
            try:
                with cache_file.open("rb") as f:
                    print("获取新数据失败，使用旧缓存")
                    return pickle.load(f).get("data")
            except Exception as e:
                print(f"使用旧缓存出错: {e}")
                pass
        return None


def get_fund_info(fund_code: str) -> Dict[str, str]:
    """获取基金基本信息

    使用akshare获取指定基金代码的基本信息，包括基金名称和类型

    Parameters
    ----------
    fund_code : str
        基金代码，例如"004898"

    Returns
    -------
    Dict[str, str]
        包含基金基本信息的字典，包括：
        - name: 基金名称
        - type: 基金类型
    """
    try:
        fund_info = get_cached_fund_info()
        if fund_info is None:
            return {"name": f"基金 {fund_code}", "type": "查询信息为空"}

        fund_info = fund_info[fund_info["基金代码"] == fund_code]
        if fund_info.empty:
            return {"name": f"基金 {fund_code}", "type": "未查询到"}

        fund_data = fund_info.to_dict(orient="records")[0]
        return {"name": fund_data["基金简称"], "type": fund_data["基金类型"]}

    except Exception as e:
        print(f"获取基金信息时出错: {e}")
        return {"name": f"基金 {fund_code}", "type": "查询错误"}


def _get_cache_index() -> Dict:
    """获取并更新基金缓存索引

    Returns
    -------
    Dict
        包含所有缓存基金的索引，格式为 {fund_code: last_access_timestamp}
    """
    if FUND_CACHE_INDEX.exists():
        try:
            with FUND_CACHE_INDEX.open("r") as f:
                return json.load(f)
        except Exception as e:
            print(f"读取基金缓存索引文件出错: {e}")
            return {}
    return {}


def _update_cache_index(fund_code: str) -> None:
    """更新基金缓存索引，并在必要时清理旧缓存

    Parameters
    ----------
    fund_code : str
        要更新的基金代码
    """
    # 获取当前缓存索引
    cache_index = _get_cache_index()

    # 更新当前基金的访问时间
    current_time = datetime.now().timestamp()
    cache_index[fund_code] = current_time

    # 如果缓存数量超过限制，删除最旧的缓存
    if len(cache_index) > MAX_FUND_CACHE:
        # 按最后访问时间排序
        sorted_funds = sorted(cache_index.items(), key=lambda x: x[1])
        # 计算需要删除的数量
        to_remove = len(cache_index) - MAX_FUND_CACHE

        # 删除最旧的缓存文件和索引条目
        for i in range(to_remove):
            old_fund_code = sorted_funds[i][0]
            old_cache_file = CACHE_DIR / f"fund_data_{old_fund_code}.pkl"
            try:
                if old_cache_file.exists():
                    old_cache_file.unlink()  # 删除文件
                    print(f"删除旧缓存文件: {old_fund_code}")
                del cache_index[old_fund_code]  # 从索引中删除
            except Exception as e:
                print(f"删除旧缓存文件时出错: {e}")

    # 保存更新后的索引
    try:
        with FUND_CACHE_INDEX.open("w") as f:
            json.dump(cache_index, f)
    except Exception as e:
        print(f"保存基金缓存索引文件时出错: {e}")


def get_cached_fund_networth(fund_code: str) -> Optional[pd.DataFrame]:
    """获取缓存的基金净值数据，如果缓存不存在或已过期则重新获取

    Parameters
    ----------
    fund_code : str
        基金代码，例如"004898"

    Returns
    -------
    pandas.DataFrame or None
        包含基金净值数据的DataFrame，字段包括：净值日期、单位净值、日增长率
        如果获取失败则返回None
    """
    cache_file = CACHE_DIR / f"fund_networth_{fund_code}.pkl"
    today = datetime.now().date()

    if cache_file.exists():
        try:
            with cache_file.open("rb") as f:
                cache_data = pickle.load(f)
                cache_date = cache_data.get("date")

                # 如果缓存是今天的，直接返回
                if cache_date == today:
                    print(f"使用缓存的基金净值数据: {fund_code}")
                    # 更新缓存索引，表示该基金数据被访问
                    _update_cache_index(fund_code)
                    return cache_data.get("data")
        except Exception as e:
            print(f"读取基金净值缓存文件出错: {e}")

    # 缓存不存在或已过期，重新获取数据
    try:
        print(f"获取新的基金净值数据并缓存: {fund_code}")
        fund_data = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势", period="成立来")

        # 保存到缓存前先更新缓存索引，可能需要清理旧缓存
        _update_cache_index(fund_code)

        # 保存到缓存
        cache_data = {"date": today, "data": fund_data}
        with cache_file.open("wb") as f:
            pickle.dump(cache_data, f)

        return fund_data

    except Exception as e:
        print(f"获取基金净值数据出错: {e}")

        # 如果获取新数据失败但有旧缓存，尝试使用旧缓存
        if cache_file.exists():
            try:
                with cache_file.open("rb") as f:
                    print(f"获取新数据失败，使用旧缓存: {fund_code}")
                    # 即使使用旧缓存，也更新访问时间
                    _update_cache_index(fund_code)
                    return pickle.load(f).get("data")
            except Exception as e:
                print(f"使用旧缓存出错: {e}")
        return None


def get_fund_networth(fund_code: str) -> Optional[pd.DataFrame]:
    """获取基金的每日净值数据

    使用akshare接口获取指定基金代码的净值数据
    API文档：https://akshare.akfamily.xyz/data/fund/fund_public.html#id15

    Parameters
    ----------
    fund_code : str
        基金代码，例如"004898"

    Returns
    -------
    pandas.DataFrame or None
        包含基金净值数据的DataFrame，字段包括：净值日期、单位净值、日增长率
        如果获取失败则返回None

    """
    fund_data = get_cached_fund_networth(fund_code)
    fund_data["净值日期"] = pd.to_datetime(fund_data["净值日期"])
    fund_data.sort_values("净值日期", inplace=True)
    return fund_data


def calculate_weekly_returns(fund_data: pd.DataFrame, investment_amount: int = 100000) -> pd.DataFrame:
    """计算每周的收益金额 (全部历史数据)"""
    # 计算每日收益率
    fund_data["日收益率"] = fund_data["单位净值"].pct_change()
    fund_data.loc[fund_data.index[0], "日收益率"] = 0

    # 计算每日收益金额
    fund_data["日收益金额"] = fund_data["日收益率"] * investment_amount

    # 创建年周组合键，以处理跨年的周
    fund_data["周"] = fund_data["净值日期"].dt.isocalendar().week
    fund_data["年"] = fund_data["净值日期"].dt.isocalendar().year
    fund_data["年周"] = fund_data["年"].astype(str) + "-" + fund_data["周"].astype(str)

    # 计算周收益
    weekly_returns_df = (
        fund_data.groupby("年周").agg(周开始日期=("净值日期", "min"), 周结束日期=("净值日期", "max"), 周收益金额=("日收益金额", "sum")).reset_index()
    )

    # 按日期排序
    weekly_returns_df = weekly_returns_df.sort_values("周开始日期").reset_index(drop=True)

    # 格式化日期和收益
    weekly_returns_df["开始日期"] = weekly_returns_df["周开始日期"].dt.strftime("%m.%d")
    weekly_returns_df["结束日期"] = weekly_returns_df["周结束日期"].dt.strftime("%m.%d")
    weekly_returns_df["日期范围"] = weekly_returns_df["开始日期"] + " - " + weekly_returns_df["结束日期"]
    weekly_returns_df["收益"] = weekly_returns_df["周收益金额"]

    positive_weeks_count = 0
    if not weekly_returns_df.empty:
        positive_weeks_count = len(weekly_returns_df[weekly_returns_df["周收益金额"] > 0])

    avg_weekly_return = 0.0
    period_text = "N/A"
    if not weekly_returns_df.empty:
        max_week_end_date = weekly_returns_df["周结束日期"].max()
        if pd.notna(max_week_end_date):
            start_date_1y_dt = max_week_end_date - timedelta(days=365)
            data_1y_weekly = weekly_returns_df[weekly_returns_df["周开始日期"] >= start_date_1y_dt]
            total_weeks_count = len(weekly_returns_df)

            period_text = "1年"
            if total_weeks_count >= 52:
                avg_weekly_return = data_1y_weekly["周收益金额"].mean()
            else:
                avg_weekly_return = weekly_returns_df["周收益金额"].mean()
                period_text = f"{total_weeks_count}周"

    return weekly_returns_df, {
        "positive_weeks_count": positive_weeks_count,
        "period_text": period_text,
        "avg_weekly_return": avg_weekly_return,
    }


def get_recent_weekly_returns(weekly_returns_df: pd.DataFrame, num_weeks: int = 12) -> List[Dict[str, any]]:
    """
    从已计算的全部周收益数据中提取最近指定周数的数据，并格式化为网页展示所需格式。

    Args:
        weekly_returns_df (pd.DataFrame): 包含所有周收益数据的DataFrame。
                                             必须包含 '周开始日期', '日期范围', '开始日期', '结束日期', '收益' 列。
        num_weeks (int): 需要提取的最近周数，默认为12。

    Returns:
        weekly_data_list (list): 包含最近 num_weeks 周收益数据的列表，每项为字典。
    """
    if weekly_returns_df.empty:
        return []

    recent_weekly_df = weekly_returns_df.sort_values("周开始日期").tail(num_weeks).copy()
    recent_weekly_df["显示周序号"] = range(1, len(recent_weekly_df) + 1)

    weekly_data_list = []
    for _, row in recent_weekly_df.iterrows():
        week_data = {
            "date_range": row["日期范围"],
            "start_date": row["开始日期"],
            "end_date": row["结束日期"],
            "return_amount": row["收益"],
        }
        weekly_data_list.append(week_data)

    return weekly_data_list


def calculate_annualized_returns(fund_data: pd.DataFrame) -> Dict[str, float]:
    """计算基金的不同周期年化收益率

    计算近1周、近1个月、近3个月、近6个月、近1年及自成立以来的年化收益率

    Args:
        fund_data: 包含基金净值数据的DataFrame，需包含'净值日期'和'单位净值'列

    Returns:
        包含不同周期年化收益率的字典，键为周期名称，值为年化收益率（百分比）
    """
    if fund_data is None or fund_data.empty:
        return {"1week": 0.0, "1month": 0.0, "3months": 0.0, "6months": 0.0, "1year": 0.0, "since_inception": 0.0}

    # 获取最新日期和净值
    latest_date = fund_data["净值日期"].max()
    latest_value = fund_data[fund_data["净值日期"] == latest_date]["单位净值"].values[0]

    # 定义各个周期的时间范围
    period_deltas = {
        "1week": pd.Timedelta(days=7),
        "1month": relativedelta(months=1),
        "3months": relativedelta(months=3),
        "6months": relativedelta(months=6),
        "1year": relativedelta(years=1),
    }

    results = {}

    # 计算各个周期的年化收益率
    for period_name, period_delta in period_deltas.items():
        start_date = latest_date - period_delta

        # 找到开始日期之前最近的一个交易日数据
        prior_data = fund_data[fund_data["净值日期"] <= start_date]

        if prior_data.empty:
            # 如果没有足够的历史数据，则跳过该周期
            results[period_name] = 0.0
            continue

        # 获取开始日期的净值
        start_value = prior_data.iloc[-1]["单位净值"]

        # 计算实际天数
        actual_start_date = prior_data.iloc[-1]["净值日期"]
        actual_days = (latest_date - actual_start_date).days

        if actual_days <= 0:
            results[period_name] = 0.0
            continue

        # 计算年化收益率
        annualized_return = (latest_value - start_value) / start_value / actual_days * 365

        # 转换为百分比并保留两位小数
        results[period_name] = annualized_return * 100

    # 计算自成立以来的年化收益率
    # 获取最早的净值数据
    earliest_data = fund_data.iloc[0]
    earliest_date = earliest_data["净值日期"]
    earliest_value = earliest_data["单位净值"]

    # 计算自成立以来的天数
    inception_days = (latest_date - earliest_date).days

    if inception_days > 0:
        # 计算年化收益率
        since_inception_return = (latest_value - earliest_value) / earliest_value / inception_days * 365
        results["since"] = since_inception_return * 100
    else:
        results["since"] = 0.0

    return results


def calculate_historical_performance(fund_data: pd.DataFrame) -> Dict[str, float]:
    """
    计算不同时间区间的历史业绩表现
    计算近1月、近3月、近6月、近1年、近3年的涨跌幅

    Parameters
    ----------
    fund_data : pd.DataFrame
        包含基金净值数据的DataFrame，需包含'净值日期'和'单位净值'列

    Returns
    -------
    Dict[str, float]
        包含不同时间区间涨跌幅的字典，键为时间区间名称，值为涨跌幅（百分比）
    """
    latest_date = fund_data["净值日期"].max()
    latest_value = fund_data.loc[fund_data["净值日期"] == latest_date, "单位净值"].values[0]

    # 时间段定义（自然日）
    period_deltas = {
        "1week": pd.Timedelta(days=7),
        "1month": relativedelta(months=1),
        "3months": relativedelta(months=3),
        "6months": relativedelta(months=6),
        "1year": relativedelta(years=1),
    }

    results = {}
    for label, delta in period_deltas.items():
        # 目标时间点（自然时间）
        if isinstance(delta, pd.Timedelta):
            target_date = latest_date - delta
        else:
            target_date = latest_date - delta

        # 找小于等于 target_date 的最大交易日
        df_before = fund_data[fund_data["净值日期"] <= target_date]
        if df_before.empty:
            results[label] = None  # 没有足够早的数据
            continue

        start_nav = df_before["单位净值"].iloc[-1]
        pct = (latest_value - start_nav) / start_nav * 100
        results[label] = round(pct, 2)

    return results


def get_historical_networth_points(fund_data: pd.DataFrame) -> List[Dict[str, float]]:
    """获取基金历史净值数据点"""
    net_worth_data = []
    if not fund_data.empty:
        recent_data = fund_data.tail(30)
        for _, row in recent_data.iterrows():
            net_worth_data.append(
                {
                    "date": row["净值日期"].strftime("%Y-%m-%d"),
                    "value": round(float(row["单位净值"]), 4),
                    "growth_rate": round(float(row["日增长率"]) if pd.notna(row["日增长率"]) else 0.0, 2),
                }
            )
    return net_worth_data


def get_fund_returns(fund_code: str, investment_amount: Optional[int] = 100000) -> Dict[str, any]:
    """获取基金收益数据

    计算基金的总收益、平均收益、日收益和周收益数据

    Args:
        fund_code: 基金代码
        investment_amount: 投资金额，默认100000

    Returns:
        包含基金收益数据的字典
    """
    print(os.environ)
    # 基金信息
    fund_info = get_fund_info(fund_code)

    # 基金净值
    fund_data = get_fund_networth(fund_code)

    # 最新净值
    latest_value = fund_data.iloc[-1]["单位净值"]
    latest_date = fund_data.iloc[-1]["净值日期"].strftime("%Y-%m-%d")

    # 全年周收益
    all_weekly_returns_df, weekly_stats = calculate_weekly_returns(fund_data, investment_amount)

    # 近3个月周收益
    weekly_data = get_recent_weekly_returns(all_weekly_returns_df, num_weeks=12)

    # 年化收益率
    annualized_returns = calculate_annualized_returns(fund_data)

    # 历史业绩
    historical_performance = calculate_historical_performance(fund_data)

    # 历史净值
    networth_data = get_historical_networth_points(fund_data)

    result = {
        "fund_code": fund_code,
        "fund_name": fund_info["name"],
        "fund_type": fund_info["type"],
        "latest_value": latest_value,
        "latest_date": latest_date,
        "investment_amount": investment_amount,
        "avg_weekly_return": weekly_stats["avg_weekly_return"],
        "positive_weeks_count": weekly_stats["positive_weeks_count"],
        "period_text": weekly_stats["period_text"],
        "weekly_data": weekly_data,
        "annualized_returns": annualized_returns,
        "historical_performance": historical_performance,
        "net_worth_data": networth_data,
    }
    return result
