import asyncio
import os
import sys

from browser_use.llm.openai.chat import ChatOpenAI
from browser_use.llm.openai.chat import ChatOpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()


from browser_use import Agent, ChatGoogle

# Initialize the model
llm = ChatGoogle(
	model='gemini-2.0-flash',
)


task = '帮我打开小红书官网'
agent = Agent(task=task, llm=llm)


async def main():
	await agent.run()


if __name__ == '__main__':
	asyncio.run(main())
