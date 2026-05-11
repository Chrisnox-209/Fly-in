import sys
# from pydantic import BaseModel, Field
from typing import Any


def create_list_optional(string: str) -> list[str | dict[str, str]]:
    list_value: list[str | dict[str, str]] = []
    dict_option: dict[str, str] = {}
    key: str
    value: str

    data: str = string[:string.index("[")].strip()
    list_value.extend(data.strip().split())

    option: str = string[string.index("[") + 1: string.index("]")].strip()
    for item in option.split():
        key, value = item.split("=", 1)
        dict_option[key] = value

    list_value.append(dict_option)
    return list_value


def parse(file_name: str) -> tuple[list[Any], list[Any], list[Any],
                                   list[list[Any]], list[Any]] | list[Any]:
    hub_start: list[Any] = []
    hub_end: list[Any] = []
    hub_list: list[list] = []
    connection: list[Any] = []
    nb_drones: list[Any] = []
    try:
        key: Any
        data: Any
        with open(file_name, 'r', encoding='utf8') as file:
            for i, line in enumerate(file):
                if line.startswith("nb_drones: "):
                    data = line.strip().split(":")[-1].strip()
                    nb_drones.append(data)
                    nb_drones.append(i + 1)
                elif line.startswith("start_hub: "):
                    key, data = line.split(":", 1)
                    if "[" in data and "]" in data:
                        hub_start = create_list_optional(data)
                        hub_start.append(i + 1)
                    else:
                        hub_start = data.strip().split()
                        hub_start.append(i + 1)
                elif line.startswith("end_hub: "):
                    key, data = line.split(":", 1)
                    if "[" in data and "]" in data:
                        hub_end = create_list_optional(data)
                        hub_end.append(i + 1)
                    else:
                        hub_end = data.strip().split()
                        hub_end.append(i + 1)
                elif line.startswith("hub: "):
                    key, data = line.split(":", 1)
                    if "[" in data and "]" in data:
                        list_data: list[str] = []
                        list_data = create_list_optional(data)
                        list_data.append(i + 1)
                        hub_list.append(list_data)
                    else:
                        list_data = []
                        list_data = list_data + data.strip().split()
                        list_data.append(i + 1)
                        hub_list.append(list_data)
                elif line.startswith("connection: "):
                    key, data = line.split(":", 1)
                    if "[" in data and "]" in data:
                        list_data = []
                        list_data = (
                            list_data + create_list_optional(data))
                        list_data.append(i + 1)
                        connection.append(list_data)
                    else:
                        list_data = []
                        list_data = list_data + data.strip().split()
                        list_data.append(i + 1)
                        connection.append(list_data)
                else:
                    continue
    except (FileNotFoundError, PermissionError, ValueError) as error:
        print(f"Error: {error}")
        sys.exit(1)
    return nb_drones, hub_start, hub_end, hub_list, connection
