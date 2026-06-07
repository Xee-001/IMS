from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    success: bool = True
    data: Optional[DataT] = None
