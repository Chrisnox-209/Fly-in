import math
import random
import warnings
from enum import Enum
from typing import cast
from parser import Global
from structure import Hub, Connection, Node

import pygame
from pygame.font import Font
from pygame.sprite import Group

warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API"
)


class HubColor(Enum):
    """Enumeration of predefined hub colors and their corresponding
    RGB values."""

    YELLOW = (255, 255, 0)
    GREY = (128, 128, 128)
    RED = (255, 0, 0)
    ORANGE = (255, 165, 0)
    BROWN = (165, 42, 42)
    BLUE = (0, 0, 255)
    GREEN = (0, 128, 0)
    PINK = (255, 192, 203)
    CYAN = (0, 255, 255)
    PURPLE = (128, 0, 128)
    LIME = (0, 255, 0)
    MAGENTA = (255, 0, 255)
    GOLD = (255, 215, 0)
    BLACK = (0, 0, 0)
    MAROON = (128, 0, 0)
    DARKRED = (139, 0, 0)
    VIOLET = (238, 130, 238)
    CRIMSON = (220, 20, 60)
    RAINBOW = "dynamic"

    @property
    def rgb(self) -> pygame.Color | tuple[int, int, int]:
        if self == HubColor.RAINBOW:
            hue: int = (pygame.time.get_ticks() // 10) % 360
            color: pygame.Color = pygame.Color(0)
            color.hsva = (hue, 100, 100, 100)
            return color
        return cast(tuple[int, int, int], self.value)


class VisualNode(pygame.sprite.Sprite):
    """Represents a visual hub or node drawn on the simulation grid.

    Attributes:
        dict_x (dict[int, int]): Dictionary for logical to visual X conversion.
        dict_y (dict[int, int]): Dictionary for logical to visual Y conversion.
        name (str): The name of the node.
        zone_type (str): The node's special zone type.
        capacity (int): Maximum drone capacity.
        radius (int): Visually calculated radius based on capacity.
        image (pygame.Surface): The generated sprite surface.
        rect (pygame.Rect): The sprite's rectangular bounds.
    """

    def __init__(
        self,
        x: int,
        y: int,
        name: str,
        color: pygame.Surface | pygame.Color | tuple[int, int, int],
        dict_x: dict[int, int],
        dict_y: dict[int, int],
        base_radius: float,
        capacity: int,
        zone_type: str = "normal"
    ) -> None:
        """Initializes a VisualNode sprite.

        Args:
            x (int): Logical X grid coordinate.
            y (int): Logical Y grid coordinate.
            name (str): Name identifier for the node.
            color (pygame.Surface | pygame.Color | tuple[int, int, int]):
            The node's color.
            dict_x (dict[int, int]): X-coordinate mappings.
            dict_y (dict[int, int]): Y-coordinate mappings.
            base_radius (float): Base radius factor for scaling.
            capacity (int): The drone capacity limit.
            zone_type (str, optional): The zone designation.
            Defaults to "normal".
        """
        super().__init__()
        self.dict_x: dict[int, int] = dict_x
        self.dict_y: dict[int, int] = dict_y
        self.name: str = name
        self.zone_type: str = zone_type
        self.capacity: int = capacity

        percentage: float = 60 + (capacity - 1) * 5.5
        theoretical_radius: int = math.ceil(
            (base_radius * 0.8) * percentage / 100
        )
        max_radius: int = math.ceil(base_radius * 0.9)

        self.radius: int = min(theoretical_radius, max_radius)
        self.image: pygame.Surface = pygame.Surface(
            (self.radius * 2, self.radius * 2), pygame.SRCALPHA
        )

        if isinstance(color, pygame.Surface):
            pygame.draw.circle(
                self.image,
                (255, 255, 255, 255),
                (self.radius, self.radius),
                self.radius
            )
            self.image.blit(color, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        else:
            pygame.draw.circle(
                self.image,
                color,
                (self.radius, self.radius),
                self.radius
            )

        font: Font = pygame.font.SysFont("arial", 35, bold=True)
        capacity_text: str = str(capacity)
        text_surface: pygame.Surface = font.render(
            capacity_text, True, (45, 45, 45)
        )
        text_rect: pygame.Rect = text_surface.get_rect(
            center=(self.radius, self.radius)
        )
        self.image.blit(text_surface, text_rect)
        self.draw_zone_badge(self.radius)

        self.rect: pygame.Rect = self.image.get_rect()
        self.rect.center = (x, y)
        if self.radius < 21:
            raise ValueError("[ERROR] (MAP) "
                             f"radius too small -> {self.radius}")

    def draw_zone_badge(self, radius: int) -> None:
        if self.zone_type == "normal":
            return

        badge_radius: int = max(12, radius // 3)
        bx: int = int(radius + radius * 0.6)
        by: int = int(radius - radius * 0.6)
        font: Font = pygame.font.SysFont(
            "arial", int(badge_radius * 1.5), bold=True
        )

        bg_color: tuple[int, int, int]
        text: pygame.Surface

        if self.zone_type == "blocked":
            bg_color = (220, 20, 60)
            text = font.render("X", True, (255, 255, 255))
        elif self.zone_type == "restricted":
            bg_color = (255, 165, 0)
            text = font.render("!", True, (0, 0, 0))
        elif self.zone_type == "priority":
            bg_color = (0, 150, 255)
            text = font.render("P", True, (255, 255, 255))
        else:
            return

        pygame.draw.circle(
            self.image, (255, 255, 255), (bx, by), badge_radius + 2
        )
        pygame.draw.circle(self.image, bg_color, (bx, by), badge_radius)

        text_rect: pygame.Rect = text.get_rect(center=(bx, by))
        self.image.blit(text, text_rect)


class VisualDrone(pygame.sprite.Sprite):
    """Represents a flying drone animated on the Pygame screen.

    Handles movement interpolation between hubs, sprite animation (propellers),
    and logic for determining the current destination based on the flight plan.

    Attributes:
        name (str): Identifier for the drone.
        flight_plan (list[str]): Sequential list of hub names the drone visits.
        step (int): Current index in the flight plan.
        current_frame (float): Animation frame
        progress for the current movement.
        sprites (list[pygame.Surface]): Frames for the drone animation.
    """
    def __init__(
        self,
        name: str,
        x: float,
        y: float,
        dict_x: dict[int, int],
        dict_y: dict[int, int],
        radius: int,
        flight_plan: list[str],
        hub_info: dict[str, tuple[int, int]],
        step: int = 0
    ) -> None:
        """Initializes the VisualDrone sprite.

        Args:
            name (str): Identifier for the drone.
            x (float): Initial x-coordinate.
            y (float): Initial Y coordinate.
            dict_x (dict[int, int]): Node X-coordinate reference table.
            dict_y (dict[int, int]): Node Y-coordinate reference table.
            radius (int): Base size radius.
            flight_plan (list[str]): Planned hubs to visit turn-by-turn.
            hub_info (dict[str, tuple[int, int]]): Coordinates for all hubs.
            step (int, optional): Initial flight plan index. Defaults to 0.
        """
        super().__init__()
        drone_images: list[list[str]] = [
            ["assets/gold-1.png", "assets/gold-2.png",
             "assets/gold-3.png", "assets/gold-4.png"],
            ["assets/red-1.png", "assets/red-2.png",
             "assets/red-3.png", "assets/red-4.png"],
            ["assets/blue-1.png", "assets/blue-2.png",
             "assets/blue-3.png", "assets/blue-4.png"],
            ["assets/green-1.png", "assets/green-2.png",
             "assets/green-3.png", "assets/green-4.png"],
            ["assets/yellow-1.png", "assets/yellow-2.png",
             "assets/yellow-3.png", "assets/yellow-4.png"],
        ]
        self.dict_x: dict[int, int] = dict_x
        self.dict_y: dict[int, int] = dict_y
        self.name: str = name
        self.flight_plan: list[str] = flight_plan
        self.step: int = step
        self.hub_info: dict[str, tuple[int, int]] = hub_info

        self.frames_per_turn: int = 30
        self.current_frame: float = 0.0
        self.radius: int = radius

        chosen_paths: list[str] = random.choice(drone_images)
        self.sprites: list[pygame.Surface] = []

        width: int = self.radius
        height: float = self.radius / 1.21

        path: str
        for path in chosen_paths:
            img: pygame.Surface = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (width, height))
            self.sprites.append(img)

        self.current_sprite: float = 0.0
        self.propellers: float = 0.0

        self.image: pygame.Surface = self.sprites[0]
        self.rect: pygame.Rect = self.image.get_rect()

        self.x: float = float(x)
        self.y: float = float(y)
        self.rect.center = (int(self.x), int(self.y))

        self.angle: float = 270.0
        original_image: pygame.Surface = self.sprites[0]
        self.image = pygame.transform.rotate(original_image, self.angle)

    def set_angle(self, target_x: float, target_y: float) -> None:
        """Calculates and sets the rotation angle
        to face the target destination.

        Args:
            target_x (float): Target X-coordinate.
            target_y (float): Target Y-coordinate.
        """
        dx: float = target_x - self.x
        dy: float = target_y - self.y
        if dx == 0.0 and dy == 0.0:
            return

        calculated_angle: float = math.degrees(math.atan2(-dy, dx))
        offset: float = -90.0
        self.angle = calculated_angle + offset

    def update(self) -> None:
        """Updates the drone's position, rotation, and animation frame.

        Calculates linear interpolation between
        the current hub and the next hub
        based on the flight plan and frames per turn.
        """
        if self.step >= len(self.flight_plan):
            self.propellers = 0.0
            return

        current_hub_name: str = self.flight_plan[self.step]
        next_hub_name: str
        if self.step + 1 < len(self.flight_plan):
            next_hub_name = self.flight_plan[self.step + 1]
        else:
            next_hub_name = current_hub_name

        start_x: int
        start_y: int
        target_x: int
        target_y: int
        start_x, start_y = self.hub_info[current_hub_name]
        target_x, target_y = self.hub_info[next_hub_name]

        if current_hub_name != next_hub_name:
            self.set_angle(float(target_x), float(target_y))

        progression: float = self.current_frame / self.frames_per_turn
        if progression > 1.0:
            progression = 1.0

        if current_hub_name == next_hub_name:
            self.x = float(start_x)
            self.y = float(start_y)
            self.propellers = 0.6
        else:
            self.x = start_x + (target_x - start_x) * progression
            self.y = start_y + (target_y - start_y) * progression
            self.propellers = 2.0 if progression < 1.0 else 0.6

        self.current_frame += 1.3
        pause_frames: float = 15.0
        if self.current_frame >= self.frames_per_turn + pause_frames:
            self.current_frame = 0.0
            self.step += 1

        self.current_sprite += self.propellers
        if int(self.current_sprite) >= len(self.sprites):
            self.current_sprite = 0.0

        original_image: pygame.Surface = self.sprites[int(self.current_sprite)]
        self.image = pygame.transform.rotate(original_image, self.angle)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))


