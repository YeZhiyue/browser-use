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
任务：从 https://crm.xiaoman.cn/new_discovery/mining-v2 查找以下公司最近1万条记录的提单详情。

公司列表：
- MITTAL REFRIGERATIONS
- ABID TRADING
- RUKNUSSIHALAH EST

提取信息：
- 到港时间
- 供应商名称
- HS编码
- 产品描述
- 金额(美元)

操作步骤：
1. 打开链接。
2. 在公司名称搜索框中输入公司名称。
3. 点击搜索结果中的第一个选项进入详情页。
4. 在详情页中找到“提单详情”部分。
5. 提取指定的信息。
"""
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
