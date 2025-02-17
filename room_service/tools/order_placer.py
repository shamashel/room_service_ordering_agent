from typing import Annotated
from langchain.tools import BaseTool
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langgraph.prebuilt.tool_node import InjectedState
from langgraph.types import Command
from room_service.services.room_service_api import RoomServiceAPI
from room_service.models.order import GoodOrderResponse
from room_service.models.state import OrderState

class OrderPlacerTool(BaseTool):
  """LangChain tool for placing a validated order with the room service system."""

  name = "order_placer"
  description = "Places a validated order with the room service system. Any order should first be validated with the `order_validator` tool and then confirmed by the user."
  
  def __init__(self):
    super().__init__()
    self.api = RoomServiceAPI()
  
  def _run(self, tool_call_id: Annotated[str, InjectedToolCallId], state: Annotated[OrderState, InjectedState]) -> Command:
    if not state["validated_order"] or not state["validation_result"]:
      raise ValueError("Cannot place order - no validated order in state. Ensure the order has been validated with the `order_validator` tool.")
      
    result = self.api.place_order(state["validated_order"])
    if isinstance(result, GoodOrderResponse):
      return Command(
        update={
          "messages": [
            ToolMessage(content=f"Order placed successfully. Inform the user of their order ID {result.order_id} and estimated delivery time of {result.estimated_delivery_time_minutes} minutes.", tool_call_id=tool_call_id)
          ]
        }
      )
    else:
      return Command(
        update={
          "messages": [
            ToolMessage(content=f"Order failed to place with error: {result.message}.", tool_call_id=tool_call_id)
          ]
        }
      )
