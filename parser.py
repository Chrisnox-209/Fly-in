import sys
from pydantic import BaseModel, Field
from typing import Any, Optional, Annotated


class Node(BaseModel):
    name: Annotated[str, Field(min_length=1, strip_whitespace=True)]
    x: int = Field(...)
    y: int = Field(...)
    nb_line: int = Field(..., ge=1)
    color: str | None = None
    max_drones:  int | None = None


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
    max_link_capacity: int | None = None


def create_hub(string: str, line: int) -> Hub:
    value: str
    key: str
    if "[" in string and "]" in string:
        data: str = string[:string.index("[")].strip()
        data_list: list[str] = data.strip().split()
        if len(data_list) != 3:
            raise ValueError(f"[HUB]InvalidArguments (line={line})")
        else:
            hub = Hub(name=data_list[0],
                      x=int(data_list[1]),
                      y=int(data_list[2]),
                      nb_line=line)
        option: str = string[string.index("[") + 1: string.index("]")].strip()
        for item in option.split():
            key, value = item.split("=", 1)
            if key == "color":
                hub.color = value
            elif key == "max_drones":
                hub.max_drones = int(value)
            else:
                raise ValueError(f"[HUB]InvalidOption (line={line})")
    else:
        data_list = string.strip().split()
        if len(data_list) > 3 or len(data_list) < 3:
            raise ValueError(f"[HUB]InvalidArguments (line={line})")
        else:
            hub = Hub(name=data_list[0],
                      x=int(data_list[1]),
                      y=int(data_list[2]),
                      nb_line=line)
    return hub


def create_connection(string: str, line: int) -> Connection:
    a: str
    b: str
    key: str
    value: str
    if "[" in string and "]" in string:
        data: str = string[:string.index("[")].strip()
        data_list: list[str] = data.strip().split()
        if len(data_list) != 1 or data_list[0].count("-") != 1:
            raise ValueError(f"[CONNECTION]InvalidArguments cd(line={line})")
        a, b = data_list[0].split("-", 1)
        connection = Connection(connection_a=a,
                                connection_b=b,
                                nb_line=line)
        option: str = string[string.index("[") + 1: string.index("]")].strip()
        for item in option.split():
            key, value = item.split("=", 1)
            if key == "max_link_capacity":
                connection.max_link_capacity = int(value)
            else:
                raise ValueError(f"[CONNECTION]InvalidOption (line={line})")
    else:
        if len(string.split()) != 1 or string.count("-") != 1:
            raise ValueError(f"[CONNECTION]InvalidArguments (line={line})")
        a, b = string.split("-", 1)
        connection = Connection(connection_a=a,
                                connection_b=b,
                                nb_line=line)
    return connection


def parse(file_name: str) -> Any:
    hub_list: list[Any] = []
    connection_list: list[Any] = []
    try:
        data: Any
        with open(file_name, 'r', encoding='utf8') as file:
            for i, line in enumerate(file):
                index: str = line.split(":", 1)[0].strip()
                if index == "nb_drones":
                    data = line.split(":", 1)[1].strip()
                    drone = Drone(nb_drone=data, nb_line=(i + 1))
                elif index == "start_hub":
                    data = line.split(":", 1)[1].strip()
                    hub_start: Hub = create_hub(data, (i + 1))
                elif index == "end_hub":
                    data = line.split(":", 1)[1].strip()
                    hub_end: Hub = create_hub(data, (i + 1))
                elif index == "hub":
                    data = line.split(":", 1)[1].strip()
                    hub: Hub = create_hub(data, (i + 1))
                    hub_list.append(hub)
                elif index == "connection":
                    data = line.split(":", 1)[1].strip()
                    connection: Connection = create_connection(data, (i + 1))
                    connection_list.append(connection)
                else:
                    continue
    except (FileNotFoundError, PermissionError, ValueError) as error:
        print(f"Error: {error}")
        sys.exit(1)
    return drone, hub_start, hub_end, hub_list, connection_list
