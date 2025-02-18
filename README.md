# Room Service Ordering Agent

## Overview

This is a simple agent that can be used to order food in a hotel room. It uses a combination of a language model and a set of tools to validate the order and place it.

This was built as part of a coding challenge for [Clara AI](https://claralabs.com/), check them out for a crazy good AI executive assistant.

## Project Structure

- `room_service/`: Contains the main application code.
- `tests/`: Contains the test suite.
- `pyproject.toml`: Project configuration file.
- `specifications/`: A directory containing the original challenge requirements, a flow diagram, and example validation paths

## Running the Application

To start the Room Service Ordering Agent, run:

```bash
poetry run python ./room_service/main.py
```

## Running Tests

To run the tests, execute:

```bash
poetry run pytest
```
