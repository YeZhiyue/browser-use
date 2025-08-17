import asyncio
from browser_use import Agent, Controller
from browser_use.llm import ChatGoogle
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

# Define the output format as a Pydantic model
class CompanyInfo(BaseModel):
	company_name: str
	info_url: str
	company_order_history: List[str]  # 修改为 List[str]


class CompanyInfos(BaseModel):
	posts: List[CompanyInfo]



controller = Controller(output_model=CompanyInfos)


async def main():
	task = """
按照以下工作流去提取每个公司的提单详情信息：

1. 找到 https://crm.xiaoman.cn/new_discovery/mining-v2 中的 营销产品或者公司名称是什么 的输入框输入公司名称
2. 找到第一个结果点击，会弹出右侧详情页
3. 在右侧详情页中下拉找到提单详情信息（一般会有很多页），如果没找到，就返回步骤1，开始寻找下一家公司
4. 找到 提单详情信息 后将结果记录为字符串，然后返回步骤1，开始寻找下一家公司

公司列表：
- MITTAL REFRIGERATIONS
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
			# 将列表转换为字符串，用分号分隔
			order_history_str = "; ".join(post.company_order_history)
			company_data.append({
				'Company Name': post.company_name,
				'Info URL': post.info_url,
				'Order History': order_history_str  # 存储为字符串
			})

		# 打印解析后的数据
		print("\nParsed Company Data:")
		for company in company_data:
			print(company)

		# 将数据转换为 pandas DataFrame
		df = pd.DataFrame(company_data)

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
