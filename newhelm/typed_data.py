from typing import Any, Dict, Optional, Type, TypeVar
from typing_extensions import Self
from pydantic import BaseModel

from newhelm.general import get_class

Typeable = BaseModel | Dict[str, Any]

_BaseModelType = TypeVar("_BaseModelType", bound=Typeable)


class TypedData(BaseModel):
    """This is a generic container that allows Pydantic to do polymorphic serialization.

    This is useful in situations where you have an unknown set of classes that could be
    used in a particular field.
    """

    module: str
    class_name: str
    data: Dict[str, Any]

    @classmethod
    def from_instance(cls, obj: Typeable) -> Self:
        """Convert the object into a TypedData instance."""
        if isinstance(obj, BaseModel):
            data = obj.model_dump()
        elif isinstance(obj, Dict):
            data = obj
        else:
            raise TypeError(f"Unexpected type {type(obj)}.")
        return cls(
            module=obj.__class__.__module__,
            class_name=obj.__class__.__qualname__,
            data=data,
        )

    def to_instance(
        self, instance_cls: Optional[Type[_BaseModelType]] = None
    ) -> _BaseModelType:
        """Convert this data back into its original type.

        You can optionally include the desired resulting type to get
        strong type checking and to avoid having to do reflection.
        """
        cls_obj: Type[_BaseModelType]
        if instance_cls is None:
            cls_obj = get_class(self.module, self.class_name)
        else:
            cls_obj = instance_cls
        assert (
            cls_obj.__module__ == self.module
            and cls_obj.__qualname__ == self.class_name
        ), (
            f"Cannot convert {self.module}.{self.class_name} to "
            f"{cls_obj.__module__}.{cls_obj.__qualname__}."
        )
        if issubclass(cls_obj, BaseModel):
            return cls_obj.model_validate(self.data)  # type: ignore
        elif issubclass(cls_obj, Dict):
            return cls_obj(self.data)  # type: ignore
        else:
            raise TypeError(f"Unexpected type {cls_obj}.")
