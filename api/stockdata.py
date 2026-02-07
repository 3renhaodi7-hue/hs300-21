from http.server import BaseHTTPRequestHandler
import json
import akshare as ak
import pandas as pd
from datetime import datetime
import sys
import os

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 设置响应头
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            print("开始获取数据...")
            
            # 获取沪深300指数数据
            index_data = ak.stock_zh_index_spot_sina()
            hs300_row = index_data[index_data['代码'] == 'sh000300']
            
            hs300_price = None
            if not hs300_row.empty:
                hs300_price = float(hs300_row['最新价'].values[0])
            
            # 获取沪深300市盈率
            pe_data = ak.index_value_hist_funddb(symbol="沪深300")
            latest_pe = None
            if not pe_data.empty and '市盈率PE' in pe_data.columns:
                latest_pe = float(pe_data.iloc[-1]['市盈率PE'])
            
            # 获取10年期国债收益率
            bond_data = ak.bond_china_yield()
            ten_year = bond_data[bond_data['期限'] == '10年']
            bond_yield = None
            if not ten_year.empty:
                bond_yield = float(ten_year.iloc[-1]['收益率'])
            
            # 计算衍生指标
            earnings_yield = None
            stock_bond_spread = None
            
            if latest_pe and latest_pe > 0:
                earnings_yield = (1 / latest_pe) * 100
                if bond_yield:
                    stock_bond_spread = earnings_yield - bond_yield
            
            # 构建响应
            response = {
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
            
            # 返回 JSON 响应
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            print("数据获取成功")
            
        except Exception as e:
            print(f"错误: {str(e)}")
            import traceback
            traceback.print_exc()
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            error_response = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
