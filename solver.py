from parser import Global
from typing import Any


class TrafficController:
    def __init__(self, map_data: Any) -> None:
        self.map_data: Any = map_data

        drones: int = map_data.glb_drones.nb_drone
        self.pos_drones: dict = {}
        self.hub_details: dict = {}
        self.address_book: dict = {}

        for i in range(drones):
            number_drone: Any = "D" + str(i)
            self.pos_drones[number_drone] = map_data.glb_start.name

        self.hub_details[map_data.glb_start.name] = (
            map_data.glb_start.max_drones,
            map_data.glb_start.zone)
        self.hub_details[map_data.glb_end.name] = (
            map_data.glb_end.max_drones,
            map_data.glb_end.zone)

        self.address_book[map_data.glb_start.name] = set()
        self.address_book[map_data.glb_end.name] = set()

        for hub in map_data.glb_hub:
            self.address_book[hub.name] = set()
            self.hub_details[hub.name] = (hub.max_drones, hub.zone)

        for c in map_data.glb_connection:
            if c.connection_a in self.address_book:
                self.address_book[c.connection_a].add(c.connection_b)
            if c.connection_b in self.address_book:
                self.address_book[c.connection_b].add(c.connection_a)

        print(self.address_book)

    def find_path(self) -> None:
        pass