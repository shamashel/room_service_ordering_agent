
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.types import Command
from room_service.agent.chat import LLM_WITH_TOOLS, SYSTEM_PROMPT
from room_service.models.state import OrderState
from room_service.tools import get_tool_by_name
from langgraph.prebuilt.tool_node import _get_state_args

def llm_call_node(state: OrderState):
  """Call the LLM with the current state."""
  response = LLM_WITH_TOOLS.invoke([
    SystemMessage(content=SYSTEM_PROMPT),
    *state["messages"]
  ])
  return {
    "messages": [
      response
    ]
  }

def should_call_tool(state: OrderState):
  """Determine if tools need to be called.
  
  Assumptions:
  - This node is only called after `llm_call_node`
  - The last message is an AIMessage with tool calls (as a result of the above assumption)
  """
  last_message = state["messages"][-1]
  assert isinstance(last_message, AIMessage), "`should_call_tool` must be called after `llm_call_node`"
  return bool(last_message.tool_calls)

def tool_node(state: OrderState):
  """Call the tool with the current state.
  
  Assumptions:
  - This node is only called after `llm_call_node` and `should_call_tool`
  - The last message is an AIMessage with tool calls (as a result of the above assumption)
  - All tools return a Command
  """
  last_message = state["messages"][-1]
  assert isinstance(last_message, AIMessage), "`tool_node` must be called after `llm_call_node`"
  result: list[Command] = []
  for tool_call in last_message.tool_calls:
    tool = get_tool_by_name(tool_call["name"])
    state_args = _get_state_args(tool)
    try:
      response = tool.invoke({**state_args, **tool_call["args"]})
      assert isinstance(response, Command), "Tool must return a Command"
      result.append(response)
    except Exception as e:
      response = Command(update={"messages": [f"Error: {e}"]})
      result.append(response)
  return result
