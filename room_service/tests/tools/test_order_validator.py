from room_service.tools.order_validator import OrderValidatorTool
from room_service.models.order import OrderItem
from room_service.models.order_validation import InvalidItemReasons

def test_validate_room_valid_numbers():
  """Test that valid room numbers are correctly validated."""
  validator = OrderValidatorTool()

  # Test valid room numbers on different floors
  assert validator._validate_room(101) is True  # Room 1 on floor 1
  assert validator._validate_room(220) is True  # Room 20 on floor 2
  assert validator._validate_room(315) is True  # Room 15 on floor 3

  # Test edge cases
  assert validator._validate_room(100) is True  # Room 0 on floor 1
  assert validator._validate_room(320) is True  # Room 20 on floor 3 (max valid room)

def test_validate_room_invalid_numbers():
  """Test that invalid room numbers are correctly rejected."""
  validator = OrderValidatorTool()

  # Test rooms with numbers too high
  assert validator._validate_room(199) is False  # Room 99 on floor 1
  assert validator._validate_room(121) is False  # Room 21 on floor 1

  # Test edge cases and invalid inputs
  assert validator._validate_room(-101) is False  # Negative room number
  assert validator._validate_room(0) is False    # No floor number
  assert validator._validate_room(99) is False   # Invalid floor format 
  assert validator._validate_room(425) is False  # Floor 4 doesn't exist

def test_validate_item_valid():
  """Test that valid items are correctly validated."""
  validator = OrderValidatorTool()

  # Test basic item with no modifications
  result = validator._validate_item(OrderItem(name="Still Water", quantity=1))
  assert result.is_valid is True
  assert result.valid_item is not None
  assert result.valid_item.name == "Still Water"
  assert result.valid_item.valid_quantity == 1
  assert result.valid_item.valid_modifications == []
  assert result.invalid_item is None

  # Test item with valid modifications
  result = validator._validate_item(
    OrderItem(name="Club Sandwich", quantity=2, modifications=["extra bacon", "no tomato"])
  )
  assert result.is_valid is True
  assert result.valid_item is not None
  assert result.valid_item.name == "Club Sandwich"
  assert result.valid_item.valid_quantity == 2
  assert set(result.valid_item.valid_modifications) == {"extra bacon", "no tomato"}
  assert result.invalid_item is None

def test_validate_item_not_on_menu():
  """Test validation of items that aren't on the menu."""
  validator = OrderValidatorTool()

  result = validator._validate_item(OrderItem(name="InvalidItem", quantity=1))
  assert result.is_valid is False
  assert result.valid_item is None
  assert result.invalid_item is not None
  assert result.invalid_item.name == "InvalidItem"
  assert result.invalid_item.reason == InvalidItemReasons.NOT_ON_MENU

def test_validate_item_invalid_quantity():
  """Test validation of items with invalid quantities."""
  validator = OrderValidatorTool()

  # Order more than available
  result = validator._validate_item(OrderItem(name="French Fries", quantity=100))
  assert result.is_valid is False
  assert result.valid_item is None
  assert result.invalid_item is not None
  assert result.invalid_item.name == "French Fries"
  assert result.invalid_item.reason == InvalidItemReasons.OUT_OF_STOCK
  assert result.invalid_item.valid_quantity == 5  # French Fries has available_quantity=5

def test_validate_item_modifications_not_allowed():
  """Test validation of items with modifications that do not allow modifications."""
  validator = OrderValidatorTool()

  # Test modifications on non-modifiable item
  result = validator._validate_item(
    OrderItem(name="Still Water", quantity=1, modifications=["extra ice"])
  )
  assert result.is_valid is False
  assert result.valid_item is None
  assert result.invalid_item is not None
  assert result.invalid_item.name == "Still Water"
  assert result.invalid_item.valid_quantity == 1
  assert result.invalid_item.reason == InvalidItemReasons.MODIFICATIONS_NOT_ALLOWED
  assert result.invalid_item.valid_modifications is None
  assert result.invalid_item.invalid_modifications is not None
  assert set(result.invalid_item.invalid_modifications) == {"extra ice"}

def test_validate_item_invalid_modifications():
  """Test validation of items with invalid modifications."""
  validator = OrderValidatorTool()

  # Test invalid modification on modifiable item
  result = validator._validate_item(
    OrderItem(name="Club Sandwich", quantity=1, modifications=["add pineapple"])
  )
  assert result.is_valid is False
  assert result.valid_item is None
  assert result.invalid_item is not None
  assert result.invalid_item.name == "Club Sandwich"
  assert result.invalid_item.valid_quantity == 1
  assert result.invalid_item.reason == InvalidItemReasons.INVALID_MODIFICATIONS
  assert result.invalid_item.invalid_modifications is not None
  assert set(result.invalid_item.invalid_modifications) == {"add pineapple"}