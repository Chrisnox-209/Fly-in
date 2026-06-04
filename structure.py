from typing import Optional


class Node:
    """Base class representing a physical location in the network.

    Attributes:
        name (str): Unique identifier for the node.
        id (int): Numerical ID for internal logic.
        x (int): The x-coordinate of the node.
        y (int): The y-coordinate of the node.
        line_number (int): The line number in the source file where
        this node was defined.
        color (Optional[str]): Color assigned to the node, if any.
        max_drones (int): Maximum number of drones that can be
        present on this node simultaneously.
        zone (str): Zone type affecting routing (e.g., 'normal',
        'blocked', 'priority', 'restricted').
    """

    def __init__(self, name: str, id: int, x: int, y: int,
                 line_number: int, color: Optional[str] = None,
                 max_drones: int = 1, zone: str = "normal") -> None:
        """Initializes the Node instance.

        Args:
            name (str): The name of the node.
            id (int): The numerical identifier.
            x (int): The horizontal coordinate.
            y (int): The vertical coordinate.
            line_number (int): Line number in the parsed file.
            color (Optional[str], optional): Color property. Defaults to None.
            max_drones (int, optional): Capacity constraint. Defaults to 1.
            zone (str, optional): Zone type. Defaults to "normal".
        """
        self.name: str = name
        self.id: int = id
        self.x: int = x
        self.y: int = y
        self.line_number: int = line_number
        self.color: Optional[str] = color
        self.max_drones: int = max_drones
        self.zone: str = zone


class Hub(Node):
    """Represents a standard intermediate waypoint or hub in the network."""
    pass


class Start(Node):
    """Represents the designated starting hub for all drones."""
    pass


class End(Node):
    """Represents the designated destination hub (goal) for all drones."""
    pass


class Drone:
    """Represents the global fleet of drones in the simulation.

    Attributes:
        drone_count (int): The total number of drones to route.
        line_number (int): The line number in the parsed file.
        position (Optional[int]): Specific position ID if assigned.
    """

    def __init__(self, drone_count: int, line_number: int,
                 position: int | None = None) -> None:
        """Initializes the Drone configuration.

        Args:
            drone_count (int): Total number of drones.
            line_number (int): Line number in the parsed file.
            position (Optional[int], optional): Initial position index.
            Defaults to None.
        """
        self.drone_count: int = drone_count
        self.line_number: int = line_number
        self.position: int | None = position


class Connection:
    """Represents a bidirectional link between two hubs in the network.

    Attributes:
        connection_a (str): The name of the first hub.
        connection_b (str): The name of the second hub.
        line_number (int): The line number in the parsed file.
        max_link_capacity (int): The maximum number of drones that can
        traverse this connection per turn.
    """

    def __init__(self, connection_a: str, connection_b: str,
                 line_number: int, max_link_capacity: int = 1) -> None:
        """Initializes a Connection link.

        Args:
            connection_a (str): Name of the first connected node.
            connection_b (str): Name of the second connected node.
            line_number (int): Line number in the parsed file.
            max_link_capacity (int, optional): Drone capacity per turn.
            Defaults to 1.
        """
        self.connection_a: str = connection_a
        self.connection_b: str = connection_b
        self.line_number: int = line_number
        self.max_link_capacity: int = max_link_capacity
