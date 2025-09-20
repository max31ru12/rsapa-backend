from typing import Annotated

from pydantic import Field

Password = Annotated[str, Field()]
