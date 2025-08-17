import asyncio
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from browser_use import Agent, Controller
from browser_use.llm import ChatGoogle
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

# Database configuration
DB_HOST = "localhost"  # Replace with your DB host if not localhost
DB_NAME = "company_data"  # Replace with your DB name
DB_USER = "root"  # Replace with your DB user
DB_PASSWORD = ""  # Replace with your DB password
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Check if the Google API key is set
if not GOOGLE_API_KEY:
	logging.error("GOOGLE_API_KEY is not set in the environment variables. Please set it.")
	exit(1)  # Exit if the API key is not set

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

def fetch_company_data():
	"""Fetches company data with empty history_order_info from the database."""
	connection = None  # Initialize connection to None
	try:
		connection = mysql.connector.connect(host=DB_HOST,
											 database=DB_NAME,
											 user=DB_USER,
											 password=DB_PASSWORD)
		if connection.is_connected():
			db_Info = connection.get_server_info()
			logging.info(f"Connected to MySQL Server version {db_Info}")
			cursor = connection.cursor()
			cursor.execute("SELECT id, company_name, xiaoman_order_info_url FROM company_info WHERE history_order_info IS NULL OR history_order_info = '' LIMIT 100")  # Limit to 100 for testing
			records = cursor.fetchall()
			logging.info(f"Fetched {len(records)} company records from the database.")
			return records
	except Error as e:
		logging.error(f"Error while connecting to MySQL: {e}")
		return []
	finally:
		if connection and connection.is_connected():
			cursor = connection.cursor()
			cursor.close()
			connection.close()
			logging.info("MySQL connection is closed")
		elif connection:
			logging.warning("Connection object exists but is not connected. Attempting to close.")
			try:
				connection.close()
				logging.info("Potentially broken MySQL connection closed.")
			except Exception as e:
				logging.error(f"Failed to close potentially broken MySQL connection: {e}")


def update_company_data(company_id, history_order_info):
	"""Updates the history_order_info in the database."""
	connection = None  # Initialize connection to None
	try:
		connection = mysql.connector.connect(host=DB_HOST,
											 database=DB_NAME,
											 user=DB_USER,
											 password=DB_PASSWORD)
		if connection.is_connected():
			cursor = connection.cursor()
			sql = "UPDATE company_info SET history_order_info = %s WHERE id = %s"
			val = (history_order_info, company_id)
			cursor.execute(sql, val)
			connection.commit()
			logging.info(f"Updated company_id {company_id} with history_order_info")
	except Error as e:
		logging.error(f"Error while updating MySQL: {e}")
	finally:
		if connection and connection.is_connected():
			cursor = connection.cursor()
			cursor.close()
			connection.close()
			logging.info("MySQL connection is closed")
		elif connection:
			logging.warning("Connection object exists but is not connected. Attempting to close.")
			try:
				connection.close()
				logging.info("Potentially broken MySQL connection closed.")
			except Exception as e:
				logging.error(f"Failed to close potentially broken MySQL connection: {e}")


async def process_company(company_id, company_name, xiaoman_order_info_url):
	"""Processes a single company to extract order details."""
	logging.info(f"Processing company_id: {company_id}, company_name: {company_name}")
	task = f"""
    提取公司 {company_name} (URL: {xiaoman_order_info_url}) 的提单详情信息，但只提取每个公司结果页面的第一个公司信息。请将所有输出翻译成中文。

    按照以下工作流提取信息：

    1.  打开 URL: {xiaoman_order_info_url}。
    2.  选择列表中第一个公司点击，右侧会弹出公司详情，在详情中继续执行下面操作
    3.  **提取数据:**
        *   在右侧面板中，向下滚动，直到找到标题为 "贸易数据" 的选项卡，点击该选项卡。
        *   继续向下滚动，找到标题为 "提单详情(只显示最近1万条记录)" 的表格。
        *   在表格的下方，找到 "10条/页" 的下拉菜单，选择 "100条/页"。
        *   从该表格中，提取**第一条**记录的以下信息：
            *   **到港时间:** 提取到港日期。
            *   **HS编码:** 提取 HS 编码。
            *   **产品描述:** 提取产品描述。
            *   **金额(美元):** 提取美元金额。
    4.  **处理分页:**  忽略分页。
    5.  **保存数据:** 将提取的信息保存为结构化的数据格式。

    [
        {{
            "arrival_time": "到港时间",
            "hs_code": "HS编码",
            "product_description": "产品描述",
            "amount_usd": "金额(美元)"
        }}
    ]

    只返回上述格式的一个列表，所有内容必须是中文。
    """

	model = ChatGoogle(model='gemini-2.0-flash', api_key=GOOGLE_API_KEY)
	agent = Agent(
		task=task, llm=model,
		controller=controller,
		use_vision=True
	)

	try:
		history = await agent.run()
		result = history.final_result()

		if result:
			try:
				parsed: CompanyInfos = CompanyInfos.model_validate_json(result)
				order_history_json = parsed.model_dump_json()
				update_company_data(company_id, order_history_json)  # Store JSON string in DB
				logging.info(f"Successfully processed and saved data for company_id: {company_id}")

			except Exception as e:
				logging.error(f"Error parsing result for company_id {company_id}: {e}", exc_info=True)
				update_company_data(company_id, f"Error parsing result: {e}")  # Store error in DB
		else:
			logging.warning(f"No result for company_id: {company_id}")
			update_company_data(company_id, "No result from agent.")  # Store "No result" in DB

	except Exception as e:
		logging.error(f"Error running agent for company_id {company_id}: {e}", exc_info=True)
		update_company_data(company_id, f"Error running agent: {e}")  # Store error in DB


async def main():
	logging.info("Starting the main process...")
	company_data = fetch_company_data()
	if not company_data:
		logging.info("No company data found in the database.")
		return

	# Use a semaphore to limit the number of concurrent tasks
	semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent tasks

	async def limited_process_company(company_id, company_name, xiaoman_order_info_url):
		async with semaphore:
			logging.info(f"Acquired semaphore for company_id: {company_id}")
			try:
				await process_company(company_id, company_name, xiaoman_order_info_url)
			finally:
				logging.info(f"Releasing semaphore for company_id: {company_id}")
				semaphore.release()  # Ensure semaphore is always released

	# Create tasks for each company
	tasks = [limited_process_company(company_id, company_name, xiaoman_order_info_url) for company_id, company_name, xiaoman_order_info_url in company_data]

	# Run tasks concurrently
	logging.info(f"Running {len(tasks)} tasks concurrently...")
	await asyncio.gather(*tasks)

	logging.info("All companies processed.")

if __name__ == '__main__':
	asyncio.run(main())
