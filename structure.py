from typing import Optional


class Node:
    def __init__(self, name: str, x: int, y: int,
                 nb_line: int, color=None,
                 max_drones: int = 1, zone: str = "normal") -> None:
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.nb_line: int = nb_line
        self.color: Optional[str] = color
        self.max_drones: int = max_drones
        self.zone: str = zone


class Hub(Node):
    pass


class Start(Node):
    pass


class End(Node):
    pass


class Drone:
    def __init__(self, nb_drone: int, nb_line: int,
                 position: int = None) -> None:
        self.nb_drone: int = nb_drone
        self.nb_line: int = nb_line
        self.position: Optional[str] = position


class Connection:
    def __init__(self, connection_a: str, connection_b: str,
                 nb_line: int, max_link_capacity=1) -> None:
        self.connection_a: str = connection_a
        self.connection_b: str = connection_b
        self.nb_line: int = nb_line
        self.max_link_capacity: int = max_link_capacity
