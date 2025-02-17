# LLM Room Service Order Management System

## Overview

In this exercise, you’ll implement a lightweight Python application that processes room service orders via natural-language input, validates them against an in-memory menu and inventory, and submits the confirmed order to a mock API. 

The goal is to demonstrate your ability to interact with an LLM to parse unstructured requests into structured data, handle validation, and then design a system that takes deterministic actions based on these outputs.

## Core Requirements

### **Order Parsing**

* Receive a natural-language request (e.g., “I’d like a club sandwich with extra bacon…”) and prompt an LLM to produce **structured output** conforming to a schema you define.   
* The schema itself and how it is established in code is up to you.  
* The response from the LLM should be validated to verify any returned fields adhere to the schema you’ve defined.

### **Inventory Management**

* Check item availability against an in-memory `INVENTORY` dict / context you create.  
* For unavailable available items within an order, you must initiate a **revision flow**:  
  * Indicate to the user (via a follow-up LLM and/or a static, templated message) which items are unavailable.  
  * Request a potential replacement or confirm removal.  
  * **Note:** It’s only necessary to support a couple well-defined revision paths (for instance, either remove the unavailable item, or suggest a known alternative from the menu).

### **Order Confirmation**

* Once a final list of items is determined, place the order through a mock RoomServiceAPI that simulates sending it to the kitchen.  
* Return or print a success message with any relevant details (e.g., an order ID).

### **Error Handling & Robustness**

* Handle invalid/malformed LLM output gracefully (e.g., missing fields, extra fields, or parse errors).  
* Manage edge cases (e.g., unrecognized items in the user request, invalid room numbers).  
* Decide how to handle continuous re-prompting or fallback if the LLM fails to produce valid data.

### **Optional Extensions**

* Logging and concurrency for multiple orders  
* More expansive revision flow  
* Synthetic data and basic evaluation to test your LLM operations

## Technical Specifications

### **Input**

A natural language input string such as:

`"I'd like a club sandwich with extra bacon, two bottles of still water, and a slice of apple pie to room 312"`

No GUI interface is required. Strings can be provided over CLI.

**Prompt & LLM**

This is left intentionally open-ended. The key considerations here are to provide flexibility in the different LLM models that could be used, and having a guarantee that the LLM returns a valid structured response. There are several Python libraries and guides regarding the generation of structured outputs from LLMs.

**Error Handling**

* **Invalid LLM Output**: If the LLM doesn’t return valid JSON or is missing required fields, handle gracefully (print an error, re-prompt, etc.).  
* **Menu/Inventory Mismatch**: If a user asks for “Chocolate Cake,” which isn’t in `MENU_ITEMS`, you should highlight that it’s unrecognized.  
* **API Failure**: If place\_order returns an error status, show the error message or simulate a fallback.

**Valid Menu**

