"""Tool for validating room service orders."""

from typing import Annotated, NamedTuple, Optional, Type
from langchain.tools import BaseTool
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langgraph.types import Command
from pydantic import BaseModel

from room_service.models.general import Status
from room_service.models.order import Order, OrderItem
from room_service.models.order_validation import (
    InvalidItemReasons,
    OrderValidationResult,
    ValidationDetails,
    ValidationError,
    ValidItem,
    InvalidItem,
)
from room_service.db.menu import MENU_ITEMS
from room_service.util import calculate_order_details, partition
import logging

logger = logging.getLogger(__name__)

class OrderValidationSchema(BaseModel):
  """Schema for the Order Validator tool."""
  order: Order
  tool_call_id: Annotated[str, InjectedToolCallId]

class ItemValidationResult(NamedTuple):
  """NamedTuple representing the result of validating an order item."""
  is_valid: bool
  valid_item: Optional[ValidItem]
  invalid_item: Optional[InvalidItem]


class OrderValidatorTool(BaseTool):
  """LangChain tool for validating room service orders."""

  name: str = "order_validator"
  description: str = (
      "Validates a room service order against menu items and room constraints. This tool should be called only once per order."
  )
  args_schema: Type[BaseModel] = OrderValidationSchema

  def __init__(self):
    """Initialize the OrderValidatorTool. Explicitly doing this so basedpyright realizes we don't need params."""
    super().__init__()

  def _validate_room(self, room: int) -> bool:
    """Validate the room number.

    We don't have a real list of rooms, so let's assume only rooms 0-20 exist on each floor and that the room number is the floor number times 100 plus the room number on that floor

    Returns:
      bool: Whether the room number is valid
    """
    assert room >= 100 and room <= 399, "Room number must be between 100 and 399. This should have been checked by the Order model, so something is wrong."
    room_number_in_floor = room % 100
    return 0 <= room_number_in_floor <= 20

  def _validate_item(self, item: OrderItem) -> ItemValidationResult:
    """Validate a single order item against the menu.

    Returns:
      Tuple[bool, ValidationItem, InvalidItem]:
        (is_valid, valid_item_if_valid, invalid_item_if_invalid)
    """
    menu_item = MENU_ITEMS.get(item.name)

    # Item not in menu
    if not menu_item:
      return ItemValidationResult(
        False,
        None,
        InvalidItem(
          name=item.name,
          reason=InvalidItemReasons.NOT_ON_MENU,
        ),
      )

    # Item not in stock
    if item.quantity > menu_item.available_quantity:
      return ItemValidationResult(
        False,
        None,
        InvalidItem(
          name=item.name,
          valid_quantity=menu_item.available_quantity,
          invalid_quantity=item.quantity - menu_item.available_quantity,
          reason=InvalidItemReasons.OUT_OF_STOCK,
        ),
      )

    # Check if any modifications are on item
    if item.modifications and not menu_item.modifications_allowed:
      return ItemValidationResult(
        False,
        None,
        InvalidItem(
          name=item.name,
          valid_quantity=item.quantity,
          valid_modifications=[],
          invalid_modifications=item.modifications,
          reason=InvalidItemReasons.MODIFICATIONS_NOT_ALLOWED,
        ),
      )

    # Check if provided modifications are valid
    if item.modifications:
      invalid_mods, valid_mods = partition(lambda x: x in menu_item.available_modifications, item.modifications)
      if invalid_mods:
        return ItemValidationResult(
          False,
          None,
          InvalidItem(
            name=item.name,
            valid_quantity=item.quantity,
            valid_modifications=valid_mods,
            invalid_modifications=invalid_mods,
            reason=InvalidItemReasons.INVALID_MODIFICATIONS,
          ),
        )

    # Item is valid
    return ItemValidationResult(
      True,
      ValidItem(
        name=item.name,
        valid_quantity=item.quantity,
        valid_modifications=item.modifications
      ),
      None,
    )

  def _run(self, tool_call_id: Annotated[str, InjectedToolCallId], order: Order) -> Command:
    """Run order validation.

    Args:
      order: The order to validate

    Returns:
      OrderValidationResult: The validation result
    """
    logger.info(f"Validating order: {order} for tool call id {tool_call_id}")
    # Validate room number
    is_valid_room = self._validate_room(order.room)

    # Validate each item
    valid_items: list[ValidItem] = []
    invalid_items: list[InvalidItem] = []

    # If speed is a concern here, we could use a threadpool to validate items in parallel since they're independent
    for item in order.items:
      is_valid, valid_item, invalid_item = self._validate_item(item)
      if is_valid:
        assert valid_item is not None, "Valid item should not be None when is_valid is True"
        valid_items.append(valid_item)
      else:
        assert invalid_item is not None, "Invalid item should not be None when is_valid is False"
        invalid_items.append(invalid_item)

    # Construct response based on validation results
    if is_valid_room and not invalid_items:
      # All valid - happy path
      total_price, prep_time = calculate_order_details(valid_items)

      details = ValidationDetails(
        valid_room=str(order.room), valid_items=valid_items
      )

      items_summary = ", ".join(
        f"{item.valid_quantity} {item.name}"
        + (
          f" with {', '.join(item.valid_modifications)}"
          if item.valid_modifications
          else ""
        )
        for item in valid_items
      )

      result = OrderValidationResult(
        status=Status.SUCCESS,
        response=f"The requested order of {items_summary}, will cost {total_price} and can be prepared in approximately {prep_time} minutes. Inform the user of this and request their confirmation to place this order. The `order_placer` tool may be used to place this order after confirmation.",
        details=details,
        total_price=total_price,
        preparation_time=prep_time,
      )
      # Order validated, so update validated_order
      return Command(
        update={
          "validated_order": order,
          "validation_result": result,
          "messages": [
            ToolMessage(content=result.model_dump_json(indent=2), tool_call_id=tool_call_id)
          ]
        }
      )
    else:
      # Error path
      details = ValidationError(
        valid_room=str(order.room) if is_valid_room else None,
        invalid_room=str(order.room) if not is_valid_room else None,
        valid_items=valid_items,
        invalid_items=invalid_items,
      )

      error_messages = []
      error_resolutions = []
      if not is_valid_room:
        error_messages.append("Room number is invalid")
        error_resolutions.append("clarify the room number")
      if invalid_items:
        error_messages.append("Some requested items cannot be prepared")
        error_resolutions.append("clarify the items they would like to order")
      result = OrderValidationResult(
        status=Status.ERROR,
        response=f"{'. '.join(error_messages)}. Please ask the user to {'and '.join(error_resolutions)}.",
        details=details,
        total_price=None,
        preparation_time=None,
      )
      # Order not validated, so don't update validated_order
      return Command(
        update={
          "validation_result": result,
          "messages": [
            ToolMessage(content=result.model_dump_json(indent=2), tool_call_id=tool_call_id)
          ]
        }
      )
