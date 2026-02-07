"""
简化版的股票数据API - 直接复制这个代码
"""

from http.server import BaseHTTPRequestHandler
import json
import akshare as ak
import pandas as pd
from datetime import datetime

def handler(request, response):
    """Vercel Serverless Function 入口"""
    
    # 设置响应头
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # 处理OPTIONS请求（CORS预检）
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        print("开始获取数据...")
        
        # 1. 获取沪深300指数
        index_data = ak.stock_zh_index_spot_sina()
        hs300 = index_data[index_data['代码'] == 'sh000300']
        
        hs300_price = None
        if not hs300.empty:
            hs300_price = float(hs300['最新价'].values[0])
        
        # 2. 获取沪深300市盈率
        pe_data = ak.index_value_hist_funddb(symbol="沪深300")
        latest_pe = None
        if not pe_data.empty:
            latest_pe = float(pe_data.iloc[-1]['市盈率PE'])
        
        # 3. 获取国债收益率
        bond_data = ak.bond_china_yield()
        ten_year = bond_data[bond_data['期限'] == '10年']
        bond_yield = None
        if not ten_year.empty:
            bond_yield = float(ten_year.iloc[-1]['收益率'])
        
        # 4. 计算指标
        earnings_yield = None
        stock_bond_spread = None
        if latest_pe and latest_pe > 0:
            earnings_yield = (1 / latest_pe) * 100
            if bond_yield:
                stock_bond_spread = earnings_yield - bond_yield
        
        # 构建响应数据
        result = {
            "success": True,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": {
                "hs300_price": hs300_price,
                "hs300_pe": latest_pe,
                "bond_yield_10y": bond_yield,
                "earnings_yield": earnings_yield,
                "stock_bond_spread": stock_bond_spread
            }
        }
        
        print("数据获取成功")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(result, ensure_ascii=False)
        }
        
    except Exception as e:
        print(f"错误: {str(e)}")
        
        error_result = {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps(error_result, ensure_ascii=False)
        }
