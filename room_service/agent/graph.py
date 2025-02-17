from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from room_service.agent.nodes import llm_call_node, tool_node, should_call_tool
from room_service.models.state import OrderState

def create_graph() -> CompiledStateGraph:
  """Create the state graph for the room service agent.
  
  The graph follows this flow:
  1. LLM generates a response/action
  2. Check if tools need to be called
  3. If yes, call tools and loop back to LLM
  4. If no, end conversation
  """
  # Create graph with OrderState
  workflow = StateGraph(OrderState)

  # Add the LLM node that generates responses
  workflow.add_node("llm", llm_call_node)

  # Add the tool execution node
  workflow.add_node("tools", tool_node)

  # Add conditional edges
  workflow.add_conditional_edges(
    "llm",
    should_call_tool,
    {
      True: "tools",  # If tools needed, go to tools node
      False: END,     # If no tools needed, return response to user
    }
  )

  # Connect tools back to LLM to continue conversation
  workflow.add_edge("tools", "llm")

  # Set the entry point
  workflow.set_entry_point("llm")

  return workflow.compile()
