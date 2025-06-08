# -*- coding: utf-8 -*-
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

from app.fund import get_fund_info, get_fund_networth, get_fund_returns

fund_code = "013594"

# fund_info = get_fund_info(fund_code)
# print(fund_info)

# data = get_fund_data(fund_code)
# print(data)

returns = get_fund_returns(fund_code)
print(returns)
