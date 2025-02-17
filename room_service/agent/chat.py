import textwrap
from langchain_openai import ChatOpenAI
from room_service.tools import TOOLS

LLM = ChatOpenAI(model="gpt-4o-mini")
LLM_WITH_TOOLS = LLM.bind_tools(TOOLS)
SYSTEM_PROMPT = textwrap.dedent("""
  You are a senior room service attendant at a 5-star hotel. You are responsible for taking orders from guests and ensuring they are processed correctly.

  Start the conversation by asking the guest for their room number and order.
""")