from typing import Any
import math
import heapq


class TrafficController:
    def __init__(self, map_data: Any) -> None:
        self.map_data: Any = map_data

        drones: int = map_data.glb_drones.nb_drone
        self.pos_drones: dict = {}
        self.hub_details: dict = {}
        self.address_book: dict = {}
        self.start: str = map_data.glb_start.name
        self.end: str = map_data.glb_end.name

        for i in range(drones):
            number_drone: Any = "D" + str(i)
            self.pos_drones[number_drone] = map_data.glb_start.name

        self.hub_details[map_data.glb_start.name] = (
            map_data.glb_start.max_drones,
            map_data.glb_start.zone,
            map_data.glb_start.x,
            map_data.glb_start.y)
        self.hub_details[map_data.glb_end.name] = (
            map_data.glb_end.max_drones,
            map_data.glb_end.zone,
            map_data.glb_end.x,
            map_data.glb_end.y)

        self.address_book[map_data.glb_start.name] = set()
        self.address_book[map_data.glb_end.name] = set()

        for hub in map_data.glb_hub:
            self.address_book[hub.name] = set()
            self.hub_details[hub.name] = (
                hub.max_drones,
                hub.zone,
                hub.x,
                hub.y)

        for c in map_data.glb_connection:
            if c.connection_a in self.address_book:
                self.address_book[c.connection_a].add(c.connection_b)
            if c.connection_b in self.address_book:
                self.address_book[c.connection_b].add(c.connection_a)

    @staticmethod
    def score(xa: int, ya: int, xb: int, yb: int) -> float:
        result = math.sqrt(
            (xb - xa)**2 + (yb - ya)**2)
        return result

    def find_path(self) -> None:
        waiting_list: list = []
        origin: dict = {self.start: None}
        g_score: dict = {self.start: 0}
        heapq.heappush(waiting_list, (0, self.start))
        end_position: tuple[int, int] = (self.map_data.glb_end.x,
                                         self.map_data.glb_end.y)

        while waiting_list:

            score: int
            hub: str
            score, hub = heapq.heappop(waiting_list)

            if hub == self.end:
                break

            if hub in self.address_book:
                for hub_next in self.address_book[hub]:
                    g_current = g_score[hub] + 1
                    if (hub_next not in g_score
                       or g_current < g_score[hub_next]):
                        g_score[hub_next] = g_current
                        origin[hub_next] = hub

                        hub_position: tuple = (self.hub_details[hub_next][-2],
                                               self.hub_details[hub_next][-1])
                        score_h: float = self.score(
                            hub_position[0],
                            hub_position[1],
                            end_position[0],
                            end_position[1])
                        score_f: Any = g_current + score_h
                        heapq.heappush(waiting_list, (score_f, hub_next))

