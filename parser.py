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
                raise ValueError(f"[CONNECTION] connector "
                                 f"{connection.connection_a}"
                                 " name "
                                 "does not match a hub line → "
                                 f"{connection.nb_line}")
        for connection in self.glb_connection:
            if connection.connection_b not in valid_names:
                raise ValueError(f"[CONNECTION] connector "
                                 f"{connection.connection_b}"
                                 " name "
                                 "does not match a hub line → "
                                 f"{connection.nb_line}")
        return self

    @model_validator(mode="after")
    def check_duplicate_name(self) -> Self:
        all_names: list[str] = [hub.name for hub in self.glb_hub]
        all_names.append(self.glb_start.name)
        all_names.append(self.glb_end.name)

        for hub in self.glb_hub:
            if all_names.count(hub.name) >= 2:
                raise ValueError(f"[HUB] the hub name "
                                 f"({hub.name}) is "
                                 "already in use line → "
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
                raise ValueError("[DRONE] The drone parameter "
                                 "is not in the first position "
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
                raise ValueError(f"[CONNECTION] The path for "
                                 f"this connector {path_tuple}"
                                 " already exists line → "
                                 f"{c.nb_line}")
        return self

    @model_validator(mode="after")
    def check_color(self) -> Self:
        list_colors: list[str] = ["yellow", "grey", "red", "orange", "brown",
                                  "blue", "green", "pink", "cyan", "purple",
                                  "lime", "magenta", "gold", "black", "maroon",
                                  "darkred", "violet", "crimson", "rainbow"]

        for hub in self.glb_hub:
            if hub.color not in list_colors and hub.color is not None:
                raise ValueError("[HUB] The color for the "
                                 "hub is not valid line → "
                                 f"{hub.nb_line}\n"
                                 "[Valid color list]: "
                                 f"{list_colors}")

        if (self.glb_start.color not in list_colors
           and self.glb_start.color is not None):
            raise ValueError("[START HUB] The color for the "
                             "Start hub is not valid line → "
                             f"{self.glb_start.nb_line}\n"
                             "[Valid color list]: "
                             f"{list_colors}")

        if (self.glb_end.color not in list_colors
           and self.glb_end.color is not None):
            raise ValueError("[END HUB] The color for the "
                             "End  hub is not valid line → "
                             f"{self.glb_end.nb_line}\n"
                             "[Valid color list]: "
                             f"{list_colors}")

        return self

    @model_validator(mode="after")
    def check_zone(self) -> Self:
        list_zone: list[str] = ["normal", "blocked", "restricted", "priority"]

        for hub in self.glb_hub:
            if hub.zone not in list_zone:
                raise ValueError("[HUB] The zone for the "
                                 "hub is not valid line → "
                                 f"{hub.nb_line}\n"
                                 "[Valid zone list]: "
                                 f"{list_zone}")
        return self

    @model_validator(mode="after")
    def check_coordinates(self) -> Self:
        list_xy: list[tuple[int, int]] = [(hub.x, hub.y)
                                          for hub in self.glb_hub]
        list_xy.append((self.glb_start.x, self.glb_start.y))
        list_xy.append((self.glb_end.x, self.glb_end.y))

        data_start: tuple[int, int] = (self.glb_start.x, self.glb_start.y)
        if list_xy.count(data_start) > 1:
            raise ValueError(f"[START_HUB] {self.glb_start.name} These "
                             f"coordinates {data_start} "
                             "are already in use "
                             f"line → {self.glb_start.nb_line}")

        for hub in self.glb_hub:
            data: tuple[int, int] = (hub.x, hub.y)
            if list_xy.count(data) > 1:
                raise ValueError(f"[HUB] {hub.name} These coordinates "
                                 f"{data} "
                                 "are already in use "
                                 f"line → {hub.nb_line}")

        data_end: tuple[int, int] = (self.glb_end.x, self.glb_end.y)
        if list_xy.count(data_end) > 1:
            raise ValueError(f"[END_HUB] {self.glb_end.name} These "
                             f"coordinates {data_end} "
                             "are already in use "
                             f"line → {self.glb_end.nb_line}")

        return self


class ParseMaps():

    @staticmethod
    def create_hub(type_obj: Any, string: str, line: int, id: int) -> Any:
        key: str
        value: str
        if "[" in string and "]" in string:
            data: str = string[:string.index("[")].strip()
            data_list: list[str] = data.strip().split()

            if len(data_list) != 3:
                raise ValueError("[HUB] Invalid arguments "
                                 f"line → {line}")

            try:
                x = int(data_list[1])
                y = int(data_list[2])
            except ValueError:
                raise ValueError("[HUB] Invalid number format "
                                 f"({data_list[1]}, {data_list[2]}) "
                                 f"line → {line}")

            if "-" in data_list[0]:
                raise ValueError("[HUB] The character '-' is "
                                 "not allowed in the name"
                                 f" line → {line}")
            hub: Any = type_obj(
                name=data_list[0],
                id=id,
                x=x,
                y=y,
                nb_line=line
            )

            option: str = (
                string[string.index("[") + 1: string.index("]")].strip())
            if len(option.split()) < 1 and len(option.split()) > 3:
                raise ValueError("[HUB] Invalid format option "
                                 f"line → {line}")
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
                        raise ValueError("[HUB] Invalid max_drones "
                                         f"line → {line}")
                    if hub.max_drones < 1:
                        raise ValueError("[HUB] Invalid max_drones "
                                         "must be greater than 0 "
                                         f"line → {line}")
                else:
                    raise ValueError("[HUB] Invalid option "
                                     f"line → {line}")

        else:
            data_list = string.strip().split()

            if len(data_list) != 3:
                raise ValueError("[HUB] Invalid arguments "
                                 f"line → {line}")

            try:
                x = int(data_list[1])
                y = int(data_list[2])
            except ValueError:
                raise ValueError("[HUB] Invalid number format "
                                 f"line → {line}")

            hub = type_obj(
                name=data_list[0],
                x=x,
                y=y,
                nb_line=line
            )

        return hub

    @staticmethod
    def create_connection(string: str, line: int) -> Connection:
        a: str
        b: str
        key: str
        value: str
        if "[" in string and "]" in string:
            data: str = string[:string.index("[")].strip()
            data_list: list[str] = data.strip().split()
            if len(data_list) != 1 or data_list[0].count("-") != 1:
                raise ValueError("[CONNECTION] Invalid arguments "
                                 f"line → {line}")
            a, b = data_list[0].split("-", 1)
            connection = Connection(connection_a=a,
                                    connection_b=b,
                                    nb_line=line)
            option: str = (
                string[string.index("[") + 1: string.index("]")].strip())
            for item in option.split():
                key, value = item.split("=", 1)
                if key == "max_link_capacity":
                    try:
                        value_int = int(value)
                    except ValueError:
                        raise ValueError(
                            "[CONNECTION] Invalid value "
                            f"('{value}') "
                            "for max_link_capacity "
                            f"line → {line}"
                        )
                    if value_int < 1:
                        raise ValueError("[HUB] max_link_capacity "
                                         "must be greater than 0 "
                                         f"line → {line}")
                    connection.max_link_capacity = value_int
        else:
            if len(string.split()) != 1 or string.count("-") != 1:
                raise ValueError("[CONNECTION] Invalid option "
                                 f"line → {line}")
            a, b = string.split("-", 1)
            connection = Connection(connection_a=a,
                                    connection_b=b,
                                    nb_line=line)
        return connection

    @staticmethod
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
            id: int = 0
            with open(file_name, 'r', encoding='utf8') as file:
                for i, line in enumerate(file):
                    index: str = line.split(":", 1)[0].strip()
                    if index == "nb_drones":
                        data = line.split(":", 1)[1].strip()
                        try:
                            nb_drone = int(data)
                        except ValueError:
                            raise ValueError("[DRONE] invalid int "
                                             f"'{data}' line → {i + 1}")
                        if nb_drone < 1:
                            raise ValueError("[DRONE] nb_drone "
                                             "must be >= 1 "
                                             f"line → {i + 1}")
                        drone = Drone(nb_drone=nb_drone, nb_line=i+1)
                    elif index == "start_hub":
                        start_flag += 1
                        if start_flag > 1:
                            raise ValueError("[START_HUB] the parameter "
                                             "is duplicated "
                                             f"line → {i + 1}")
                        data = line.split(":", 1)[1].strip()
                        hub_start = ParseMaps.create_hub(Start, data,
                                                         (i + 1), id)
                        id += 1
                    elif index == "end_hub":
                        end_flag += 1
                        if end_flag > 1:
                            raise ValueError("[END_HUB] the parameter "
                                             "is duplicated "
                                             f"line → {i + 1}")
                        data = line.split(":", 1)[1].strip()
                        hub_end = ParseMaps.create_hub(End, data, (i + 1), id)
                        id += 1
                    elif index == "hub":
                        data = line.split(":", 1)[1].strip()
                        hub: Hub = ParseMaps.create_hub(Hub, data, (i + 1), id)
                        hub_list.append(hub)
                        id += 1
                    elif index == "connection":
                        data = line.split(":", 1)[1].strip()
                        connection: Connection = (
                            ParseMaps.create_connection(data, (i + 1)))
                        connection_list.append(connection)
                    else:
                        continue

                if hub_start is None:
                    raise ValueError("[MAP] start_hub is not present"
                                     " in the map")
                if hub_end is None:
                    raise ValueError("[MAP] start_end is not present"
                                     " in the map")
                if drone is None:
                    raise ValueError("[MAP] nb_drones is not present"
                                     " in the map")
                if connection_list == []:
                    raise ValueError("[MAP] connection is not "
                                     "present in the map")

        except (FileNotFoundError, PermissionError, ValueError) as error:
            raise ValueError(f"[ERROR]: ({type(error).__name__}) {error}")
        try:
            map = Global(glb_drones=drone,
                         glb_start=hub_start,
                         glb_end=hub_end,
                         glb_hub=hub_list,
                         glb_connection=connection_list)

        except ValidationError as error:
            raise ValueError(f"[ERROR]: ({error.errors()[0]['type']}) "
                  f"{error.errors()[0]['ctx']['error'].args[0]}")

        return map