class Buttom_Gm:
    """A simple clickable button used in the game's simulation finish screen.

    Attributes:
        rect (pygame.Rect): Rectangular boundaries of the button.
        text (str): The label displayed on the button.
        color (tuple[int, int, int]): Background color RGB.
        font (Font): Pygame font for the label.
    """
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        color: tuple[int, int, int]
    ) -> None:
        """Initializes the Button.

        Args:
            x (int): X-coordinate.
            y (int): Y-coordinate.
            width (int): Button width.
            height (int): Button height.
            text (str): Label text.
            color (tuple[int, int, int]): Background color.
        """
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.text: str = text
        self.color: tuple[int, int, int] = color
        self.font: Font = pygame.font.SysFont("arial", 24, bold=True)

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(
            screen,
            self.color,
            self.rect,
            border_radius=12,
        )

        text_btn: pygame.Surface = self.font.render(
            self.text, True, (255, 255, 255)
        )
        text_rect: pygame.Rect = text_btn.get_rect(center=self.rect.center)
        screen.blit(text_btn, text_rect)


class GraphRenderer:
    """Handles the rendering of the simulation map,
    hubs, connections, and drones.

    Uses Pygame to draw a dynamic, interactive map of the entire network.

    Attributes:
        map_data (Global): Parsed map definition.
        screen_width (int): Target width for the Pygame window.
        screen_height (int): Target height for the Pygame window.
        all_sprites (pygame.sprite.Group): Group of all VisualNodes.
        drones_sprites (pygame.sprite.Group): Group of all VisualDrones.
    """
    def __init__(self, map_data: Global) -> None:
        """Initializes the GraphRenderer with the simulation map data.

        Args:
            map_data (Global): The parsed network data.
        """
        pygame.init()
        self.screen_width: int = 2832
        self.screen_height: int = 1504
        self.rainbow_texture: pygame.Surface = pygame.image.load(
            "assets/rainbow.jpg"
        ).convert_alpha()

        icon: pygame.Surface = pygame.image.load(
            "assets/icon.png"
        ).convert_alpha()
        pygame.display.set_icon(icon)
        pygame.display.set_caption("Fly_In")

        self.map_data: Global = map_data
        self.all_sprites: Group[VisualNode] = pygame.sprite.Group()
        self.drones_sprites: Group[VisualDrone] = pygame.sprite.Group()

        self.dict_x: dict[int, int] = {}
        self.dict_y: dict[int, int] = {}
        self.dict_x, self.dict_y = self.calculate_xy_coordinates()

        self.hub_info: dict[str, tuple[int, int]] = {}
        self.nodes: dict[str, VisualNode] = {}

        max_x: int = max(self.dict_x.values())
        min_x: int = min(self.dict_x.values())
        max_y: int = max(self.dict_y.values())
        min_y: int = min(self.dict_y.values())

        grid_x: int = abs(max_x - min_x) + 1
        grid_y: int = abs(max_y - min_y) + 1

        pos_x: float = self.screen_width / grid_x
        pos_y: float = self.screen_height / grid_y

        min_pos: float = min(pos_x, pos_y)
        base_radius: float = min_pos / 2

        self.create_hub(
            self.map_data.glb_start, min_x, max_y, pos_x, pos_y, base_radius
        )
        self.create_hub(
            self.map_data.glb_end, min_x, max_y, pos_x, pos_y, base_radius
        )

        for hub in self.map_data.glb_hub:
            self.create_hub(
                hub, min_x, max_y, pos_x, pos_y, base_radius
            )

    def create_hub(
        self,
        hub_data: Node,  # from structure.py
        min_x: int,
        max_y: int,
        pos_x: float,
        pos_y: float,
        base_radius: float
    ) -> None:
        col: int = hub_data.x - min_x
        pos_hub_x: float = (col * pos_x) + (pos_x / 2)
        line: int = max_y - hub_data.y
        pos_hub_y: float = (line * pos_y) + (pos_y / 2)

        self.hub_info[hub_data.name] = (int(pos_hub_x), int(pos_hub_y))

        percentage: float = 50 + (hub_data.max_drones - 1) * 5.5
        theoretical_radius: int = math.ceil(
            (base_radius * 0.8) * percentage / 100
        )
        max_radius: int = math.ceil(base_radius * 0.9)
        radius: int = min(theoretical_radius, max_radius)
        diameter: int = radius * 2

        hub_color: str | None = hub_data.color
        rgb: pygame.Surface | pygame.Color | tuple[int, int, int]

        if hub_color == "rainbow":
            rgb = pygame.transform.smoothscale(
                self.rainbow_texture, (diameter, diameter)
            )
        else:
            try:
                if hub_color is None:
                    color_enum: HubColor = HubColor.GREY
                else:
                    color_enum = HubColor[hub_color.upper()]
                rgb = color_enum.rgb
            except KeyError:
                rgb = (255, 255, 255)

        zone_type: str = getattr(hub_data, 'zone', 'normal')
        visual_node: VisualNode = VisualNode(
            int(pos_hub_x), int(pos_hub_y),
            hub_data.name,
            rgb,
            self.dict_x, self.dict_y,
            base_radius,
            hub_data.max_drones,
            zone_type=zone_type
        )
        self.all_sprites.add(visual_node)
        self.nodes[hub_data.name] = visual_node

    def draw_connections(self, surface: pygame.Surface) -> None:
        font: pygame.font.Font = pygame.font.SysFont("arial", 20, bold=True)
        connection: 'Connection'  # from structure.py
        for connection in self.map_data.glb_connection:
            start_x: int = self.hub_info[connection.connection_a][0]
            start_y: int = self.hub_info[connection.connection_a][1]
            end_x: int = self.hub_info[connection.connection_b][0]
            end_y: int = self.hub_info[connection.connection_b][1]
            pygame.draw.line(
                surface,
                (200, 200, 200),
                (start_x, start_y),
                (end_x, end_y),
                5
            )

            mid_x: int = (start_x + end_x) // 2
            mid_y: int = (start_y + end_y) // 2

            pygame.draw.circle(
                surface,
                (200, 200, 200),
                (mid_x, mid_y),
                16
            )

            text_surf: pygame.Surface = font.render(
                str(connection.max_link_capacity),
                True,
                (30, 30, 30)
            )
            text_rect: pygame.Rect = text_surf.get_rect(
                center=(mid_x, mid_y)
            )
            surface.blit(text_surf, text_rect)

    def draw_drones(self, surface: pygame.Surface) -> None:
        self.drones_sprites.draw(surface)

    def calculate_xy_coordinates(self) -> tuple[dict[int, int],
                                                dict[int, int]]:
        dict_y: dict[int, int] = {}
        dict_x: dict[int, int] = {}

        dict_x[self.map_data.glb_start.id] = self.map_data.glb_start.x
        dict_y[self.map_data.glb_start.id] = self.map_data.glb_start.y

        dict_x[self.map_data.glb_end.id] = self.map_data.glb_end.x
        dict_y[self.map_data.glb_end.id] = self.map_data.glb_end.y

        hub: 'Hub'  # from structure.py
        for hub in self.map_data.glb_hub:
            dict_x[hub.id] = hub.x
            dict_y[hub.id] = hub.y

        return dict_x, dict_y
