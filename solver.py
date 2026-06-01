from typing import Any
import math
import heapq


class TrafficController:
    def __init__(self, map_data: Any) -> None:
        self.map_data: Any = map_data
        self.hub_details: dict[str, tuple[int, str, int, int]] = {}
        self.address_book: dict[str, set[str]] = {}
        self.reservations: dict[tuple[str, int], int] = {}
        self.start: str = map_data.glb_start.name
        self.end: str = map_data.glb_end.name

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
        result: float = math.sqrt(
            (xb - xa)**2 + (yb - ya)**2)
        return result

    def find_path(self, start_turn: int) -> list[str] | None:
        waiting_list: list = []
        path_finaly: list = []
        origin: dict = {self.start: None}
        g_score: dict = {self.start: start_turn}
        heapq.heappush(waiting_list, (0, self.start))
        end_position: tuple[int, int] = (self.map_data.glb_end.x,
                                         self.map_data.glb_end.y)
        end: str = self.map_data.glb_end.name

        while waiting_list:
            score: int
            hub: str
            score, hub = heapq.heappop(waiting_list)

            if hub == self.end:
                path_finaly.append(self.map_data.glb_end.name)
                for i in range(len(origin)):
                    if origin[end] is not None:
                        path_finaly.append(origin[end])
                        end = origin[end]
                path_finaly.reverse()
                return path_finaly

            if hub in self.address_book:
                for hub_next in self.address_book[hub]:
                    
                    # 1. On lit le type de zone du prochain hub
                    zone_type: str = self.hub_details[hub_next][1]
                    
                    # 2. ZONE BLOCKED : On passe directement au voisin suivant
                    if zone_type == "blocked":
                        continue
                        
                    # 3. CALCUL DU COÛT RÉEL (Les tours)
                    step_cost: int = 1 # Coût par défaut (normal et priority)
                    if zone_type == "restricted":
                        step_cost = 2
                        
                    # On calcule le vrai temps de trajet (g_score)
                    g_current: int = g_score[hub] + step_cost
                    
                    
                    max_capacity: int = self.hub_details[hub_next][0]
                    current_occupancy: int = self.reservations.get((hub_next, g_current), 0)
                    
                    if current_occupancy >= max_capacity:
                        continue

                    if (hub_next not in g_score or g_current < g_score[hub_next]):
                        g_score[hub_next] = g_current
                        origin[hub_next] = hub

                        hub_position: tuple = (self.hub_details[hub_next][-2],
                                               self.hub_details[hub_next][-1])
                        score_h: float = self.score(
                            hub_position[0],
                            hub_position[1],
                            end_position[0],
                            end_position[1])
                            
                        # 4. LE SCORE FINAL AVEC L'ATTRAIT "PRIORITY"
                        score_f: float = g_current + score_h
                        
                        if zone_type == "priority":
                            # L'aimant algorithmique : on abaisse artificiellement le score 
                            # final pour que heapq le place en haut de la liste d'attente !
                            score_f -= 0.5
                        heapq.heappush(waiting_list, (score_f, hub_next))
        return None

    def trafic_drones(self) -> dict:
        flight_plan: dict = {}
        for i in range(self.map_data.glb_drones.nb_drone):
            drone: str = "D" + str(i)
            
            # CHAQUE DRONE REÇOIT UN TOUR DE DÉPART DIFFÉRENT (0, 1, 2, 3...)
            start_turn: int = i 
            path: list[str] | None = self.find_path(start_turn)
            
            if path is not None:
                sleep_list = [self.start] * start_turn
                flight_plan[drone] = sleep_list + path
                
                # ON ENREGISTRE LES RÉSERVATIONS EN COMMENÇANT AU BON TOUR
                current_turn: int = start_turn
                for hub_step in path:
                    self.reservations[(hub_step, current_turn)] = self.reservations.get((hub_step, current_turn), 0) + 1
                    
                    # (Note : Si la zone est restricted, pense à faire += 2 ici)
                    current_turn += 1 
                    
        return flight_plan