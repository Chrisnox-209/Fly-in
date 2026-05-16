import sys
from structure import Drone, Start, End, Hub, Connection
from typing import Any, ClassVar, Self
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    model_validator,
)


class Global(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        arbitrary_types_allowed=True
    )
    glb_drones: Drone = Field(...)
    glb_start: Start = Field(...)
    glb_end: End = Field(...)
    glb_hub: list[Hub] = Field(...)
    glb_connection: list[Connection] = Field(...)

    @model_validator(mode="after")
    def check_connection_ab(self) -> Self:
        valid_names: list[str] = [hub.name for hub in self.glb_hub]
        valid_names.append(self.glb_start.name)
        valid_names.append(self.glb_end.name)

        for connection in self.glb_connection:
            if connection.connection_a not in valid_names:
                raise ValueError(f"[CONNECTION]\033[1;37m connector "
                                 f"\033[38;5;215m{connection.connection_a}"
                                 "\033[1;37m name "
                                 "does not match a hub \033[1;35mline → "
                                 f"{connection.nb_line}")
        for connection in self.glb_connection:
            if connection.connection_b not in valid_names:
                raise ValueError(f"[CONNECTION]\033[1;37m connector "
                                 f"\033[38;5;215m{connection.connection_b}"
                                 "\033[1;37m name "
                                 "does not match a hub \033[1;35mline → "
                                 f"{connection.nb_line}")
        return self

    @model_validator(mode="after")
    def check_duplicate_name(self) -> Self:
        all_names: list[str] = [hub.name for hub in self.glb_hub]
        all_names.append(self.glb_start.name)
        all_names.append(self.glb_end.name)

        for hub in self.glb_hub:
            if all_names.count(hub.name) >= 2:
                raise ValueError(f"[HUB]\033[1;37m the hub name "
                                 f"(\033[38;5;215m{hub.name}\033[1;37m) is "
                                 "already in use\033[1;35m line → "
                                 f"{hub.nb_line}")
        return self

    @model_validator(mode="after")
    def postion_drone(self) -> Self:
        pos_drone: int = self.glb_drones.nb_line
        all_pos: list[int] = [hub.nb_line for hub in self.glb_hub]
        all_pos_connection: list[int] = [connect.nb_line for connect
                                         in self.glb_connection]
        all_pos.extend(all_pos_connection)
        all_pos.append(self.glb_end.nb_line)
        all_pos.append(self.glb_start.nb_line)

        for nb in all_pos:
            if nb <= pos_drone:
                raise ValueError("[DRONE]\033[1;37m The drone parameter "
                                 "is not in the first position \033[1;35m"
                                 f"line → {pos_drone}")
        return self

    @model_validator(mode="after")
    def check_double_path(self) -> Self:
        list_connector: list[tuple[str, str]] = [
            (con.connection_a, con.connection_b)
            for con in self.glb_connection]

        reverse_connector: list[tuple[str, str]] = [
            (con.connection_b, con.connection_a)
            for con in self.glb_connection]

        list_connector.extend(reverse_connector)

        for c in self.glb_connection:
            path_tuple: tuple[str, str] = c.connection_a, c.connection_b
            if list_connector.count(path_tuple) > 1:
                raise ValueError(f"[CONNECTION]\033[1;37m The path for "
                                 f"this connector \033[38;5;215m{path_tuple}"
                                 "\033[1;37m already exists\033[1;35m line → "
                                 f"{c.nb_line}")
        return self

    @model_validator(mode="after")
    def check_color(self) -> Self:
        list_colors: list[str] = ["yellow", "grey", "red",
                                  "blue", "green", "pink", "cyan"]

        for hub in self.glb_hub:
            if hub.color not in list_colors and hub.color is not None:
                raise ValueError("[HUB]\033[1;37m The color for the "
                                 "hub is not valid \033[1;35m line → "
                                 f"{hub.nb_line}\n\n"
                                 "\033[1;37m[Valid color list]: "
                                 f"\033[1;32m{list_colors}")

        if self.glb_start.color not in list_colors and hub.color is not None:
            raise ValueError("[START HUB]\033[1;37m The color for the "
                             "Start hub is not valid \033[1;35m line → "
                             f"{hub.nb_line}\n\n"
                             "\033[1;37m[Valid color list]: "
                             f"\033[1;32m{list_colors}")

        if self.glb_end.color not in list_colors and hub.color is not None:
            raise ValueError("[END HUB]\033[1;37m The color for the "
                             "End  hub is not valid \033[1;35m line → "
                             f"{hub.nb_line}\n\n"
                             "\033[1;37m[Valid color list]: "
                             f"\033[1;32m{list_colors}")

        return self

    @model_validator(mode="after")
    def check_zone(self) -> Self:
        list_zone: list[str] = ["normal", "blocked", "restricted", "priority"]

        for hub in self.glb_hub:
            if hub.zone not in list_zone:
                raise ValueError("[HUB]\033[1;37m The zone for the "
                                 "hub is not valid \033[1;35m line → "
                                 f"{hub.nb_line}\n\n"
                                 "\033[1;37m[Valid zone list]: "
                                 f"\033[1;32m{list_zone}")
        return self


