from functools import wraps
import importlib
from typing import Any, List, Mapping
from pydantic import BaseModel

from newhelm.dependency_injection import (
    inject_dependencies,
    serialize_injected_dependencies,
)
from newhelm.secret_values import RawSecrets


class InitializationRecord(BaseModel):
    """Holds data sufficient to reconstruct an object."""

    module: str
    class_name: str
    args: List[Any]
    kwargs: Mapping[str, Any]

    def recreate_object(self, *, secrets: RawSecrets = {}):
        """Redoes the init call from this record."""
        cls = getattr(importlib.import_module(self.module), self.class_name)
        args, kwargs = inject_dependencies(self.args, self.kwargs, secrets=secrets)
        return cls(*args, **kwargs)


def add_initialization_record(self, *args, **kwargs):
    # We want the outer-most init to be recorded, so don't overwrite it.
    record_args, record_kwargs = serialize_injected_dependencies(args, kwargs)
    self._initialization_record = InitializationRecord(
        module=self.__class__.__module__,
        class_name=self.__class__.__qualname__,
        args=record_args,
        kwargs=record_kwargs,
    )


def get_initialization_record(obj) -> InitializationRecord:
    """Get the initialization record from an object."""
    try:
        return obj._initialization_record
    except AttributeError:
        raise AssertionError(
            f"Class {obj.__class__.__qualname__} in module "
            f"{obj.__class__.__module__} needs to call "
            f"`add_initialization_record` to its `__init__` "
            f"or `_after_init` to enable system reproducibility."
        )
