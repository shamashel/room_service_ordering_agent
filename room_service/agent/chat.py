import textwrap
from langchain_openai import ChatOpenAI
from room_service.tools import TOOLS
from room_service.env import ENV

TOOL_CALLING_LLM = ChatOpenAI(model="gpt-4o-mini", api_key=ENV.OPENAI_API_KEY).bind_tools(TOOLS)

SYSTEM_PROMPT = textwrap.dedent("""
  You are a senior room service attendant at a 5-star hotel. You are responsible for taking orders from guests and ensuring they are processed correctly.

  Start the conversation by asking the guest for their room number and order.
""")