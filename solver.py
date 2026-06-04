import heapq
from parser import Global
from structure import Hub, Connection


class TrafficController:
    """Manages the pathfinding and scheduling of drones across the network.

    Uses an A* algorithm with a time-expanded state space to route drones
    while respecting node and connection capacity limits.
    """
    def __init__(self, map_data: Global) -> None:
        """Initializes the TrafficController with the parsed map data.

        Args:
            map_data (Global): The parsed Global map model containing
            all hubs and connections.
        """
        self.map_data: Global = map_data
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

        hub: 'Hub'  # Type from structure.py
        for hub in map_data.glb_hub:
            self.address_book[hub.name] = set()
            self.hub_details[hub.name] = (
                hub.max_drones,
                hub.zone,
                float(hub.x),
                float(hub.y)
            )

        connection: 'Connection'  # Type from structure.py
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

            wp_name: str = f"wp_{node_a}_{node_b}"
            self.hub_details[wp_name] = (
                capacity,
                "priority",
                (x_a + x_b) / 2.0,
                (y_a + y_b) / 2.0
            )
            self.address_book[wp_name] = set()

            self.generated_waypoints.append(
                (wp_name, node_a, node_b, 0.5)
            )

            self.address_book[node_a].add(wp_name)
            self.address_book[wp_name].add(node_a)
            self.link_capacities[(node_a, wp_name)] = capacity
            self.link_capacities[(wp_name, node_a)] = capacity

            self.address_book[wp_name].add(node_b)
            self.address_book[node_b].add(wp_name)
            self.link_capacities[(wp_name, node_b)] = capacity
            self.link_capacities[(node_b, wp_name)] = capacity

        # Dijkstra to find shortest path distance from self.end to all hubs
        self.distance_to_end: dict[str, float] = {}
        dijkstra_queue: list[tuple[float, str]] = [(0.0, self.end)]
        while dijkstra_queue:
            dist: float
            node: str
            dist, node = heapq.heappop(dijkstra_queue)
            if node in self.distance_to_end:
                continue
            self.distance_to_end[node] = dist
            neighbor: str
            for neighbor in self.address_book[node]:
                if neighbor not in self.distance_to_end:
                    # In forward path, the drone enters 'node' from 'neighbor'.
                    # So the cost is the zone_score of 'node'.
                    zone_score: int = self.get_zone_score(
                        self.hub_details[node][1]
                    )
                    if zone_score > 0:
                        heapq.heappush(
                            dijkstra_queue, (dist + zone_score, neighbor)
                        )

    @staticmethod
    def get_zone_score(zone: str) -> int:
        """Determines the traversal time penalty for a given zone type.

        Args:
            zone (str): The zone string (e.g., 'blocked', 'restricted').

        Returns:
            int: The number of turns required to traverse the
            zone (0 if blocked).
        """
        if zone == "blocked":
            return 0
        if zone == "restricted":
            return 2
        if zone == "priority":
            return 1
        return 1

    def find_path(self) -> tuple[list[str], list[tuple[str, int]]] | None:
        """Finds the optimal path for a single drone avoiding collisions.

        Uses the A* algorithm over a time-expanded state
        graph to ensure the drone
        reaches the destination without exceeding hub or
        connection capacities at
        any given turn.

        Returns:
            tuple[list[str], list[tuple[str, int]]] | None:
                A tuple containing the list of hubs visited per turn,
                and a list
                of the state transitions (hub, turn),
                or None if no path exists.
        """
        waiting_list: list[tuple[float, float, str, int]] = []
        initial_state: tuple[str, int] = (self.start, 0)

        origin: dict[tuple[str, int], tuple[str, int] | None] = {
            initial_state: None
        }
        g_score: dict[tuple[str, int], float] = {initial_state: 0.0}

        heapq.heappush(waiting_list, (0.0, 0.0, self.start, 0))

        while waiting_list:
            _: float
            g_val: float
            current_hub: str
            current_turn: int
            _, g_val, current_hub, current_turn = heapq.heappop(waiting_list)

            if current_turn > 2000:
                return None

            current_state: tuple[str, int] = (current_hub, current_turn)

            if g_val > g_score.get(current_state, float('inf')):
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
                hub_full: bool = False
                if next_hub != self.start:
                    t: int
                    for t in range(current_turn + 1, end_turn + 1):
                        drones_count_t: int = self.flight_log.get((
                            next_hub, t), 0)
                        if drones_count_t >= capacity_max:
                            hub_full = True
                            break

                if hub_full:
                    continue

                if next_hub != current_hub:
                    route_cap: int = self.link_capacities[(
                        current_hub, next_hub
                    )]
                    route_full: bool = False
                    tt: int
                    for tt in range(current_turn, end_turn):
                        if self.link_log.get((current_hub, next_hub, tt),
                                             0) >= route_cap:
                            route_full = True
                            break
                    if route_full:
                        continue

                wait_penalty: float = (
                    1e-6
                    if next_hub == current_hub
                    else 0.0
                )
                h_next: float = self.distance_to_end.get(next_hub,
                                                         float('inf'))
                h_curr: float = self.distance_to_end.get(current_hub,
                                                         float('inf'))
                backtrack_penalty: float = 2.0 if h_next > h_curr else 0.0

                next_g: float = (
                    g_val + zone_score + wait_penalty + backtrack_penalty
                )

                if next_state not in g_score or next_g < g_score[next_state]:
                    g_score[next_state] = next_g
                    origin[next_state] = current_state

                    score_h: float = self.distance_to_end.get(
                        next_hub, float('inf')
                    )

                    heapq.heappush(
                        waiting_list,
                        (next_g + score_h, next_g, next_hub, end_turn)
                    )

        return None

    def get_traffic_plan(self) -> dict[str, list[str]]:
        """Generates flight plans for all drones in the simulation.

        Iterates over the total number of drones and sequentially
        assigns them paths
        while updating the global flight and link logs to prevent
        future collisions.

        Returns:
            dict[str, list[str]]: A dictionary mapping each
            drone ID (e.g., 'D0')
                to its sequence of hub visits turn-by-turn.

        Raises:
            ValueError: If no valid path can be found for a drone.
        """
        flight_plan: dict[str, list[str]] = {}
        self.flight_log.clear()
        self.link_log.clear()

        i: int
        for i in range(self.map_data.glb_drones.drone_count):
            drone_id: str = f"D{i}"
            res: tuple[list[str], list[
                tuple[str, int]]] | None = self.find_path()
            if res is None:
                raise ValueError("Impossible to resolve map")

            path: list[str] = res[0]
            states: list[tuple[str, int]] = res[1]

            flight_plan[drone_id] = path

            t_val: int
            h_val: str
            for h_val, t_val in states:
                self.flight_log[(h_val, t_val)] = self.flight_log.get(
                    (h_val, t_val), 0
                ) + 1

            idx: int
            for idx in range(len(states) - 1):
                curr_h: str = states[idx][0]
                curr_t: int = states[idx][1]
                next_h: str = states[idx+1][0]
                next_t: int = states[idx+1][1]

                if curr_h != next_h:
                    tt: int
                    for tt in range(curr_t, next_t):
                        self.link_log[(curr_h, next_h, tt)] = (
                            self.link_log.get((curr_h, next_h, tt), 0) + 1
                        )
                        self.link_log[(next_h, curr_h, tt)] = (
                            self.link_log.get((next_h, curr_h, tt), 0) + 1
                        )
        return flight_plan