def create_hub(type_obj: Any, string: str, line: int) -> Any:
    key: str
    value: str
    if "[" in string and "]" in string:
        data: str = string[:string.index("[")].strip()
        data_list: list[str] = data.strip().split()

        if len(data_list) != 3:
            raise ValueError("[HUB]\033[1;37m Invalid arguments "
                             f"\033[1;35mline → {line}")

        try:
            x = int(data_list[1])
            y = int(data_list[2])
        except ValueError:
            raise ValueError("[HUB]\033[1;37m Invalid number format "
                             f"\033[1;35mline → {line}")

        if "-" in data_list[0]:
            raise ValueError("[HUB]\033[1;37m The character '-' is "
                             "not allowed in the name"
                             f"\033[1;35m line → {line}")
        hub: Any = type_obj(
            name=data_list[0],
            x=x,
            y=y,
            nb_line=line
        )

        option: str = string[string.index("[") + 1: string.index("]")].strip()
        if len(option.split()) < 1 and len(option.split()) > 3:
            raise ValueError("[HUB] Invalid format option "
                             f"\033[1;35mline → {line}")
        for item in option.split():
            key, value = item.split("=", 1)

            if key == "color":
                hub.color = value
            elif key == "zone":
                hub.zone = value
            elif key == "max_drones":
                try:
                    hub.max_drones = int(value)
                except ValueError:
                    raise ValueError("[HUB]\033[1;37m Invalid max_drones "
                                     f"\033[1;35mline → {line}")
                if hub.max_drones < 1:
                    raise ValueError("[HUB]\033[1;37m Invalid max_drones "
                                     "must be greater than 0 "
                                     f"\033[1;35mline → {line}")
            else:
                raise ValueError("[HUB]\033[1;37m InvalidOption "
                                 f"\033[1;35mline → {line}")

    else:
        data_list = string.strip().split()

        if len(data_list) != 3:
            raise ValueError("[HUB]\033[1;37m Invalid arguments "
                             f"\033[1;35mline → {line}")

        try:
            x = int(data_list[1])
            y = int(data_list[2])
        except ValueError:
            raise ValueError("[HUB]\033[1;37m Invalid number format "
                             f"\033[1;35mline → {line}")

        hub = type_obj(
            name=data_list[0],
            x=x,
            y=y,
            nb_line=line
        )

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
            raise ValueError("[CONNECTION]\033[1;37m Invalid arguments "
                             f"\033[1;35mline → {line}")
        a, b = data_list[0].split("-", 1)
        connection = Connection(connection_a=a,
                                connection_b=b,
                                nb_line=line)
        option: str = string[string.index("[") + 1: string.index("]")].strip()
        for item in option.split():
            key, value = item.split("=", 1)
            if key == "max_link_capacity":
                try:
                    int_value = int(value)
                except ValueError:
                    raise ValueError(
                        "[CONNECTION]\033[1;37m Invalid value "
                        f"\033[1;36m('{value}') "
                        "\033[1;37mfor max_link_capacity "
                        f"\033[1;35mline → {line}"
                    )
            if connection.max_link_capacity < 1:
                raise ValueError("[HUB]\033[1;37m max_link_capacity "
                                 "must be greater than 0 "
                                 f"\033[1;35mline → {line}")
            connection.max_link_capacity = int_value
    else:
        if len(string.split()) != 1 or string.count("-") != 1:
            raise ValueError("[CONNECTION]\033[1;37m InvalidOption "
                             f"\033[1;35mline → {line}")
        a, b = string.split("-", 1)
        connection = Connection(connection_a=a,
                                connection_b=b,
                                nb_line=line)
    return connection


