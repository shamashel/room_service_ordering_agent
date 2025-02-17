"""Mocking a database for orders. This should be behind a real room_service_api, but that's mocked for now too.

Not actually storing orders, just a counter for now."""

ORDER_COUNTER = 0

def get_order_id() -> str:
  """Get a new order ID."""
  global ORDER_COUNTER
  ORDER_COUNTER += 1
  return f"ORDER-{ORDER_COUNTER:04d}"