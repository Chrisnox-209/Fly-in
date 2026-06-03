import math
import heapq
from typing import Any


class TrafficController:
    def __init__(self, map_data: Any) -> None:
        self.map_data: Any = map_data
        self.hub_details: dict[str, tuple[int, str, float, float]] = {}
        self.address_book: dict[str, set[str]] = {}
        self.start: str = map_data.glb_start.name
        self.end: str = map_data.glb_end.name
        self.link_capacities: dict[tuple[str, str], int] = {}

        self.flight_log: dict[tuple[str, int], int] = {}
        self.link_log: dict[tuple[str, str, int], int] = {}

        self.generated_waypoints: list[tuple[str, str, str, float]] = []

        self.hub_details[map_data.glb_start.name] = (
            map_data.glb_start.max_drones,
            map_data.glb_start.zone,
            float(map_data.glb_start.x),
            float(map_data.glb_start.y)
        )
        self.hub_details[map_data.glb_end.name] = (
            map_data.glb_end.max_drones,
            map_data.glb_end.zone,
            float(map_data.glb_end.x),
            float(map_data.glb_end.y)
        )

        self.address_book[map_data.glb_start.name] = set()
        self.address_book[map_data.glb_end.name] = set()

        hub: Any
        for hub in map_data.glb_hub:
            self.address_book[hub.name] = set()
            self.hub_details[hub.name] = (
                hub.max_drones,
                hub.zone,
                float(hub.x),
                float(hub.y)
            )

        connection: Any
        for connection in map_data.glb_connection:
            node_a: str = connection.connection_a
            node_b: str = connection.connection_b
            capacity: int = connection.max_link_capacity

            x_a: float = self.hub_details[node_a][2]
            y_a: float = self.hub_details[node_a][3]
            x_b: float = self.hub_details[node_b][2]
            y_b: float = self.hub_details[node_b][3]

            self.address_book[node_a].add(node_b)
            self.address_book[node_b].add(node_a)
            self.link_capacities[(node_a, node_b)] = capacity
            self.link_capacities[(node_b, node_a)] = capacity

            prev_node: str = node_a
            i: int
            for i in range(1, capacity + 1):
                wp_name: str = f"wp_{node_a}_{node_b}_{i}"
                fraction: float = i / (capacity + 1)

                mx: float = x_a + (x_b - x_a) * fraction
                my: float = y_a + (y_b - y_a) * fraction

                self.hub_details[wp_name] = (1, "priority", mx, my)
                self.address_book[wp_name] = set()

                self.generated_waypoints.append(
                    (wp_name, node_a, node_b, fraction)
                )

                self.address_book[prev_node].add(wp_name)
                self.address_book[wp_name].add(prev_node)
                self.link_capacities[(prev_node, wp_name)] = 1
                self.link_capacities[(wp_name, prev_node)] = 1

                prev_node = wp_name

            self.address_book[prev_node].add(node_b)
            self.address_book[node_b].add(prev_node)
            self.link_capacities[(prev_node, node_b)] = 1
            self.link_capacities[(node_b, prev_node)] = 1

    @staticmethod
    def calculate_score(xa: float, ya: float, xb: float, yb: float) -> float:
        return math.sqrt((xb - xa) ** 2 + (yb - ya) ** 2)

    @staticmethod
    def get_zone_score(zone: str) -> int:
        if zone == "blocked":
            return 0
        if zone == "restricted":
            return 3
        if zone == "priority":
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

        end_pos: tuple[float, float] = (
            self.hub_details[self.end][2],
            self.hub_details[self.end][3]
        )

        while waiting_list:
            _, current_hub, current_turn = heapq.heappop(waiting_list)
            current_state: tuple[str, int] = (current_hub, current_turn)

            if current_turn > g_score.get(current_state, float('inf')):
                continue

            previous_hub: str | None = None
            prev_state: tuple[str, int] | None = origin.get(current_state)

            while prev_state is not None:
                if prev_state[0] != current_hub:
                    previous_hub = prev_state[0]
                    break
                prev_state = origin.get(prev_state)

            if current_hub == self.end:
                path_states: list[tuple[str, int]] = []
                state: tuple[str, int] | None = current_state

                while state is not None:
                    path_states.append(state)
                    state = origin.get(state)

                path_states.reverse()

                final_path: list[str] = [path_states[0][0]]
                i: int
                for i in range(len(path_states) - 1):
                    step_turn: int = path_states[i][1]
                    next_hub: str = path_states[i + 1][0]
                    next_turn: int = path_states[i + 1][1]

                    for _ in range(next_turn - step_turn):
                        final_path.append(next_hub)

                return final_path, path_states

            if current_hub not in self.address_book:
                continue

            possible_neighbors: list[str] = list(
                self.address_book[current_hub]
            )
            possible_neighbors.append(current_hub)

            for next_hub in possible_neighbors:
                if next_hub == previous_hub:
                    continue

                zone_score: int
                if next_hub == current_hub:
                    zone_score = 1
                else:
                    zone_score = self.get_zone_score(
                        self.hub_details[next_hub][1]
                    )
                    if zone_score == 0:
                        continue

                end_turn: int = current_turn + zone_score
                next_state: tuple[str, int] = (next_hub, end_turn)

                capacity_max: int = self.hub_details[next_hub][0]
                hub_full: bool = self.flight_log.get(
                    (next_hub, end_turn), 0
                ) >= capacity_max

                if hub_full and next_hub != self.start:
                    continue

                if next_hub != current_hub:
                    route_cap: int = self.link_capacities[(
                        current_hub, next_hub
                    )]
                    route_full: bool = False
                    for t in range(current_turn, end_turn + 1):
                        if self.link_log.get((current_hub, next_hub, t),
                                             0) >= route_cap:
                            route_full = True
                            break
                    if route_full:
                        continue

                if next_state not in g_score or end_turn < g_score[next_state]:
                    g_score[next_state] = end_turn
                    origin[next_state] = current_state

                    pos: tuple[float, float] = (
                        self.hub_details[next_hub][2],
                        self.hub_details[next_hub][3]
                    )

                    score_h: float = self.calculate_score(
                        pos[0], pos[1], end_pos[0], end_pos[1]
                    )

                    wait_penalty: float = (
                        1e-6
                        if next_hub == current_hub and next_hub != self.start
                        else 0.0
                    )

                    heapq.heappush(
                        waiting_list,
                        (end_turn + score_h + wait_penalty, next_hub, end_turn)
                    )

        return None

    def get_traffic_plan(self) -> dict[str, list[str]]:
        flight_plan: dict[str, list[str]] = {}
        self.flight_log.clear()
        self.link_log.clear()

        for i in range(self.map_data.glb_drones.nb_drone):
            drone: str = f"D{i}"
            result = self.find_path()

            if result is None:
                flight_plan[drone] = [self.start]
                continue

            path, path_states = result
            flight_plan[drone] = path

            for idx, step in enumerate(path):
                self.flight_log[(step, idx)] = (
                    self.flight_log.get((step, idx), 0) + 1
                )

            for j in range(len(path_states) - 1):
                cur_node: str = path_states[j][0]
                cur_t: int = path_states[j][1]
                nxt_node: str = path_states[j + 1][0]
                nxt_t: int = path_states[j + 1][1]

                if cur_node != nxt_node:
                    for t in range(cur_t, nxt_t + 1):
                        self.link_log[(cur_node, nxt_node, t)] = (
                            self.link_log.get((cur_node, nxt_node, t), 0) + 1
                        )
                        self.link_log[(nxt_node, cur_node, t)] = (
                            self.link_log.get((nxt_node, cur_node, t), 0) + 1
                        )

        return flight_plan
