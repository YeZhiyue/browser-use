import asyncio
from browser_use import Agent, Controller
from browser_use.llm import ChatGoogle
from pydantic import BaseModel
from typing import List, Dict, Optional
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

# Define the output format as a Pydantic model
class OrderDetail(BaseModel):
	arrival_time: Optional[str] = None  # 使用Optional，允许为空
	hs_code: Optional[str] = None
	product_description: Optional[str] = None
	amount_usd: Optional[float] = None

class CompanyInfo(BaseModel):
	company_name: str
	info_url: str
	order_history: List[OrderDetail]


class CompanyInfos(BaseModel):
	posts: List[CompanyInfo]


controller = Controller(output_model=CompanyInfos)

# - ABID TRADING
# - RUKNUSSIHALAH EST

async def main():
	task = """
	
按照以下工作流去提取公司列表中的每个公司的提单详情信息，但只提取每个公司结果页面的第一个公司信息。

公司列表（已进行 URL 编码）：
- https://crm.xiaoman.cn/new_discovery/mining-v2/list?filter={"keyword":"MITTAL%20REFRIGERATIONS","keywordOperator":"OR","countryCode":[]}
- https://crm.xiaoman.cn/new_discovery/mining-v2/list?filter={"keyword":"ABID%20TRADING","keywordOperator":"OR","countryCode":[]}
- https://crm.xiaoman.cn/new_discovery/mining-v2/list?filter={"keyword":"RUKNUSSIHALAH%20EST","keywordOperator":"OR","countryCode":[]}
- https://crm.xiaoman.cn/new_discovery/mining-v2/list?filter={"keyword":"P%20L%20PRODUCTS","keywordOperator":"OR","countryCode":[]}
- https://crm.xiaoman.cn/new_discovery/mining-v2/list?filter={"keyword":"CADWARE%20SDN","keywordOperator":"OR","countryCode":[]}
- https://crm.xiaoman.cn/new_discovery/mining-v2/list?filter={"keyword":"AIK%20SENG%20INDUSTRIES%20SDN","keywordOperator":"OR","countryCode":[]}
- https://crm.xiaoman.cn/new_discovery/mining-v2/list?filter={"keyword":"C%20A%20SOI%20%26%20CORPORATE","keywordOperator":"OR","countryCode":[]}

对于列表中的每个 URL，执行以下步骤：

1.  打开 URL。
2.  选择列表中第一个公司点击，右侧会弹出公司详情，在详情中继续执行下面操作
3.  **提取数据:**
    *   在右侧面板中，向下滚动，直到找到标题为 "贸易数据(239)" 的选项卡，点击该选项卡。
    *   继续向下滚动，找到标题为 "提单详情(只显示最近1万条记录)" 的表格。
    *   在表格的下方，找到 "10条/页" 的下拉菜单，选择 "100条/页"。
    *   从该表格中，提取**第一条**记录的以下信息：
        *   **到港时间:** 提取到港日期。
        *   **供应商名称:** 提取供应商名称。
        *   **HS编码:** 提取 HS 编码。
        *   **产品描述:** 提取产品描述。
        *   **金额(美元):** 提取美元金额。
4.  **处理分页:**  忽略分页。
5.  **保存数据:** 将提取的信息保存为结构化的数据格式。

[
    {
        "arrival_time": "2019-03-16",
        "supplier_name": "...",
        "hs_code": "84818050",
        "product_description": "SOLENOID VALVE F64-3 3/8 (50 PCS) (USE FOR REFRIGERATOR)",
        "amount_usd": "411"
    }
]

对于每个URL，都生成上述格式的一个列表。
	"""

	# - ABID TRADING
	# - RUKNUSSIHALAH EST

	model = ChatGoogle(model='gemini-2.0-flash', api_key=google_api_key)
	agent = Agent(
		task=task, llm=model,
		controller=controller,
		use_vision=True
	)

	history = await agent.run()

	result = history.final_result()

	# 打印原始结果
	print("Raw Result from Agent:")
	print(result)

	if result:
		parsed: CompanyInfos = CompanyInfos.model_validate_json(result)

		# 创建一个列表来存储公司信息
		company_data = []
		for post in parsed.posts:
			company_data.append({
				'Company Name': post.company_name,
				'Info URL': post.info_url,
				'Order History': post.order_history  # 直接存储OrderDetail列表
			})

		# 打印解析后的数据
		print("\nParsed Company Data:")
		for company in company_data:
			print(company)

		# 将数据转换为 pandas DataFrame
		# 首先将OrderDetail对象转换为字典
		df_data = []
		for company in company_data:
			for order in company['Order History']:
				df_data.append({
					'Company Name': company['Company Name'],
					'Info URL': company['Info URL'],
					'Arrival Time': order.arrival_time,
					'HS Code': order.hs_code,
					'Product Description': order.product_description,
					'Amount (USD)': order.amount_usd
				})
		df = pd.DataFrame(df_data)


		# 获取当前时间
		now = datetime.now()
		timestamp = now.strftime("%Y%m%d_%H%M%S")

		# 构建导出路径和文件名
		download_path = os.path.expanduser("~/Downloads")
		filename = f"company_info_{timestamp}.xlsx"
		filepath = os.path.join(download_path, filename)

		# 将 DataFrame 导出到 Excel 文件
		df.to_excel(filepath, index=False)

		print(f'\nData exported to {filepath}')
	else:
		print('No result')


if __name__ == '__main__':
	asyncio.run(main())
