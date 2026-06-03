import math
import heapq
from typing import Any


class TrafficController:
    def __init__(self, map_data: Any) -> None:
        self.map_data: Any = map_data
        self.hub_details: dict[str, tuple[int, str, int, int]] = {}
        self.address_book: dict[str, set[str]] = {}
        self.start: str = map_data.glb_start.name
        self.end: str = map_data.glb_end.name
        self.link_capacities: dict[tuple[str, str], int] = {}

        self.flight_log: dict[tuple[str, int], int] = {}
        self.link_log: dict[tuple[str, str, int], int] = {}

        self.hub_details[map_data.glb_start.name] = (
            map_data.glb_start.max_drones,
            map_data.glb_start.zone,
            map_data.glb_start.x,
            map_data.glb_start.y
        )
        self.hub_details[map_data.glb_end.name] = (
            map_data.glb_end.max_drones,
            map_data.glb_end.zone,
            map_data.glb_end.x,
            map_data.glb_end.y
        )

        self.address_book[map_data.glb_start.name] = set()
        self.address_book[map_data.glb_end.name] = set()

        for hub in map_data.glb_hub:
            self.address_book[hub.name] = set()
            self.hub_details[hub.name] = (
                hub.max_drones,
                hub.zone,
                hub.x,
                hub.y
            )

        for c in map_data.glb_connection:
            if c.connection_a in self.address_book:
                self.address_book[c.connection_a].add(c.connection_b)
            if c.connection_b in self.address_book:
                self.address_book[c.connection_b].add(c.connection_a)
            self.link_capacities[(c.connection_a, c.connection_b)] = (
                c.max_link_capacity
            )
            self.link_capacities[(c.connection_b, c.connection_a)] = (
                c.max_link_capacity
            )

    @staticmethod
    def score(xa: int, ya: int, xb: int, yb: int) -> float:
        return math.sqrt((xb - xa) ** 2 + (yb - ya) ** 2)

    @staticmethod
    def zone_type_score(zone: str) -> int:
        if zone == "blocked":
            return 0
        elif zone == "restricted":
            return 3
        elif zone == "priority":
            return 1
        return 2

    def find_path(self) -> tuple[list[str], list[tuple[str, int]]] | None:
        waiting_list: list[tuple[float, str, int]] = []
        initial_state: tuple[str, int] = (self.start, 0)

        origin: dict[tuple[str, int], tuple[str, int] | None] = {
            initial_state: None
        }
        g_score: dict[tuple[str, int], int] = {initial_state: 0}

        heapq.heappush(waiting_list, (0.0, self.start, 0))

        end_position: tuple[int, int] = (
            self.map_data.glb_end.x,
            self.map_data.glb_end.y
        )

        while waiting_list:
            score_f: float
            current_hub: str
            current_turn: int
            score_f, current_hub, current_turn = heapq.heappop(waiting_list)

            current_state: tuple[str, int] = (current_hub, current_turn)

            if g_score.get(current_state, float('inf')) < current_turn:
                continue

            previous_physical_hub: str | None = None
            previous_state: tuple[str, int] | None = origin.get(current_state)

            while previous_state is not None:
                if previous_state[0] != current_hub:
                    previous_physical_hub = previous_state[0]
                    break
                previous_state = origin.get(previous_state)

            if current_hub == self.end:
                path_states: list[tuple[str, int]] = []
                state: tuple[str, int] | None = current_state

                while state is not None:
                    path_states.append(state)
                    state = origin.get(state)

                path_states.reverse()

                path_final: list[str] = []
                for i in range(len(path_states) - 1):
                    hub_actuel: str = path_states[i][0]
                    tour_actuel: int = path_states[i][1]
                    tour_suivant: int = path_states[i + 1][1]

                    for _ in range(tour_suivant - tour_actuel):
                        path_final.append(hub_actuel)

                path_final.append(path_states[-1][0])

                return path_final, path_states

            if current_hub not in self.address_book:
                continue

            possible_neighbors: list[str] = list(
                self.address_book[current_hub]
            )
            possible_neighbors.append(current_hub)

            for next_hub in possible_neighbors:
                if next_hub == previous_physical_hub:
                    continue

                zone_score: int
                if next_hub == current_hub:
                    zone_score = 4
                else:
                    type_zone: str = self.hub_details[next_hub][1]
                    zone_score = TrafficController.zone_type_score(type_zone)
                    if zone_score == 0:
                        continue

                end_turn: int = current_turn + zone_score
                next_state: tuple[str, int] = (next_hub, end_turn)

                capacity_max: int = self.hub_details[next_hub][0]
                hub_full: bool = False

                for t in range(current_turn + 1, end_turn + 1):
                    if self.flight_log.get((next_hub, t), 0) >= capacity_max:
                        hub_full = True
                        break

                if hub_full and next_hub != self.start:
                    continue

                if next_hub != current_hub:
                    route_capacity: int = self.link_capacities[
                        (current_hub, next_hub)
                    ]
                    route_is_full: bool = False

                    for t in range(current_turn + 1, end_turn + 1):
                        if self.link_log.get(
                            (current_hub, next_hub, t), 0
                        ) >= route_capacity:
                            route_is_full = True
                            break

                    if route_is_full:
                        continue

                if next_state not in g_score or end_turn < g_score[next_state]:
                    g_score[next_state] = end_turn
                    origin[next_state] = current_state

                    hub_position: tuple[int, int] = (
                        self.hub_details[next_hub][2],
                        self.hub_details[next_hub][3]
                    )

                    score_h: float = self.score(
                        hub_position[0],
                        hub_position[1],
                        end_position[0],
                        end_position[1]
                    )

                    heapq.heappush(
                        waiting_list,
                        (end_turn + score_h, next_hub, end_turn)
                    )

        return None

    def trafic_drones(self) -> dict[str, list[str]]:
        flight_plan: dict[str, list[str]] = {}

        self.flight_log.clear()
        self.link_log.clear()

        for i in range(self.map_data.glb_drones.nb_drone):
            drone: str = "D" + str(i)
            result: tuple[list[str], list[tuple[str, int]]] | None = (
                self.find_path()
            )

            if result is None:
                flight_plan[drone] = [self.start]
                continue

            path: list[str]
            path_states: list[tuple[str, int]]
            path, path_states = result
            flight_plan[drone] = path

            round_idx: int
            step: str
            for round_idx, step in enumerate(path):
                self.flight_log[(step, round_idx)] = (
                    self.flight_log.get((step, round_idx), 0) + 1
                )

            j: int
            for j in range(len(path_states) - 1):
                hub_actuel: str = path_states[j][0]
                tour_actuel: int = path_states[j][1]
                hub_suivant: str = path_states[j + 1][0]
                tour_suivant: int = path_states[j + 1][1]

                if hub_actuel != hub_suivant:
                    t: int
                    for t in range(tour_actuel + 1, tour_suivant + 1):
                        self.link_log[(hub_actuel, hub_suivant, t)] = (
                            self.link_log.get(
                                (hub_actuel, hub_suivant, t), 0
                            ) + 1
                        )
                        self.link_log[(hub_suivant, hub_actuel, t)] = (
                            self.link_log.get(
                                (hub_suivant, hub_actuel, t), 0
                            ) + 1
                        )

        return flight_plan
