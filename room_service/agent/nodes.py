
import logging
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.graph import END
from langgraph.types import Command
from room_service.agent.chat import TOOL_CALLING_LLM
from room_service.models.state import OrderState
from room_service.tools import get_tool_by_name
from langgraph.prebuilt.tool_node import _get_state_args

logger = logging.getLogger(__name__)
def tool_calling_llm_node(state: OrderState):
  """Call the LLM with the current state."""
  logger.info("Calling Tool Calling LLM")
  response = TOOL_CALLING_LLM.invoke(state["messages"])
  logger.info(f"Tool Calling LLM response: {response}")
  return {
    "messages": [
      response
    ]
  }


TOOL_CALLING_LLM_NODES = {
  "order_validating_llm": tool_calling_llm_node,
}

def should_call_tool(state: OrderState):
  """Determine if tools need to be called.
  
  Assumptions:
  - This node is only called after `llm_call_node`
  - The last message is an AIMessage with tool calls (as a result of the above assumption)
  """
  last_message = state["messages"][-1]
  assert isinstance(last_message, AIMessage), "`should_call_tool` must be called after `llm_call_node`"
  should_call = len(last_message.tool_calls) > 0 if last_message.tool_calls else False
  res = "tools" if should_call else END
  logger.info(f"Should call tool response: {res}")
  return res

def tool_node(state: OrderState):
  """Call the tool with the current state.

  Assumptions:
  - This node is only called after `llm_call_node` and `should_call_tool`
  - The last message is an AIMessage with tool calls (as a result of the above assumption)
  - All tools return a Command
  """
  logger.info("Calling Tool Node")
  last_message = state["messages"][-1]
  assert isinstance(last_message, AIMessage), "`tool_node` must be called after `llm_call_node`"
  result: list[Command] = []
  for tool_call in last_message.tool_calls:
    tool = get_tool_by_name(tool_call["name"])
    state_args = {var: state for var in _get_state_args(tool)}
    try:
      response = tool.invoke({**tool_call, "args": {**state_args, **tool_call["args"]}})
      assert isinstance(response, Command), "Tool must return a Command"
      result.append(response)
      state["sequential_error_count"] = 0
    except Exception as e:
      logger.error(f"Tool {tool_call['name']} raised an error: {e}")
      state["sequential_error_count"] = state.get("sequential_error_count", 0) + 1
      # I'd want actual error handling here, but I don't have time so just crash.
      assert state["sequential_error_count"] < 3, "Unrecoverable error. Please contact the hotel reception and speak with a human representative."
      response = Command(update={"messages": [ToolMessage(content=f"Error: {e}", tool_call_id=tool_call["id"])]})
      result.append(response)
  logger.info(f"Tool node result: {result}")
  return result
