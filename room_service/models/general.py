

from enum import Enum


class Status(str, Enum):
    """Represents the status of a tool call."""
    SUCCESS = "Success"
    ERROR = "Error"