def parse(file_name: str) -> Global:
    hub_list: list[Hub] = []
    connection_list: list[Connection] = []
    hub_start: Start | None = None
    hub_end: End | None = None
    drone: Drone | None = None
    start_flag: int = 0
    end_flag: int = 0

    try:
        data: Any
        with open(file_name, 'r', encoding='utf8') as file:
            for i, line in enumerate(file):
                index: str = line.split(":", 1)[0].strip()
                if index == "nb_drones":
                    data = line.split(":", 1)[1].strip()
                    try:
                        nb_drone = int(data)
                    except ValueError:
                        raise ValueError("[DRONE]\033[1;37m invalid int "
                                         f"'{data}' \033[1;35mline → {i + 1}")
                    if nb_drone < 1:
                        raise ValueError("[DRONE]\033[1;37m nb_drone "
                                         "must be >= 1 "
                                         f"\033[1;35mline → {i + 1}")
                    drone = Drone(nb_drone=nb_drone, nb_line=i+1)
                elif index == "start_hub":
                    start_flag += 1
                    if start_flag > 1:
                        raise ValueError("[START_HUB]\033[1;37m the parameter "
                                         "is duplicated "
                                         f"\033[1;35mline → {i + 1}")
                    data = line.split(":", 1)[1].strip()
                    hub_start = create_hub(Start, data, (i + 1))
                elif index == "end_hub":
                    end_flag += 1
                    if end_flag > 1:
                        raise ValueError("[END_HUB]\033[1;37m the parameter "
                                         "is duplicated "
                                         f"\033[1;35mline → {i + 1}")
                    data = line.split(":", 1)[1].strip()
                    hub_end = create_hub(End, data, (i + 1))
                elif index == "hub":
                    data = line.split(":", 1)[1].strip()
                    hub: Hub = create_hub(Hub, data, (i + 1))
                    hub_list.append(hub)
                elif index == "connection":
                    data = line.split(":", 1)[1].strip()
                    connection: Connection = create_connection(data, (i + 1))
                    connection_list.append(connection)
                else:
                    continue

            if hub_start is None:
                raise ValueError("[MAP]\033[1;37m start_hub is not present"
                                 " in the map")
            if hub_end is None:
                raise ValueError("[MAP]\033[1;37m start_end is not present"
                                 " in the map")
            if drone is None:
                raise ValueError("[MAP]\033[1;37m nb_drones is not present"
                                 " in the map")
            if connection_list == []:
                raise ValueError("[MAP]\033[1;37m connection is not "
                                 "present in the map")

    except (FileNotFoundError, PermissionError, ValueError) as error:
        print(f"\033[1;31m[ERROR]: "
              f"\033[1;35m({type(error).__name__}) "
              f"\033[1;33m{error}")
        sys.exit(1)

    try:
        map = Global(glb_drones=drone,
                     glb_start=hub_start,
                     glb_end=hub_end,
                     glb_hub=hub_list,
                     glb_connection=connection_list)
    except ValidationError as error:
        print(f"\033[1;31m[ERROR]: \033[1;35m({error.errors()[0]['type']}) "
              f"\033[1;33m{error.errors()[0]['ctx']['error'].args[0]}")
        sys.exit(1)
    return map
