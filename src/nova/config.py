from typing import Annotated, Literal

from pydantic import Field, StrictStr
from pydantic.dataclasses import dataclass

_NonEmptyString = Annotated[StrictStr, Field(min_length=1)]


@dataclass(kw_only=True, frozen=True)
class AppInfo:
    project_name: _NonEmptyString
    version: _NonEmptyString
    environment: Literal["test", "dev", "prod"]
