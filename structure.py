from typing import Optional


class Node:
    def __init__(self, name: str, id: int, x: int, y: int,
                 nb_line: int, color: Optional[str] = None,
                 max_drones: int = 1, zone: str = "normal") -> None:
        self.name: str = name
        self.id: int = id
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
                 position: int | None = None) -> None:
        self.nb_drone: int = nb_drone
        self.nb_line: int = nb_line
        self.position: int | None = position


class Connection:
    def __init__(self, connection_a: str, connection_b: str,
                 nb_line: int, max_link_capacity: int = 1) -> None:
        self.connection_a: str = connection_a
        self.connection_b: str = connection_b
        self.nb_line: int = nb_line
        self.max_link_capacity: int = max_link_capacity
