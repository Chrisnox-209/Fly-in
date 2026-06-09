import heapq
from typing import Dict, List, Tuple, Set, Optional, Union
from parser import Global
from structure import Hub, Connection


class TrafficController:
    """
    Manages the routing and scheduling of drones.

    This class uses the Dijkstra algorithm to precompute distances.
    Then, it uses the A* algorithm to find paths for each drone.
    It avoids collisions by checking capacities.
    """

    def __init__(self, map_data: Global) -> None:
        """
        Initializes the TrafficController.

        Args:
            map_data (Global): The parsed map data.
        """
        self.map_data: Global = map_data
        self.hub_details: Dict[str, Tuple[int, str, float, float]] = {}
        self.address_book: Dict[str, Set[str]] = {}
        self.start: str = map_data.glb_start.name
        self.end: str = map_data.glb_end.name
        self.link_capacities: Dict[Tuple[str, str], int] = {}

        self.flight_log: Dict[Tuple[str, int], int] = {}
        self.link_log: Dict[Tuple[str, str, int], int] = {}
        self.connection_log: Dict[Tuple[Tuple[str, str], int], int] = {}

        self.parent_conn: Dict[
            Union[str, Tuple[str, str]], Tuple[str, str]
        ] = {}

        self.generated_waypoints: List[Tuple[str, str, str, float]] = []

        self.distance_to_end: Dict[str, float] = {}

        self.setup_hubs()
        self.setup_connections()
        self.compute_dijkstra()

    def setup_hubs(self) -> None:
        """
        Sets up the hubs in the internal dictionaries.
        """
        self.hub_details[self.map_data.glb_start.name] = (
            self.map_data.glb_start.max_drones,
            self.map_data.glb_start.zone,
            float(self.map_data.glb_start.x),
            float(self.map_data.glb_start.y)
        )
        self.hub_details[self.map_data.glb_end.name] = (
            self.map_data.glb_end.max_drones,
            self.map_data.glb_end.zone,
            float(self.map_data.glb_end.x),
            float(self.map_data.glb_end.y)
        )

        self.address_book[self.map_data.glb_start.name] = set()
        self.address_book[self.map_data.glb_end.name] = set()

        hub: Hub
        for hub in self.map_data.glb_hub:
            self.address_book[hub.name] = set()
            self.hub_details[hub.name] = (
                hub.max_drones,
                hub.zone,
                float(hub.x),
                float(hub.y)
            )

    def setup_connections(self) -> None:
        """
        Sets up the connections and waypoints in the internal dictionaries.
        """
        connection: Connection
        for connection in self.map_data.glb_connection:
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

            conn_key: Tuple[str, str] = (
                min(node_a, node_b), max(node_a, node_b)
            )
            self.parent_conn[(node_a, node_b)] = conn_key
            self.parent_conn[(node_b, node_a)] = conn_key

            wp_name: str = f"wp_{node_a}_{node_b}"
            self.hub_details[wp_name] = (
                capacity,
                "priority",
                (x_a + x_b) / 2.0,
                (y_a + y_b) / 2.0
            )
            self.address_book[wp_name] = set()

            self.generated_waypoints.append((wp_name, node_a, node_b, 0.5))

            self.address_book[node_a].add(wp_name)
            self.address_book[wp_name].add(node_a)
            self.link_capacities[(node_a, wp_name)] = capacity
            self.link_capacities[(wp_name, node_a)] = capacity

            self.address_book[wp_name].add(node_b)
            self.address_book[node_b].add(wp_name)
            self.link_capacities[(wp_name, node_b)] = capacity
            self.link_capacities[(node_b, wp_name)] = capacity

            self.parent_conn[(node_a, wp_name)] = conn_key
            self.parent_conn[(wp_name, node_a)] = conn_key
            self.parent_conn[(wp_name, node_b)] = conn_key
            self.parent_conn[(node_b, wp_name)] = conn_key
            self.parent_conn[wp_name] = conn_key

    def compute_dijkstra(self) -> None:
        """
        Computes the shortest path from the end node to all other nodes.

        It uses the Dijkstra algorithm. The results are stored in
        self.distance_to_end.
        """
        self.distance_to_end = {}
        dijkstra_queue: List[Tuple[float, str]] = []
        heapq.heappush(dijkstra_queue, (0.0, self.end))

        while len(dijkstra_queue) > 0:
            current_item: Tuple[float, str] = heapq.heappop(dijkstra_queue)
            dist: float = current_item[0]
            node: str = current_item[1]

            if node in self.distance_to_end:
                continue

            self.distance_to_end[node] = dist

            neighbor: str
            for neighbor in self.address_book[node]:
                if neighbor not in self.distance_to_end:
                    zone_type: str = self.hub_details[node][1]
                    zone_score: int = self.get_zone_score(zone_type)

                    if zone_score > 0:
                        new_dist: float = dist + float(zone_score)
                        heapq.heappush(dijkstra_queue, (new_dist, neighbor))

    @staticmethod
    def get_zone_score(zone: str) -> int:
        """
        Gets the time penalty for a given zone.

        Args:
            zone (str): The name of the zone.

        Returns:
            int: The time penalty in turns.
        """
        if zone == "blocked":
            return 0
        if zone == "restricted":
            return 2
        if zone == "priority":
            return 1
        return 1

    def get_previous_hub(
        self,
        current_state: Tuple[str, int],
        current_hub: str,
        origin: Dict[Tuple[str, int], Optional[Tuple[str, int]]]
    ) -> Optional[str]:
        """
        Retrieves the previous hub from the path history.

        Args:
            current_state (Tuple[str, int]): The current state.
            current_hub (str): The current hub name.
            origin (Dict[Tuple[str, int], Optional[Tuple[str, int]]]):
                The path history.

        Returns:
            Optional[str]: The previous hub name or None.
        """
        previous_hub: Optional[str] = None
        prev_state: Optional[Tuple[str, int]] = origin.get(current_state)

        while prev_state is not None:
            if prev_state[0] != current_hub:
                previous_hub = prev_state[0]
                break
            prev_state = origin.get(prev_state)

        return previous_hub

    def get_possible_neighbors(self, current_hub: str) -> List[str]:
        """
        Gets a list of all possible next hubs.

        Args:
            current_hub (str): The current hub name.

        Returns:
            List[str]: A list of neighbor hub names.
        """
        possible_neighbors: List[str] = []
        neighbor: str
        for neighbor in self.address_book[current_hub]:
            possible_neighbors.append(neighbor)

        # Allow waiting at the current hub if it is not a waypoint
        if not current_hub.startswith("wp_"):
            possible_neighbors.append(current_hub)

        return possible_neighbors

    def is_hub_full(
        self, next_hub: str, current_turn: int, end_turn: int
    ) -> bool:
        """
        Checks if the destination hub will be full during the transition.

        Args:
            next_hub (str): The destination hub name.
            current_turn (int): The turn the drone leaves.
            end_turn (int): The turn the drone arrives.

        Returns:
            bool: True if the hub is full, False otherwise.
        """
        if next_hub == self.start:
            return False

        capacity_max: int = self.hub_details[next_hub][0]

        t: int
        for t in range(current_turn + 1, end_turn + 1):
            drones_count_t: int = self.flight_log.get((next_hub, t), 0)
            if drones_count_t >= capacity_max:
                return True

        return False

    def is_route_full(
        self,
        current_hub: str,
        next_hub: str,
        current_turn: int,
        end_turn: int
    ) -> bool:
        """
        Checks if the route between two hubs will be full.

        Args:
            current_hub (str): The current hub name.
            next_hub (str): The destination hub name.
            current_turn (int): The turn the drone leaves.
            end_turn (int): The turn the drone arrives.

        Returns:
            bool: True if the route is full, False otherwise.
        """
        route_cap: int = self.link_capacities[(current_hub, next_hub)]
        conn_key_opt: Optional[Tuple[str, str]] = self.parent_conn.get(
            (current_hub, next_hub)
        )

        tt: int
        for tt in range(current_turn, end_turn):
            link_count: int = self.link_log.get(
                (current_hub, next_hub, tt), 0
            )
            if link_count >= route_cap:
                return True

            if conn_key_opt is not None:
                conn_count: int = self.connection_log.get(
                    (conn_key_opt, tt), 0
                )
                if conn_count >= route_cap:
                    return True

        return False

    def calculate_penalties(self, current_hub: str, next_hub: str) -> float:
        """
        Calculates waiting and backtracking penalties.

        Args:
            current_hub (str): The current hub name.
            next_hub (str): The next hub name.

        Returns:
            float: The total penalty score.
        """
        wait_penalty: float = 0.0
        if next_hub == current_hub:
            wait_penalty = 1e-6

        h_next: float = self.distance_to_end.get(next_hub, float('inf'))
        h_curr: float = self.distance_to_end.get(current_hub, float('inf'))

        backtrack_penalty: float = 0.0
        if h_next > h_curr:
            backtrack_penalty = 2.0

        return wait_penalty + backtrack_penalty

    def compute_a_star(
        self
    ) -> Optional[Tuple[List[str], List[Tuple[str, int]]]]:
        """
        Finds the optimal path for a single drone using the A* algorithm.

        Returns:
            Optional[Tuple[List[str], List[Tuple[str, int]]]]:
            A tuple containing the list of hubs visited and the
            list of state transitions, or None if no path exists.
        """
        waiting_list: List[Tuple[float, float, str, int]] = []
        initial_state: Tuple[str, int] = (self.start, 0)

        origin: Dict[Tuple[str, int], Optional[Tuple[str, int]]] = {}
        origin[initial_state] = None

        g_score: Dict[Tuple[str, int], float] = {}
        g_score[initial_state] = 0.0

        heapq.heappush(waiting_list, (0.0, 0.0, self.start, 0))

        while len(waiting_list) > 0:
            current_item: Tuple[
                float, float, str, int
            ] = heapq.heappop(waiting_list)

            g_val: float = current_item[1]
            current_hub: str = current_item[2]
            current_turn: int = current_item[3]

            if current_turn > 2000:
                return None

            current_state: Tuple[str, int] = (current_hub, current_turn)

            best_g_val: float = g_score.get(current_state, float('inf'))
            if g_val > best_g_val:
                continue

            previous_hub: Optional[str] = self.get_previous_hub(
                current_state, current_hub, origin
            )

            if current_hub == self.end:
                return self.reconstruct_path(current_state, origin)

            if current_hub not in self.address_book:
                continue

            possible_neighbors: List[str] = self.get_possible_neighbors(
                current_hub
            )

            next_hub: str
            for next_hub in possible_neighbors:
                if next_hub == previous_hub:
                    continue

                zone_score: int = 0
                if next_hub == current_hub:
                    zone_score = 1
                else:
                    zone_type: str = self.hub_details[next_hub][1]
                    zone_score = self.get_zone_score(zone_type)

                if zone_score == 0:
                    continue

                end_turn: int = current_turn + zone_score
                next_state: Tuple[str, int] = (next_hub, end_turn)

                hub_full: bool = self.is_hub_full(
                    next_hub, current_turn, end_turn
                )
                if hub_full:
                    continue

                if next_hub != current_hub:
                    route_full: bool = self.is_route_full(
                        current_hub, next_hub, current_turn, end_turn
                    )
                    if route_full:
                        continue

                penalties: float = self.calculate_penalties(
                    current_hub, next_hub
                )

                next_g: float = g_val + float(zone_score) + penalties

                best_next_g: float = g_score.get(next_state, float('inf'))
                if next_g < best_next_g:
                    g_score[next_state] = next_g
                    origin[next_state] = current_state

                    score_h: float = self.distance_to_end.get(
                        next_hub, float('inf')
                    )
                    f_val: float = next_g + score_h

                    heapq.heappush(
                        waiting_list,
                        (f_val, next_g, next_hub, end_turn)
                    )

        return None

    def reconstruct_path(
        self,
        current_state: Tuple[str, int],
        origin: Dict[Tuple[str, int], Optional[Tuple[str, int]]]
    ) -> Tuple[List[str], List[Tuple[str, int]]]:
        """
        Reconstructs the path from the origin dictionary.

        Args:
            current_state (Tuple[str, int]): The final state.
            origin (Dict[Tuple[str, int], Optional[Tuple[str, int]]]):
                The path history.

        Returns:
            Tuple[List[str], List[Tuple[str, int]]]: The reconstructed path.
        """
        path_states: List[Tuple[str, int]] = []
        state: Optional[Tuple[str, int]] = current_state

        while state is not None:
            path_states.append(state)
            state = origin.get(state)

        # Reverse the list
        reversed_path_states: List[Tuple[str, int]] = []
        index: int = len(path_states) - 1
        while index >= 0:
            reversed_path_states.append(path_states[index])
            index -= 1

        final_path: List[str] = []
        final_path.append(reversed_path_states[0][0])

        i: int
        for i in range(len(reversed_path_states) - 1):
            step_turn: int = reversed_path_states[i][1]
            next_hub: str = reversed_path_states[i + 1][0]
            next_turn: int = reversed_path_states[i + 1][1]

            turn_diff: int = next_turn - step_turn
            j: int
            for j in range(turn_diff):
                final_path.append(next_hub)

        return final_path, reversed_path_states

    def get_traffic_plan(self) -> Dict[str, List[str]]:
        """
        Generates flight plans for all drones.

        Returns:
            Dict[str, List[str]]: A dictionary with the flight plan
            for each drone.

        Raises:
            ValueError: If a path cannot be found.
        """
        flight_plan: Dict[str, List[str]] = {}
        self.flight_log.clear()
        self.link_log.clear()
        self.connection_log.clear()

        i: int
        for i in range(self.map_data.glb_drones.drone_count):
            drone_id: str = f"D{i}"
            res: Optional[
                Tuple[List[str], List[Tuple[str, int]]]
            ] = self.compute_a_star()

            if res is None:
                raise ValueError("Impossible to resolve map")

            path: List[str] = res[0]
            states: List[Tuple[str, int]] = res[1]

            flight_plan[drone_id] = path

            state_item: Tuple[str, int]
            for state_item in states:
                h_val: str = state_item[0]
                t_val: int = state_item[1]

                current_flight_count: int = self.flight_log.get(
                    (h_val, t_val), 0
                )
                self.flight_log[(h_val, t_val)] = current_flight_count + 1

            idx: int
            for idx in range(len(states) - 1):
                curr_h: str = states[idx][0]
                curr_t: int = states[idx][1]
                next_h: str = states[idx + 1][0]
                next_t: int = states[idx + 1][1]

                if curr_h != next_h:
                    tt: int
                    for tt in range(curr_t, next_t):
                        curr_link_count: int = self.link_log.get(
                            (curr_h, next_h, tt), 0
                        )
                        self.link_log[
                            (curr_h, next_h, tt)
                        ] = curr_link_count + 1

                        rev_link_count: int = self.link_log.get(
                            (next_h, curr_h, tt), 0
                        )
                        self.link_log[
                            (next_h, curr_h, tt)
                        ] = rev_link_count + 1

                        ck: Optional[
                            Tuple[str, str]
                        ] = self.parent_conn.get((curr_h, next_h))

                        if ck is not None:
                            curr_conn_count: int = self.connection_log.get(
                                (ck, tt), 0
                            )
                            self.connection_log[
                                (ck, tt)
                            ] = curr_conn_count + 1

        return flight_plan
