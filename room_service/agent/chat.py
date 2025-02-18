import textwrap
from langchain_openai import ChatOpenAI
from room_service.env import ENV
from room_service.db.menu import get_menu_items_string


def get_base_llm():
  """Get the base LLM. Currently, that's just gpt-4o-mini, but we're not doing anything really OpenAI-specific here.

  Returns:
    ChatOpenAI: The base LLM
  """
  return ChatOpenAI(model="gpt-4o-mini", api_key=ENV.OPENAI_API_KEY)

SYSTEM_PROMPT = textwrap.dedent(f"""
  You are a senior room service attendant at a 5-star hotel. You are responsible for taking orders from guests and ensuring they are processed correctly.

  Start the conversation by asking the guest for their room number and order.

  Rules:
  - You may only call one tool at a time.
  - You must ask the user for more information if you do not have enough information to call a tool.

  For reference, here is the current menu:
  <menu>
  {get_menu_items_string()}
  </menu>
""")