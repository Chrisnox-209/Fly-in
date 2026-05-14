from pydantic import BaseModel, Field
from typing import Optional, Annotated


class Node(BaseModel):
    name: Annotated[str, Field(min_length=1, strip_whitespace=True)]
    x: int = Field(...)
    y: int = Field(...)
    nb_line: int = Field(..., ge=1)
    color: Optional[str] = None
    max_drones: Optional[int] = Field(default=None, ge=1)
    zone: str = Field(default="normal")


class Hub(Node):
    pass


class Start(Node):
    pass


class End(Node):
    pass


class Drone(BaseModel):
    nb_drone: int = Field(..., ge=1)
    nb_line: int = Field(..., ge=1)


class Connection(BaseModel):
    connection_a: Annotated[str, Field(min_length=1, strip_whitespace=True)]
    connection_b: Annotated[str, Field(min_length=1, strip_whitespace=True)]
    nb_line: int = Field(..., ge=1)
    max_link_capacity: int = Field(default=1)
