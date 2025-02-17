"""Mock external Room Service API for order processing."""

import random
import time

import pydantic

from room_service.db.orders import get_order_id
from room_service.models.order import BadOrderResponse, GoodOrderResponse, Order, OrderResponse
from room_service.util import calculate_order_details

class RoomServiceAPIError(Exception):
  """Base exception for Room Service API errors."""
  pass

class KitchenOverloadedError(RoomServiceAPIError):
  """Exception for when the kitchen is overloaded."""
  pass

class RoomServiceAPI:
  """Mock external Room Service API.
  
  This simulates an external service that would process room service orders.
  In a real implementation, this would make HTTP requests to an actual API.
  """
  
  def __init__(self, simulate_failures: bool = False, simulate_latency: bool = True):
    """Initialize the Room Service API.
    
    Args:
      simulate_failures: If True, randomly simulate API failures
      simulate_latency: If True, simulate network latency
    """
    self._simulate_failures = simulate_failures
    self._simulate_latency = simulate_latency
    
  def _simulate_network_latency(self):
    """Simulate network latency if enabled."""
    if self._simulate_latency:
      time.sleep(random.uniform(0.1, 0.5))

  def _simulate_failure_events(self):
    """Simulate failure events if enabled. These can be API errors or bad responses."""
  
    # Simulate random failures if enabled
    if self._simulate_failures and random.random() < 0.1:
      raise RoomServiceAPIError("Failed to connect to Room Service API")
    
    # Simulate kitchen overload
    if self._simulate_failures and random.random() < 0.05:
      raise KitchenOverloadedError("Kitchen is currently at capacity. Please try again in 15 minutes.")

  def place_order(self, order: Order) -> OrderResponse:
    """Place a room service order.
    
    Args:
      order: The order to place
      
    Returns:
      OrderResponse with status and details
      
    Raises:
      RoomServiceAPIError: If the API fails to process the order
    """
    self._simulate_network_latency()

    try:
      self._simulate_failure_events()
    except RoomServiceAPIError | KitchenOverloadedError as e:
      return BadOrderResponse(message=str(e))
    
    # Generate order ID and calculate delivery time
    order_id = get_order_id()
    order_details = calculate_order_details(order.items)

    # Successful order
    return GoodOrderResponse(
      order_id=order_id,
      message="Order successfully placed",
      estimated_delivery_time_minutes=order_details.max_preparation_time,
      total_price=order_details.total_price
    )