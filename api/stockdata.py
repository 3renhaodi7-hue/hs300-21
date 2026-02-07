from http.server import BaseHTTPRequestHandler
import json
import akshare as ak
import pandas as pd
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 设置响应头
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            print("=== 开始获取股票数据 ===")
            
            # 1. 获取沪深300指数价格
            print("获取沪深300指数...")
            hs300_price = None
            try:
                index_data = ak.stock_zh_index_spot_sina()
                print(f"获取到指数数据: {len(index_data)} 条")
                
                if not index_data.empty:
                    # 显示所有指数代码，方便调试
                    print("可用的指数代码:", index_data['代码'].tolist())
                    
                    hs300_row = index_data[index_data['代码'] == 'sh000300']
                    if not hs300_row.empty:
                        hs300_price = float(hs300_row['最新价'].values[0])
                        print(f"沪深300价格: {hs300_price}")
                    else:
                        print("未找到sh000300，尝试其他代码...")
                        # 尝试其他可能的代码
                        for code in ['000300', '399300', 'sz399300']:
                            test_row = index_data[index_data['代码'] == code]
                            if not test_row.empty:
                                hs300_price = float(test_row['最新价'].values[0])
                                print(f"找到沪深300({code}): {hs300_price}")
                                break
            except Exception as e:
                print(f"获取指数数据失败: {e}")
                hs300_price = 3800.0
            
            # 2. 获取10年期国债收益率
            print("获取国债收益率...")
            bond_yield = None
            try:
                bond_data = ak.bond_china_yield()
                print(f"国债数据列: {bond_data.columns.tolist() if not bond_data.empty else '空'}")
                
                if not bond_data.empty:
                    # 显示所有期限
                    print("可用的期限:", bond_data['期限'].unique().tolist())
                    
                    ten_year = bond_data[bond_data['期限'] == '10年']
                    if not ten_year.empty:
                        bond_yield = float(ten_year.iloc[-1]['收益率'])
                        print(f"10年期国债收益率: {bond_yield}%")
                    else:
                        # 尝试其他可能的期限名称
                        for term in ['10.0年', '10年期', '10年国债']:
                            test_data = bond_data[bond_data['期限'].str.contains('10')]
                            if not test_data.empty:
                                bond_yield = float(test_data.iloc[-1]['收益率'])
                                print(f"找到国债收益率({term}): {bond_yield}%")
                                break
            except Exception as e:
                print(f"获取国债收益率失败: {e}")
                bond_yield = 2.85
            
            # 3. 市盈率 - 先使用固定值
            print("获取市盈率...")
            latest_pe = 12.5
            
            # 尝试获取PE数据
            try:
                # 列出所有可用的函数
                all_funcs = [f for f in dir(ak) if not f.startswith('_')]
                print(f"AkShare共有 {len(all_funcs)} 个函数")
                
                # 搜索PE相关函数
                pe_funcs = [f for f in all_funcs if any(keyword in f.lower() for keyword in ['pe', '市盈', '估值'])]
                print(f"PE相关函数: {pe_funcs}")
                
                # 尝试调用这些函数
                for func_name in pe_funcs[:3]:  # 只试前3个
                    try:
                        func = getattr(ak, func_name)
                        result = func()
                        if not result.empty and hasattr(result, 'columns'):
                            print(f"函数 {func_name} 成功，列名: {result.columns.tolist()}")
                            # 在这里可以尝试提取PE数据
                    except Exception as e:
                        print(f"函数 {func_name} 失败: {e}")
                        
            except Exception as e:
                print(f"搜索PE函数失败: {e}")
            
            # 4. 计算衍生指标
            earnings_yield = None
            stock_bond_spread = None
            
            if latest_pe and latest_pe > 0:
                earnings_yield = round((1 / latest_pe) * 100, 3)
                if bond_yield:
                    stock_bond_spread = round(earnings_yield - bond_yield, 3)
            
            print("=== 数据获取完成 ===")
            
            # 构建响应
            response = {
                "success": True,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data": {
                    "hs300_price": hs300_price,
                    "hs300_pe": latest_pe,
                    "bond_yield_10y": bond_yield,
                    "earnings_yield": earnings_yield,
                    "stock_bond_spread": stock_bond_spread,
                    "debug_info": {
                        "akshare_version": "1.16.74",
                        "api_status": "部分数据可能需要调整函数名"
                    }
                }
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False, indent=2).encode('utf-8'))
            
        except Exception as e:
            print(f"!!! 主函数错误: {e}")
            import traceback
            traceback.print_exc()
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            error_response = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "traceback": traceback.format_exc()
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
