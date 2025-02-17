"""Pydantic models for placing and tracking orders."""

from pydantic import BaseModel, Field

class OrderItem(BaseModel):
  """Represents an item in an order. Should correspond to a menu item."""
  name: str = Field(..., description="Name of the menu item being ordered")
  quantity: int = Field(..., gt=0, description="Quantity of the item")
  modifications: list[str] = Field(default_factory=list, description="List of modifications requested")

class Order(BaseModel):
  """Represents a complete room service order."""
  room: int = Field(ge=100, le=399, description="Room number")
  items: list[OrderItem] = Field(..., min_length=1, description="List of items in the order")