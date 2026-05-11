import sys
# from pydantic import BaseModel, Field
# from typing import Annotated



# class MapConfig(BaseModel):
#     nb_drones: int = Field(ge=1)
#     end_hub: tuple[
#         Annotated[str, Field(min_length=3, pattern=r"^[^\s-]*$")],
#         [int, int]]


def create_list(string: str):
    list_value = []
    dict_option = {}

    data = string[:string.index("[")].strip()
    list_value = data.strip().split()

    option = string[string.index("[") + 1 : string.index("]")].strip()
    for item in option.split():
        key, value = item.split("=", 1)
        dict_option[key] = value

    list_value.append(dict_option)
    return list_value

# text = "   start_hub     :    hub    0    0    [zone=restricted color=red]"

# left, right = text.split(":", 1)
# left = left.strip()
# print(left)


# hub_part = right[:right.index("[")].strip()
# print(hub_part)

# tags = right[right.index("["):].strip()
# print(tags)

def parse(file: str):
    data_maps = {}
    list_hub = []
    connection = []
    nb_drones = []
    try:
        with open(file, 'r', encoding='utf8') as file:
            for i, line in enumerate(file):
                if line.startswith("nb_drones: "):
                    data = line.strip().split(":")[-1].strip()
                    nb_drones.append(data)
                    nb_drones.append(i)
                    print(nb_drones)
                # elif line.startswith("start_hub: "):
                #     key, data = line.split(":", 1)
                #     if "[" in data and "]" in data:
                #         data_maps["start_hub"] = create_list(data)
                #     else:
                #         data_maps[key] = data.strip().split()
                # elif line.startswith("end_hub: "):
                #     key, data = line.split(":", 1)
                #     if "[" in data and "]" in data:
                #         data_maps["end_hub"] = create_list(data)
                #     else:
                #         data_maps[key] = data.strip().split()
                # elif line.startswith("hub: "):
                #     key, data = line.split(":", 1)
                #     if "[" in data and "]" in data:
                #         data_maps["hub"] = create_list(data)
                #     else:
                #         data_maps[key] = data.strip().split()
                # elif line.startswith("connection: "):
                #     pass
                else:
                    continue
    except (FileNotFoundError, PermissionError, ValueError) as error:
        print(f"Error: {error}")
        sys.exit(1)
    # print(data_maps)
