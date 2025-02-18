"""Tool for validating room service orders."""

from typing import Annotated, NamedTuple, Optional, Type
from langchain.tools import BaseTool
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langgraph.types import Command
from pydantic import BaseModel, Field

from room_service.models.general import Status
from room_service.models.order import Order, OrderItem
from room_service.models.order_validation import (
    InvalidItemReason,
    OrderValidationResult,
    ValidationDetails,
    ValidationError,
    ValidItem,
    InvalidItem,
)
from room_service.db.menu import MENU_ITEMS
from room_service.util import calculate_order_details, partition
import logging
from room_service.services.menu_suggestions import MenuSuggestionsService

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
  menu_suggestions_service: MenuSuggestionsService = Field(default_factory=MenuSuggestionsService)

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
          reason=InvalidItemReason.NOT_ON_MENU,
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
          reason=InvalidItemReason.OUT_OF_STOCK,
        ),
      )

    # Check if any modifications are allowed on item
    if item.modifications and not menu_item.modifications_allowed:
      return ItemValidationResult(
        False,
        None,
        InvalidItem(
          name=item.name,
          valid_quantity=item.quantity,
          valid_modifications=[],
          invalid_modifications=item.modifications,
          reason=InvalidItemReason.MODIFICATIONS_NOT_ALLOWED,
        ),
      )

    # Check if provided modifications are valid
    if item.modifications:
      valid_mods, invalid_mods = partition(lambda x: x in menu_item.available_modifications, item.modifications)
      if invalid_mods:
        return ItemValidationResult(
          False,
          None,
          InvalidItem(
            name=item.name,
            valid_quantity=item.quantity,
            valid_modifications=valid_mods,
            invalid_modifications=invalid_mods,
            reason=InvalidItemReason.INVALID_MODIFICATIONS,
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
  
  def _handle_valid_order(self, tool_call_id: Annotated[str, InjectedToolCallId], order: Order, valid_items: list[ValidItem]) -> Command:
    """Handle an order where all items are valid.

    Args:
      tool_call_id: The tool call ID as provided by the tool calling LLM
      order: The order to validate
      valid_items: The valid items in the order

    Returns:
      Command: A command to update the state with the validated order
    """
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
      response=(
        f"The requested order of {items_summary}, will cost {total_price} and can be prepared in approximately {prep_time} minutes. "
        "Inform the user of this and request their confirmation to place this order. "
        "When informing the user, remember to phrase this as a PENDING transaction, as this order has not yet been placed. "
        "The `order_placer` tool may be used to place this order after confirmation."
      ),
      details=details,
      total_price=total_price,
      preparation_time=prep_time,
    )

    return Command(
      update={
        "validated_order": order,
        "validation_result": result,
        "messages": [
          ToolMessage(content=result.model_dump_json(indent=2), tool_call_id=tool_call_id)
        ]
      }
    )
  
  def _handle_invalid_order(self, tool_call_id: Annotated[str, InjectedToolCallId], is_valid_room: bool, order: Order, valid_items: list[ValidItem], invalid_items: list[InvalidItem]) -> Command:
    """Handle an order where the room or some items are invalid.

    Args:
      tool_call_id: The tool call ID as provided by the tool calling LLM
      is_valid_room: Whether the room number is valid
      order: The order to validate
      valid_items: The valid items in the order
      invalid_items: The invalid items in the order

    Returns:
      Command: A command to update the state with the validation result
    """
    details = ValidationError(
      valid_room=str(order.room) if is_valid_room else None,
      invalid_room=str(order.room) if not is_valid_room else None,
      valid_items=valid_items,
      invalid_items=invalid_items,
      suggestions=None,
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

    suggestions = None

    try:
      # Get suggestions and append them to the response if available
      suggestions = self.menu_suggestions_service.get_menu_suggestions(result)
    except Exception as e:
      logger.error("Error getting menu suggestions: %s", e)

    if suggestions is not None and len(suggestions) > 0:
      result = OrderValidationResult(
        status=Status.ERROR,
        response=f"{result.response} Your manager has provided a list of suggestions for remediating this order. Please see the `suggestions` field for more information and inform the user of these options.",
        details=ValidationError(
          valid_room=str(order.room) if is_valid_room else None,
          invalid_room=str(order.room) if not is_valid_room else None,
          valid_items=valid_items,
          invalid_items=invalid_items,
          suggestions=suggestions,
        ),
        total_price=None,
        preparation_time=None,
      )

    return Command(
      update={
        "validation_result": result,
        "validated_order": None,
        "messages": [
          ToolMessage(content=result.model_dump_json(indent=2), tool_call_id=tool_call_id)
        ]
      }
    )

  def _run(self, tool_call_id: Annotated[str, InjectedToolCallId], order: Order) -> Command:
    """Run order validation.

    Args:
      tool_call_id: The tool call ID as provided by the tool calling LLM
      order: The order to validate

    Returns:
      Command: A command to update the state based on the validation results
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
      return self._handle_valid_order(tool_call_id, order, valid_items)
    else:
      return self._handle_invalid_order(tool_call_id, is_valid_room, order, valid_items, invalid_items)