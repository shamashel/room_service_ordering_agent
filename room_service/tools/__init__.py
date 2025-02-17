from langchain.tools import BaseTool
from room_service.tools.order_placer import OrderPlacerTool
from room_service.tools.order_validator import OrderValidatorTool

TOOLS = [
  OrderValidatorTool(),
  OrderPlacerTool(),
]

def get_tool_by_name(name: str) -> BaseTool:
  for tool in TOOLS:
    if tool.name == name:
      return tool
  raise ValueError(f"Tool with name {name} not found")
