"""Pydantic models for placing and tracking orders."""

from typing import NamedTuple
from pydantic import BaseModel, Field

from room_service.models.general import Status

class OrderItem(BaseModel):
  """Represents an item in an order. Should correspond to a menu item."""
  name: str = Field(..., description="Name of the menu item being ordered")
  quantity: int = Field(..., description="Quantity of the item")
  modifications: list[str] = Field(default_factory=list, description="List of modifications requested")

class Order(BaseModel):
  """Represents a complete room service order."""
  room: int = Field(ge=100, le=399, description="Room number")
  items: list[OrderItem] = Field(..., min_length=1, description="List of items in the order. May contain multiple items.")

class OrderDetails(NamedTuple):
  """NamedTuple representing the details of a validated order."""
  total_price: str
  max_preparation_time: int

class GoodOrderResponse(BaseModel):
  """Response from the Room Service API when the order is successful."""
  status: Status = Status.SUCCESS
  message: str
  order_id: str
  estimated_delivery_time_minutes: int
  total_price: str

class BadOrderResponse(BaseModel):
  """Response from the Room Service API when the order is not successful."""
  status: Status = Status.ERROR
  message: str

OrderResponse = GoodOrderResponse | BadOrderResponse