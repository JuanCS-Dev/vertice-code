# Base type variables - Domain level

from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)
