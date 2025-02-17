"""Mocking a database for orders. Not actuallys storing orders, just a counter for now."""
ORDER_COUNTER = 0

def get_order_id() -> str:
  """Get a new order ID."""
  global ORDER_COUNTER
  ORDER_COUNTER += 1
  return f"ORDER-{ORDER_COUNTER:04d}"