# Room Service Ordering Agent

## Overview

This is a simple agent that can be used to order food in a hotel room. It uses a combination of a language model and a set of tools to validate the order and place it.

When a requested order is invalid, such as an item not being on the menu or modifications not being available, the agent will come up an alternative through the `MenuSuggestionsService` and then suggest the replacements to the user.

This was built as part of a coding challenge for [Clara AI](https://claralabs.com/), check them out for a crazy good AI executive assistant.

## Project Structure

- `pyproject.toml`: Project configuration file.
- `room_service/`: Contains the main application code.
- `room_service/db/menu.py`: Contains the hardcoded menu items.
- `tests/`: Contains the test suite.
- `specifications/`: A directory containing the original challenge requirements, a flow diagram, and example validation paths

## Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/) (Ensure you have Poetry installed)

## Installation

Clone the repository and install the dependencies with Poetry:

```bash
poetry install
```

## Environment Variables

Only one environment variable is required, `OPENAI_API_KEY`. This can be set in the `.env` file, see the `.env.example` file for an example.

## Running the Application

To start the Room Service Ordering Agent, run:

```bash
poetry run python ./room_service/main.py
```

**NOTES**:

- You can find a copy of the full menu in the `room_service/db/menu.py` file or in the `specifications/requirements.md` file.
- When testing order remediation through the `MenuSuggestionsService`, you may need to insist that the agent run through validation regardless of what it thinks. This is because the menu is fed into the system prompt, so the agent may already be aware that an item is invalid before validation is actually run.
  - The purpose of additional validations is specifically because the user can insist an item is available and the agent will believe them.
- The chat will run indefinitely until you stop it with "exit" or `CTRL+C`.

## Example Usage

Happy Path:

```bash
User: Could I please have one Club Sandwich with no modifications for room 115?
... # Bunch of logs
Assistant: ... # Confirming Validated Order
User: Yes, please place the order.
... # Bunch of logs
Assistant: ... # Returns Order ID
```

Basic Corrections Path:

```bash
User: I would like to place another order, this time for room 213. They would like one Caesar Salad with no croutons and one Diet Coke.
... # Bunch of logs
Assistant: ... # Suggests alternative to Diet Coke as it's not on the menu
User: No problem, could I have a Sparkling Water instead?
... # Bunch of logs
Assistant: ... # Confirming Validated Order
User: Yes, please place the order.
... # Bunch of logs
Assistant: ... # Returns Order ID
```

## Running Tests

To run the tests, execute:

```bash
poetry run pytest
```
