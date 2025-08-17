import asyncio
import os
import sys
from dotenv import load_dotenv
from browser_use import Agent, ChatGoogle

load_dotenv()

# 从环境变量中读取账号密码 (推荐方式)
XIAOMAN_USERNAME = os.environ.get("XIAOMAN_USERNAME")
XIAOMAN_PASSWORD = os.environ.get("XIAOMAN_PASSWORD")

# 如果没有设置环境变量，则使用提供的账号密码 (仅用于演示，不推荐)
if not XIAOMAN_USERNAME:
	XIAOMAN_USERNAME = "admin_1092@xiaoman.smart"
if not XIAOMAN_PASSWORD:
	XIAOMAN_PASSWORD = "0654aw"

# 初始化模型
llm = ChatGoogle(model='gemini-2.0-flash')

task = '''
帮我进行如下操作：

打开下面两个页面大致浏览信息：
工具：https://crm.xiaoman.cn/new_discovery/mining-v2

公司列表：
MITTAL REFRIGERATIONS
ABID TRADING
RUKNUSSIHALAH EST

工作流：
1. 逐个公司名称信息
2. 打开工具，选择公司名称输入搜索框搜索
3. 选择搜索到的第一个选项点击进入详情
4. 下拉详情找到 提单详情 信息，拉取数据
'''
agent = Agent(task=task, llm=llm)

async def main():
	# 在 Agent 运行前，将账号密码传递给 Agent
	agent.username = XIAOMAN_USERNAME
	agent.password = XIAOMAN_PASSWORD
	await agent.run()

if __name__ == '__main__':
	asyncio.run(main())
