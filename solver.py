import heapq
from typing import Optional
from parser import Global
from structure import Node, Connection


class TrafficController:
    """Routes and schedules drones across the map.

    Phase 1 — Dijkstra (backward from end): precomputes the minimum
    distance from every hub to the goal. Used as the A* heuristic.

    Phase 2 — A* (time-expanded): finds the optimal path for each drone,
    considering the current turn as part of the state.

    Phase 3 — Reservations: after each drone is routed, its path is
    committed to logs so the next drone routes around it.
    """

    def __init__(self, map_data: Global) -> None:
        """Initializes the controller and runs the setup.

        Args:
            map_data (Global): The parsed map data.
        """
        self.map_data: Global = map_data
        self.hub_details: dict[str, tuple[int, str, float, float]] = {}
        self.address_book: dict[str, set[str]] = {}
        self.start: str = map_data.glb_start.name
        self.end: str = map_data.glb_end.name
        self.link_capacities: dict[tuple[str, str], int] = {}
        self.parent_conn: dict[object, tuple[str, str]] = {}
        self.hub_usage_log: dict[tuple[str, int], int] = {}
        self.link_usage_log: dict[tuple[tuple[str, str], int], int] = {}
        self.distance_to_end: dict[str, float] = {}
        self.generated_waypoints: list[tuple[str, str, str, float]] = []
        self.total_simulation_turns: int = 0

        self.setup_hubs()
        self.setup_connections()
        self.compute_dijkstra()

    def setup_hubs(self) -> None:
        """Registers all hubs (start, end, and intermediate) internally."""
        all_nodes: list[Node] = (
            [self.map_data.glb_start, self.map_data.glb_end]
            + list(self.map_data.glb_hub)
        )
        node: Node
        for node in all_nodes:
            self.hub_details[node.name] = (
                node.max_drones,
                node.zone,
                float(node.x),
                float(node.y),
            )
            self.address_book[node.name] = set()

    def setup_connections(self) -> None:
        """Registers connections and creates intermediate waypoint nodes.

        For every connection A-B a waypoint wp_A_B is inserted at the
        midpoint. This lets the solver track drones in transit separately
        from drones sitting at a hub.
        """
        xa: float
        ya: float
        xb: float
        yb: float
        conn: Connection
        for conn in self.map_data.glb_connection:
            a: str = conn.connection_a
            b: str = conn.connection_b
            cap: int = conn.max_link_capacity
            id_canonical: tuple[str, str] = (min(a, b), max(a, b))

            self.address_book[a].add(b)
            self.address_book[b].add(a)
            self.link_capacities[(a, b)] = cap
            self.link_capacities[(b, a)] = cap
            self.parent_conn[(a, b)] = id_canonical
            self.parent_conn[(b, a)] = id_canonical

            wp: str = f"wp_{a}_{b}"
            xa, ya = self.hub_details[a][2], self.hub_details[a][3]
            xb, yb = self.hub_details[b][2], self.hub_details[b][3]
            mid_x: float = (xa + xb) / 2
            mid_y: float = (ya + yb) / 2
            self.hub_details[wp] = (cap, "priority", mid_x, mid_y)
            self.address_book[wp] = set()
            self.generated_waypoints.append((wp, a, b, 0.5))

            src_node: str
            dst_node: str
            for src_node, dst_node in [(a, wp), (wp, a), (wp, b), (b, wp)]:
                self.address_book[src_node].add(dst_node)
                self.link_capacities[(src_node, dst_node)] = cap
                self.parent_conn[(src_node, dst_node)] = id_canonical

            self.parent_conn[wp] = id_canonical

    # Phase 1: Dijkstra
    def compute_dijkstra(self) -> None:
        """Runs Dijkstra backward from the end hub.

        Fills self.distance_to_end[hub] with the minimum cost
        to reach the end hub from each reachable hub.
        """
        queue: list[tuple[float, str]] = [(0.0, self.end)]

        while queue:
            dist: float
            node: str
            dist, node = heapq.heappop(queue)

            if node in self.distance_to_end:
                continue
            self.distance_to_end[node] = dist

            neighbor: str
            for neighbor in self.address_book[node]:
                if neighbor in self.distance_to_end:
                    continue
                cost: float = self.zone_cost(self.hub_details[node][1])
                if cost > 0:
                    heapq.heappush(queue, (dist + cost, neighbor))

    @staticmethod
    def zone_cost(zone: str) -> float:
        """Returns the turn cost to enter a zone.

        Args:
            zone (str): Zone type name.

        Returns:
            int: 0 for blocked, 2 for restricted, 1 otherwise.
        """
        if zone == "blocked":
            return 0.0
        if zone == "restricted":
            return 2.0
        if zone == "normal":
            return 1.0
        return 0.5

    # Phase 2: A*
    def compute_a_star(
        self,
    ) -> Optional[tuple[list[str], list[tuple[str, int]]]]:
        """Finds the optimal path for one drone using time-expanded A*.

        The state is (hub_name, turn). The heuristic is the Dijkstra
        distance precomputed in Phase 1.

        Returns:
            A (path, states) tuple, or None if no path exists within
            2000 turns.
        """

        origin: dict[tuple[str, int], Optional[tuple[str, int]]] = {
            (self.start, 0): None
        }
        g_score: dict[tuple[str, int], float] = {(self.start, 0): 0.0}

        queue: list[tuple[float, float, str, int]] = [
            (0.0, 0.0, self.start, 0)
        ]

        while queue:
            f: float
            g: float
            hub: str
            turn: int
            f, g, hub, turn = heapq.heappop(queue)

            if turn > 2000:
                return None

            state: tuple[str, int] = (hub, turn)

            if g > g_score.get(state, float("inf")):
                continue

            if hub == self.end:
                return self.rebuild_path(state, origin)

            prev_hub: Optional[str] = None
            prev_state: Optional[tuple[str, int]] = origin.get(state)
            while prev_state is not None:
                if prev_state[0] != hub:
                    prev_hub = prev_state[0]
                    break
                prev_state = origin.get(prev_state)

            neighbors: list[str] = list(self.address_book[hub])
            if not hub.startswith("wp_"):
                neighbors.append(hub)

            next_hub: str
            for next_hub in neighbors:
                if next_hub == prev_hub:
                    continue

                else:
                    cost: float = self.zone_cost(self.hub_details[next_hub][1])

                if cost == 0:
                    continue

                end_turn: int = turn + 1
                next_state: tuple[str, int] = (next_hub, end_turn)

                if self.hub_is_full(next_hub, turn, end_turn):
                    continue

                if next_hub != hub and self.link_is_full(
                    hub, next_hub, turn, end_turn
                ):
                    continue

                penalty: float = 0.0
                if next_hub == hub:
                    penalty += 2.0

                h_now: float = self.distance_to_end.get(hub, float("inf"))
                h_next: float = self.distance_to_end.get(
                    next_hub, float("inf")
                )
                if h_next > h_now:
                    penalty += 8.0

                next_g: float = g + cost + penalty

                if next_g < g_score.get(next_state, float("inf")):
                    g_score[next_state] = next_g
                    origin[next_state] = state
                    f = next_g + h_next
                    heapq.heappush(queue, (f, next_g, next_hub, end_turn))

        return None

    def hub_is_full(
        self, hub: str, current_turn: int, end_turn: int
    ) -> bool:
        """Returns True if the hub is already at capacity during the move.

        Args:
            hub (str): Hub to check.
            current_turn (int): Turn the drone departs.
            end_turn (int): Turn the drone arrives.

        Returns:
            bool: True if full, False if space is available.
        """

        if hub == self.start or hub == self.end:
            return False

        max_cap: int = self.hub_details[hub][0]
        t: int
        for t in range(current_turn + 1, end_turn + 1):
            if self.hub_usage_log.get((hub, t), 0) >= max_cap:
                return True
        return False

    def link_is_full(
        self, src: str, dst: str, current_turn: int, end_turn: int
    ) -> bool:
        """Returns True if the link is already at capacity during the move.

        Args:
            src (str): Departure hub.
            dst (str): Destination hub.
            current_turn (int): Turn the drone departs.
            end_turn (int): Turn the drone arrives.

        Returns:
            bool: True if full, False if space is available.
        """
        cap: int = self.link_capacities[(src, dst)]
        canonical: Optional[tuple[str, str]] = self.parent_conn.get((src, dst))

        if canonical is None:
            return False

        t: int
        for t in range(current_turn, end_turn):
            if self.link_usage_log.get((canonical, t), 0) >= cap:
                return True
        return False

    def rebuild_path(
        self,
        final_state: tuple[str, int],
        origin: dict[tuple[str, int], Optional[tuple[str, int]]],
    ) -> tuple[list[str], list[tuple[str, int]]]:
        """Rebuilds the list of states from goal back to start.

        Args:
            final_state (tuple[str, int]): The goal state reached.
            origin (dict): Parent-state mapping from A*.

        Returns:
            A (path, states) tuple where path[t] is the hub at turn t.
        """
        states: list[tuple[str, int]] = []
        state: Optional[tuple[str, int]] = final_state

        while state is not None:
            states.append(state)
            state = origin.get(state)

        states.reverse()

        path: list[str] = [states[0][0]]
        i: int
        for i in range(len(states) - 1):
            hub_next: str = states[i + 1][0]
            turns_spent: int = states[i + 1][1] - states[i][1]
            for _ in range(turns_spent):
                path.append(hub_next)

        return path, states

    # Phase 3: planning flight
    def get_traffic_plan(self) -> dict[str, list[str]]:
        """Generates flight plans for every drone one by one.

        After each drone's path is found, its occupancy is committed to
        the reservation logs so the next drone routes around it.

        Returns:
            dict[str, list[str]]: drone_id -> list of hubs per turn.

        Raises:
            ValueError: If no path can be found for a drone.
        """
        flight_plan: dict[str, list[str]] = {}
        self.hub_usage_log.clear()
        self.link_usage_log.clear()

        i: int
        for i in range(self.map_data.glb_drones.drone_count):
            result: tuple[list[str],
                          list[tuple[str, int]]] | None = self.compute_a_star()
            if result is None:
                raise ValueError("Impossible to resolve map")

            path: list[str]
            states: list[tuple[str, int]]
            path, states = result
            drone_id: str = f"D{i}"
            flight_plan[drone_id] = path

            state: tuple[str, int]
            for state in states:
                self.hub_usage_log[state] = (
                    self.hub_usage_log.get(state, 0) + 1
                )

            last_hub: str
            last_turn: int
            last_hub, last_turn = states[-1]
            if last_hub == self.end:
                for t in range(last_turn + 1, 2000):
                    self.hub_usage_log[(self.end,
                                        t)] = self.hub_usage_log.get(
                                            (self.end, t), 0) + 1
            j: int
            src: str
            t_src: int
            dst: str
            t_dst: int
            for j in range(len(states) - 1):
                src, t_src = states[j]
                dst, t_dst = states[j + 1]

                if src == dst:
                    continue

                ck: Optional[tuple[str, str]] = self.parent_conn.get(
                    (src, dst)
                )
                if ck is not None:
                    t: int
                    for t in range(t_src, t_dst):
                        self.link_usage_log[(ck, t)] = (
                            self.link_usage_log.get((ck, t), 0) + 1
                        )

        if flight_plan:
            max_path_length: int = 0

            for path in flight_plan.values():
                path_length: int = len(path)

                if path_length > max_path_length:
                    max_path_length = path_length

            self.total_simulation_turns = max_path_length - 1
        else:
            self.total_simulation_turns = 0
        return flight_plan

    def get_total_turns(self) -> int:
        return self.total_simulation_turns
