from langgraph.prebuilt.chat_agent_executor import AgentState
from typing import Optional
from room_service.models.order import Order
from room_service.models.order_validation import OrderValidationResult

class OrderState(AgentState):
  validated_order: Optional[Order]
  validation_result: Optional[OrderValidationResult]
  user_confirmed: bool