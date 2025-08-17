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

task = '登录小满CRM，并开始进行外贸拓客'  # 修改任务描述
agent = Agent(task=task, llm=llm)

async def main():
	# 在 Agent 运行前，将账号密码传递给 Agent
	agent.username = XIAOMAN_USERNAME
	agent.password = XIAOMAN_PASSWORD
	await agent.run()

if __name__ == '__main__':
	asyncio.run(main())