```py
MENU_ITEMS = {
    # Mains
    "Club Sandwich": {
        "price": 15.00,
        "category": "Main",
        "modifications_allowed": True,
        "description": "Triple-decker sandwich with turkey, crispy bacon, lettuce, tomato, and mayonnaise",
        "available_modifications": ["extra bacon", "no bacon", "toasted", "untoasted", "no tomato", "extra mayo"],
        "allergens": ["gluten", "eggs", "dairy"],
        "preparation_time": 15
    },
    "Caesar Salad": {
        "price": 12.00,
        "category": "Main",
        "modifications_allowed": True,
        "description": "Crisp romaine lettuce, parmesan cheese, croutons, and classic Caesar dressing",
        "available_modifications": ["add chicken", "no croutons", "dressing on side", "add anchovies"],
        "allergens": ["gluten", "eggs", "dairy", "fish"],
        "preparation_time": 10
    },
    "Margherita Pizza": {
        "price": 16.00,
        "category": "Main",
        "modifications_allowed": True,
        "description": "Fresh mozzarella, tomato sauce, and basil on our house-made crust",
        "available_modifications": ["extra cheese", "well done", "gluten-free crust", "add pepperoni"],
        "allergens": ["gluten", "dairy"],
        "preparation_time": 20
    },
    "Beef Burger": {
        "price": 18.00,
        "category": "Main",
        "modifications_allowed": True,
        "description": "8oz Angus beef patty with lettuce, tomato, onion, and special sauce",
        "available_modifications": ["add cheese", "no onion", "well done", "medium rare", "add bacon"],
        "allergens": ["gluten", "eggs", "dairy"],
        "preparation_time": 18
    },

    # Beverages
    "Still Water": {
        "price": 4.00,
        "category": "Beverage",
        "modifications_allowed": False,
        "description": "500ml bottle of premium spring water",
        "available_modifications": [],
        "allergens": [],
        "preparation_time": 2
    },
    "Sparkling Water": {
        "price": 4.00,
        "category": "Beverage",
        "modifications_allowed": False,
        "description": "500ml bottle of premium sparkling mineral water",
        "available_modifications": [],
        "allergens": [],
        "preparation_time": 2
    },
    "Fresh Orange Juice": {
        "price": 6.00,
        "category": "Beverage",
        "modifications_allowed": True,
        "description": "Freshly squeezed orange juice",
        "available_modifications": ["no pulp", "extra pulp"],
        "allergens": [],
        "preparation_time": 5
    },
    "House Red Wine": {
        "price": 12.00,
        "category": "Beverage",
        "modifications_allowed": False,
        "description": "Glass of house Cabernet Sauvignon",
        "available_modifications": [],
        "allergens": ["sulfites"],
        "preparation_time": 3
    },

    # Desserts
    "Apple Pie": {
        "price": 8.00,
        "category": "Dessert",
        "modifications_allowed": True,
        "description": "Warm apple pie with cinnamon and buttery crust",
        "available_modifications": ["add ice cream", "heated", "not heated"],
        "allergens": ["gluten", "dairy"],
        "preparation_time": 8
    },
    "Chocolate Mousse": {
        "price": 9.00,
        "category": "Dessert",
        "modifications_allowed": True,
        "description": "Rich dark chocolate mousse with fresh whipped cream",
        "available_modifications": ["extra whipped cream", "no whipped cream", "add berries"],
        "allergens": ["dairy", "eggs"],
        "preparation_time": 5
    },
    "Fresh Fruit Plate": {
        "price": 7.00,
        "category": "Dessert",
        "modifications_allowed": True,
        "description": "Selection of seasonal fresh fruits",
        "available_modifications": ["no melons", "extra berries"],
        "allergens": [],
        "preparation_time": 7
    },

    # Sides
    "French Fries": {
        "price": 6.00,
        "category": "Side",
        "modifications_allowed": True,
        "description": "Crispy golden fries with sea salt",
        "available_modifications": ["extra crispy", "add truffle oil", "add parmesan"],
        "allergens": [],
        "preparation_time": 10
    },
    "Garden Salad": {
        "price": 7.00,
        "category": "Side",
        "modifications_allowed": True,
        "description": "Mixed greens, cucumber, tomato with house vinaigrette",
        "available_modifications": ["no tomato", "dressing on side", "add avocado"],
        "allergens": [],
        "preparation_time": 5
    }
}
```

What We’re Looking to See

**1\. Code Quality**

* Clean, modular code with functions/classes logically separated.  
* Readable, well-documented, and appropriately commented.  
* Clear error handling and well-chosen data structures and libraries

**2\. System Design**

* Separation of concerns (LLM logic vs. business logic vs. API calls).  
* Extensibility for new models, conversational pathways, or other related functionality  
* One or two diagrams, or control-flow narratives, detailing your choices

**3\. LLM Integration**

* Effective prompt design that yields structured, valid JSON.  
* Basic error recovery for malformed or missing fields.  
* Clear approach to re-prompt or fallback when partial data is received.

**4\. Problem Solving & Edge Cases**

* Demonstrated approach for out-of-stock items, invalid items, and minimal revision flow.  
* Creative or robust handling of user requests, beyond just the happy path.  
* Consideration of performance for large orders (if relevant) or concurrency (optional).