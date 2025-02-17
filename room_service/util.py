from typing import Callable, Iterable, TypeVar

from room_service.db.menu import MENU_ITEMS
from room_service.models.order import OrderDetails, OrderItem
from room_service.models.order_validation import ValidItem



T = TypeVar('T')
 
def partition(pred: Callable[[T], bool], iterable: Iterable[T]) -> tuple[list[T], list[T]]:
  """Partition an iterable into two based on a predicate.

  Args:
    pred: A predicate function
    iterable: An iterable

  Returns:
    A tuple of two lists, the first containing the elements that satisfy the predicate, and the second containing the rest.
  """
  true_list = []
  false_list = []
  for item in iterable:
    if pred(item):
      true_list.append(item)
    else:
      false_list.append(item)
  return true_list, false_list

def calculate_order_details(items: list[ValidItem] | list[OrderItem]) -> OrderDetails:
  """Calculate total price and preparation time for valid items.

  Returns:
    OrderDetails: (total_price, max_preparation_time)
  """
  total_price = 0.0
  max_prep_time = 0

  for item in items:
    assert item.name in MENU_ITEMS, f"Item {item.name} not found in menu when calculating order details. Ensure valid_items only contained validated items."
    menu_item = MENU_ITEMS[item.name]
    max_prep_time = max(max_prep_time, menu_item.preparation_time)

    if isinstance(item, ValidItem):
      total_price += menu_item.price * item.valid_quantity
    else:
      total_price += menu_item.price * item.quantity

  return OrderDetails(f"${total_price:.2f}", max_prep_time)
