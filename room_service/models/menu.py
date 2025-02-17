"""Pydantic models for menu items."""

from pydantic import BaseModel, Field

class MenuItem(BaseModel):
  """Represents an item on the menu."""
  name: str = Field(..., description="Name of the menu item")
  price: float = Field(..., ge=0, description="Base price of the item")
  category: str = Field(..., description="Category of the item (Main, Beverage, Dessert, Side)")
  modifications_allowed: bool = Field(default=False, description="Whether modifications are allowed")
  description: str = Field(..., description="Description of the menu item")
  available_modifications: list[str] = Field(default_factory=list, description="List of allowed modifications")
  allergens: list[str] = Field(default_factory=list, description="List of allergens in the item")
  preparation_time: int = Field(..., ge=0, description="Preparation time in minutes")
  available_quantity: int = Field(..., ge=0, description="Available quantity of the item. Used tracking stock levels.")