from typing import Annotated, Type
from langchain.tools import BaseTool
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langgraph.prebuilt.tool_node import InjectedState
from langgraph.types import Command
from pydantic import BaseModel, Field
from room_service.services.room_service_api import RoomServiceAPI
from room_service.models.order import GoodOrderResponse
from room_service.models.state import OrderState
import logging

logger = logging.getLogger(__name__)

class OrderPlacerSchema(BaseModel):
  """Schema for the Order Placer tool."""
  tool_call_id: Annotated[str, InjectedToolCallId]
  state: Annotated[OrderState, InjectedState]

class OrderPlacerTool(BaseTool):
  """LangChain tool for placing a validated order with the room service system."""

  name: str = "order_placer"
  description: str = "Only call this tool if the order has already been validated and the user has confirmed the order."
  args_schema: Type[BaseModel] = OrderPlacerSchema
  api: RoomServiceAPI = Field(default_factory=RoomServiceAPI)

  def __init__(self):
    super().__init__()

  def _run(self, tool_call_id: Annotated[str, InjectedToolCallId], state: Annotated[OrderState, InjectedState]) -> Command:
    """Run order placement.

    Args:
      tool_call_id: The tool call ID
      state: The state of the order

    Returns:
      Command: A command to update the state with the order placement result
    """
    logger.info(f"Attempting to place order for tool call id: {tool_call_id}")
    validated_order, validation_result = state.get("validated_order"), state.get("validation_result")
    if not validated_order or not validation_result:
      raise ValueError("Cannot place order - no validated order in state. Ensure the order has been validated with the `order_validator` tool.")

    logger.info(f"Placing order for tool call id {tool_call_id}: {validated_order}")
    result = self.api.place_order(validated_order)
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
