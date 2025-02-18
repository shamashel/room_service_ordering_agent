"""Tests for the OrderPlacerTool."""

import pytest
from langchain_core.messages import ToolMessage
from room_service.tools.order_placer import OrderPlacerTool
from room_service.models.order import Order, OrderItem, GoodOrderResponse, BadOrderResponse
from room_service.models.order_validation import (
  OrderValidationResult, 
  ValidationDetails,
  ValidItem
)
from room_service.models.general import Status
from room_service.models.state import OrderState
from room_service.services.room_service_api import RoomServiceAPI

class MockRoomServiceAPI(RoomServiceAPI):
  """Mock API for testing."""
  def __init__(self, response: GoodOrderResponse | BadOrderResponse):
    self.response = response
    
  def place_order(self, order: Order) -> GoodOrderResponse | BadOrderResponse:
    return self.response

def create_test_state(validated_order: Order | None = None, validation_result: OrderValidationResult | None = None) -> OrderState:
  """Helper to create a test state dictionary."""
  return {
    "messages": [],
    "validated_order": validated_order,
    "validation_result": validation_result,
    "sequential_error_count": 0
  }

def test_place_order_success():
  """Test successful order placement."""
  order = Order(
    room=101,
    items=[
      OrderItem(name="Club Sandwich", quantity=1)
    ]
  )
  
  validation_result = OrderValidationResult(
    status=Status.SUCCESS,
    response="Order validated successfully",
    details=ValidationDetails(
      valid_room="101",
      valid_items=[
        ValidItem(
          name="Club Sandwich",
          valid_quantity=1,
          valid_modifications=[]
        )
      ]
    ),
    total_price="$15.00",
    preparation_time=15
  )
  
  mock_response = GoodOrderResponse(
    status=Status.SUCCESS,
    message="Order successfully placed",
    order_id="ORDER123",
    estimated_delivery_time_minutes=15,
    total_price="$15.00"
  )
  
  placer = OrderPlacerTool()
  placer.api = MockRoomServiceAPI(mock_response)
  
  result = placer._run(
    tool_call_id="test-123",
    state=create_test_state(order, validation_result)
  )
  
  assert result.update is not None
  assert len(result.update["messages"]) == 1
  message = result.update["messages"][0]
  assert isinstance(message, ToolMessage)
  assert "ORDER123" in message.content
  assert "15 minutes" in message.content
  assert message.tool_call_id == "test-123"

def test_place_order_failure():
  """Test failed order placement."""
  order = Order(
    room=101,
    items=[
      OrderItem(name="Club Sandwich", quantity=1)
    ]
  )
  
  validation_result = OrderValidationResult(
    status=Status.SUCCESS,
    response="Order validated successfully",
    details=ValidationDetails(
      valid_room="101",
      valid_items=[
        ValidItem(
          name="Club Sandwich",
          valid_quantity=1,
          valid_modifications=[]
        )
      ]
    ),
    total_price="$15.00",
    preparation_time=15
  )
  
  mock_response = BadOrderResponse(
    status=Status.ERROR,
    message="Kitchen is currently overloaded"
  )
  
  placer = OrderPlacerTool()
  placer.api = MockRoomServiceAPI(mock_response)
  
  result = placer._run(
    tool_call_id="test-123",
    state=create_test_state(order, validation_result)
  )
  
  assert result.update is not None
  assert len(result.update["messages"]) == 1
  message = result.update["messages"][0]
  assert isinstance(message, ToolMessage)
  assert "Kitchen is currently overloaded" in message.content
  assert message.tool_call_id == "test-123"

def test_place_order_without_validation():
  """Test that attempting to place an order without validation raises an error."""
  placer = OrderPlacerTool()
  
  with pytest.raises(ValueError) as exc_info:
    placer._run(
      tool_call_id="test-123",
      state=create_test_state()
    )
  
  assert "no validated order in state" in str(exc_info.value)

def test_place_order_without_validation_result():
  """Test that attempting to place an order without validation result raises an error."""
  order = Order(
    room=101,
    items=[
      OrderItem(name="Club Sandwich", quantity=1)
    ]
  )
  
  placer = OrderPlacerTool()
  
  with pytest.raises(ValueError) as exc_info:
    placer._run(
      tool_call_id="test-123",
      state=create_test_state(validated_order=order)
    )
  
  assert "no validated order in state" in str(exc_info.value) 