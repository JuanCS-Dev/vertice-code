# JSON serialization types - Domain level

from __future__ import annotations

from typing import Dict, List, Union


JSONValue = Union[str, int, float, bool, None, List["JSONValue"], "JSONDict"]
JSONDict = Dict[str, JSONValue]
