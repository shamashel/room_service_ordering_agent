"""Pydantic models for order validation."""

from enum import Enum
from typing import Optional, TypedDict
from pydantic import BaseModel, Field, field_validator

from room_service.models.general import Status

class ValidItem(BaseModel):
    """Represents a validated order item."""
    name: str = Field(..., description="Name of the menu item")
    valid_modifications: list[str] = Field(default_factory=list, description="List of modifications")
    valid_quantity: int = Field(..., gt=0, description="Quantity of the item")

class InvalidItemReasons(str, Enum):
    """Reasons why an item can be invalid."""
    NOT_ON_MENU = "Item is not on the menu"
    OUT_OF_STOCK = "Item is currently out of stock"
    MODIFICATIONS_NOT_ALLOWED = "This item does not allow modifications"
    INVALID_MODIFICATIONS = "There are invalid modifications in the order"

class InvalidItem(BaseModel):
    """Represents an invalid order item with reason.
    
    This does not inherit from ValidationItem because it's possible no valid modifications and quanitity are present."""
    # ValidationItem fields #
    name: str = Field(..., description="Name of the menu item")
    valid_modifications: Optional[list[str]] = Field(default_factory=list, description="List of modifications that are valid")
    valid_quantity: Optional[int] = Field(default=None, gt=0, description="Quantity of the item that is valid")
    # -------------------- #
    # New Fields #
    reason: InvalidItemReasons = Field(..., description="Reason why the item is invalid")
    invalid_modifications: Optional[list[str]] = Field(default_factory=list, description="List of modifications that are invalid")
    invalid_quantity: Optional[int] = Field(default=None, gt=0, description="Quantity of the item that goes over what we have in stock")
    # -------------------- #

class ValidationDetails(TypedDict):
    """TypedDict representing successful validation details."""
    valid_room: str
    valid_items: list[ValidItem]

class ValidationError(TypedDict):
    """TypedDict representing an error in validation."""
    valid_room: Optional[str]
    valid_items: list[ValidItem]
    invalid_room: Optional[str]
    invalid_items: list[InvalidItem]

class OrderValidationResult(BaseModel):
    """Represents the validation result of an order."""
    status: Status = Field(..., description="Status of validation (Success/Error)")
    response: str = Field(..., description="Human-readable response message")
    details: ValidationDetails | ValidationError = Field(..., description="Validation details including room and items")
    total_price: str | None = Field(default=None, description="Total price of the order (for successful orders)")
    preparation_time: int | None = Field(default=None, ge=0, description="Estimated preparation time in minutes (for successful orders)")

    @field_validator('details')
    @classmethod
    def validate_room_fields(cls, v: ValidationDetails | ValidationError):
        """Validate that either valid_room or invalid_room is present, but not both."""
        valid_room = v.get('valid_room')
        invalid_room = v.get('invalid_room')
        
        if valid_room is not None and invalid_room is not None:
            raise ValueError("Cannot have both valid_room and invalid_room")
        if valid_room is None and invalid_room is None:
            raise ValueError("Must have either valid_room or invalid_room")
        
        return v
