from typing import Annotated, Optional, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from room_service.models.order import Order
from room_service.models.order_validation import OrderValidationResult

class OrderState(TypedDict):
  messages: Annotated[Sequence[BaseMessage], add_messages]
  validated_order: Optional[Order]
  validation_result: Optional[OrderValidationResult]
  sequential_error_count: int