"""Service for suggesting alternative menu items and modifications."""

import logging
import textwrap
from typing import Optional

from pydantic import BaseModel, Field
from room_service.models.order import OrderItem
from room_service.models.order_validation import (
  OrderValidationResult, 
  InvalidItem,
  InvalidItemReason,
  SingleSuggestion
)
from room_service.db.menu import get_menu_items_string
from room_service.agent.chat import get_base_llm
from room_service.util import partition

logger = logging.getLogger(__name__)


class SuggestionsResponse(BaseModel):
  """Response from the suggestions LLM."""
  suggestions: list[SingleSuggestion] = Field(..., description="A list of suggestions for each invalid item.")

SUGGESTIONS_LLM = get_base_llm().with_structured_output(SuggestionsResponse)

class MenuSuggestionsService:
  """Service for suggesting alternative menu items and modifications."""

  def __init__(self):
    """Initialize the Menu Suggestions Service."""
  
  def _build_suggestions_prompt(self, invalid_items: list[InvalidItem]) -> str:
    """Build the prompt for the suggestions."""
    return textwrap.dedent(f"""
    You are a senior room service manager at a 5-star hotel. Your employees are responsible for taking orders from guests and ensuring they are processed correctly.

    The menu items are as follows:
    
    <menu_items>
    {get_menu_items_string()}
    </menu_items>

    You will be given a series of invalid order items. Please suggest a valid alternative for each item. These suggestions will be given to the employee who took the order.

    If no suggestions are possible, mark that item as "No suggestions available".

    The `reason` field in the invalid item will tell you why the item is invalid.
    - If an item is not on the menu, you should suggest the closest menu item of the same category.
    - If an item is out of stock, you should suggest the closest menu item that is in stock of the same category.
    - If there are invalid modifications, you should suggest the closest modifications for that menu item or suggest no modifications.

    Here are the invalid items:

    <invalid_items>
    {[item.model_dump_json(indent=2) for item in invalid_items]}
    </invalid_items>
    """)

  def get_menu_suggestions(self, validation_result: OrderValidationResult) -> Optional[list[SingleSuggestion]]:
    """Generate suggestions based on validation errors.
    
    Args:
      validation_result: The validation result containing any invalid items
      
    Returns:
      Optional[str]: Suggestion message if applicable, None if no suggestions needed
    """
    if validation_result.status.value == "success":
      return None

    if not isinstance(validation_result.details, dict) or "invalid_items" not in validation_result.details or len(validation_result.details["invalid_items"]) == 0:
      return None

    mods_not_allowed, others = partition(
      lambda item: item.reason == InvalidItemReason.MODIFICATIONS_NOT_ALLOWED,
      validation_result.details["invalid_items"]
    )

    suggestions: list[SingleSuggestion] = []

    for invalid_item in mods_not_allowed:
      # Since we're already in a validation path, not using assert here.
      if invalid_item.valid_quantity is None:
        logger.warning(f"Item with no mods allowed has no valid quantity:\n{invalid_item.model_dump_json(indent=2)}")
        continue

      suggestions.append(SingleSuggestion(
        original_item=invalid_item,
        suggestion="This item does not allow modifications, so please remove the modifications.",
        fixed_item=OrderItem(
          name=invalid_item.name,
          quantity=invalid_item.valid_quantity,
          modifications=[]
        )
      ))

    if len(others) > 0:
      logger.info("Generating suggestions for %d invalid items", len(others))
      prompt = self._build_suggestions_prompt(others)
      response = SUGGESTIONS_LLM.invoke(prompt)

      if not isinstance(response, SuggestionsResponse):
        logger.error("Invalid response from suggestions LLM: %s", response)
        return None

      logger.info("Suggestions generated: %s", response.model_dump_json(indent=2))
      suggestions.extend(response.suggestions)

    return suggestions
