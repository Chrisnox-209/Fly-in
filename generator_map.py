import math
import random
import warnings
from enum import Enum
from typing import Any, cast

import pygame
from pygame.font import Font
from pygame.sprite import Group

warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API"
)


class HubColor(Enum):
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
            teinte: int = (pygame.time.get_ticks() // 10) % 360
            couleur: pygame.Color = pygame.Color(0)
            couleur.hsva = (teinte, 100, 100, 100)
            return couleur
        return cast(tuple[int, int, int], self.value)


class VisualNode(pygame.sprite.Sprite):
    def __init__(
        self,
        x: int,
        y: int,
        name: str,
        color: pygame.Surface | pygame.Color | tuple[int, int, int],
        dict_x: dict[str, int],
        dict_y: dict[str, int],
        base_radius: float,
        capacity_drones: int,
        zone_type: str = "normal"
    ) -> None:
        super().__init__()
        self.dict_x: dict[str, int] = dict_x
        self.dict_y: dict[str, int] = dict_y
        self.name: str = name
        self.zone_type: str = zone_type

        percentage: float = 60 + (capacity_drones - 1) * 5.5
        theoretical_radius: int = math.ceil(
            (base_radius * 0.8) * percentage / 100
        )
        maximum_allowed_radius: int = math.ceil(base_radius * 0.9)

        self.radius: int = min(theoretical_radius, maximum_allowed_radius)
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
        texte_capacite: str = str(capacity_drones)
        text_surface: pygame.Surface = font.render(
            texte_capacite, True, (45, 45, 45)
        )
        text_rect: pygame.Rect = text_surface.get_rect(
            center=(self.radius, self.radius)
        )
        self.image.blit(text_surface, text_rect)
        self.draw_zone_badge(self.radius)

        self.rect: pygame.Rect = self.image.get_rect()
        self.rect.center = (x, y)

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
    def __init__(
        self,
        x: float,
        y: float,
        dict_x: dict[str, int],
        dict_y: dict[str, int],
        radius: int,
        flight_plan: list[str],
        info_hub: dict[str, tuple[int, int]],
        step: int = 0
    ) -> None:
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
        self.dict_x: dict[str, int] = dict_x
        self.dict_y: dict[str, int] = dict_y
        self.flight_plan: list[str] = flight_plan
        self.step: int = step
        self.info_hub: dict[str, tuple[int, int]] = info_hub

        self.frames_per_turn: int = 30
        self.current_frame: int = 0
        self.radius: int = radius

        my_drone_paths: list[str] = random.choice(drone_images)
        self.sprites: list[pygame.Surface] = []

        width: int = self.radius
        height: float = self.radius / 1.21

        path: str
        for path in my_drone_paths:
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

    def drone_angle(self, target_x: float, target_y: float) -> None:
        dx: float = target_x - self.x
        dy: float = target_y - self.y
        if dx == 0.0 and dy == 0.0:
            return

        calculate_angle: float = math.degrees(math.atan2(-dy, dx))
        offset: float = -90.0
        self.angle = calculate_angle + offset

    def update(self) -> None:
        if self.step >= len(self.flight_plan):
            self.propellers = 0.0
            return

        hub_actuel: str = self.flight_plan[self.step]
        prochain_hub: str

        if self.step + 1 < len(self.flight_plan):
            prochain_hub = self.flight_plan[self.step + 1]
        else:
            prochain_hub = hub_actuel

        start_x: int
        start_y: int
        target_x: int
        target_y: int
        start_x, start_y = self.info_hub[hub_actuel]
        target_x, target_y = self.info_hub[prochain_hub]

        if hub_actuel != prochain_hub:
            self.drone_angle(float(target_x), float(target_y))

        progression: float = self.current_frame / self.frames_per_turn

        if hub_actuel == prochain_hub:
            self.x = float(start_x)
            self.y = float(start_y)
            self.propellers = 0.6
        else:
            self.x = start_x + (target_x - start_x) * progression
            self.y = start_y + (target_y - start_y) * progression
            self.propellers = 2.0

        self.current_frame += 1

        if self.current_frame >= self.frames_per_turn:
            self.current_frame = 0
            self.step += 1

        self.current_sprite += self.propellers
        if int(self.current_sprite) >= len(self.sprites):
            self.current_sprite = 0.0

        original_image: pygame.Surface = self.sprites[int(self.current_sprite)]
        self.image = pygame.transform.rotate(original_image, self.angle)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))


class Buttom_Gm:
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        color_btn: tuple[int, int, int]
    ) -> None:
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.text: str = text
        self.color_btn: tuple[int, int, int] = color_btn
        self.font: Font = pygame.font.SysFont("arial", 24, bold=True)

    def draw(self, screen: pygame.Surface) -> None:
        draw_rect: pygame.Rect = self.rect.copy()
        pygame.draw.rect(
            screen,
            self.color_btn,
            draw_rect,
            border_radius=12,
        )

        text_btn: pygame.Surface = self.font.render(
            self.text, True, (255, 255, 255)
        )
        text_rect: pygame.Rect = text_btn.get_rect()
        text_rect.center = self.rect.center
        screen.blit(text_btn, text_rect)


class GraphRenderer:
    def __init__(self, map_data: Any) -> None:
        pygame.init()
        self.world_surface: pygame.Surface = pygame.display.set_mode(
            (2832, 1504)
        )
        self.rainbow_texture: pygame.Surface = pygame.image.load(
            "assets/rainbow.jpg"
        ).convert_alpha()

        icon: pygame.Surface = pygame.image.load(
            "assets/icon.png"
        ).convert_alpha()
        pygame.display.set_icon(icon)
        pygame.display.set_caption("Fly_In")

        self.map_data: Any = map_data
        self.all_sprites: Group[VisualNode] = pygame.sprite.Group()
        self.drones_sprites: Group[VisualDrone] = pygame.sprite.Group()

        self.dict_x: dict[str, int]
        self.dict_y: dict[str, int]
        self.dict_x, self.dict_y = self.calcul_nb_xy()

        self.infos_hub: dict[str, tuple[int, int]] = {}
        self.nodes: dict[str, VisualNode] = {}

        bigx: int = max(self.dict_x.values())
        smallx: int = min(self.dict_x.values())
        bigy: int = max(self.dict_y.values())
        smally: int = min(self.dict_y.values())

        gird_x: int = abs(bigx - smallx) + 1
        gird_y: int = abs(bigy - smally) + 1

        posx: float = 2832 / gird_x
        posy: float = 1504 / gird_y

        pos_min: float = min(posx, posy)
        base_radius: float = pos_min / 2

        x_start: int = self.map_data.glb_start.x
        y_start: int = self.map_data.glb_start.y
        colonne: int = x_start - smallx
        pos_startx: float = (colonne * posx) + (posx / 2)
        line: int = bigy - y_start
        pos_starty: float = (line * posy) + (posy / 2)

        percentage: float = (
            50 + (self.map_data.glb_start.max_drones - 1) * 5.5
        )
        theoretical_radius: int = math.ceil(
            (base_radius * 0.8) * percentage / 100
        )
        maximum_allowed_radius: int = math.ceil(base_radius * 0.9)
        radius_start: int = min(theoretical_radius, maximum_allowed_radius)
        diameter_start: int = radius_start * 2

        color_start: str | None = self.map_data.glb_start.color
        rgb_start: pygame.Surface | pygame.Color | tuple[int, int, int]

        if color_start == "rainbow":
            rgb_start = pygame.transform.smoothscale(
                self.rainbow_texture, (diameter_start, diameter_start)
            )
        else:
            try:
                if color_start is None:
                    color_enum_start: HubColor = HubColor.GREY
                else:
                    color_enum_start = HubColor[color_start.upper()]
                rgb_start = color_enum_start.rgb
            except KeyError:
                rgb_start = (255, 255, 255)

        self.infos_hub[self.map_data.glb_start.name] = (
            int(pos_startx), int(pos_starty)
        )
        current_zone: str = getattr(
            self.map_data.glb_start, 'zone', 'normal'
        )

        hub_start: VisualNode = VisualNode(
            int(pos_startx), int(pos_starty),
            self.map_data.glb_start.name,
            rgb_start,
            self.dict_x, self.dict_y,
            base_radius,
            self.map_data.glb_start.max_drones,
            zone_type=current_zone
        )
        self.all_sprites.add(hub_start)
        self.nodes[self.map_data.glb_start.name] = hub_start

        x_end: int = self.map_data.glb_end.x
        y_end: int = self.map_data.glb_end.y
        colonne_end: int = x_end - smallx
        pos_endx: float = (colonne_end * posx) + (posx / 2)
        line_end: int = bigy - y_end
        pos_endy: float = (line_end * posy) + (posy / 2)

        radius_end: int = min(theoretical_radius, maximum_allowed_radius)
        diameter_end: int = radius_end * 2

        color_end: str | None = self.map_data.glb_end.color
        rgb_end: pygame.Surface | pygame.Color | tuple[int, int, int]

        if color_end == "rainbow":
            rgb_end = pygame.transform.smoothscale(
                self.rainbow_texture, (diameter_end, diameter_end)
            )
        else:
            try:
                if color_end is None:
                    color_enum_end: HubColor = HubColor.GREY
                else:
                    color_enum_end = HubColor[color_end.upper()]
                rgb_end = color_enum_end.rgb
            except KeyError:
                rgb_end = (255, 255, 255)

        self.infos_hub[self.map_data.glb_end.name] = (
            int(pos_endx), int(pos_endy)
        )

        end_zone: str = getattr(self.map_data.glb_end, 'zone', 'normal')
        hub_end: VisualNode = VisualNode(
            int(pos_endx), int(pos_endy),
            self.map_data.glb_end.name,
            rgb_end,
            self.dict_x, self.dict_y,
            base_radius,
            self.map_data.glb_end.max_drones,
            zone_type=end_zone
        )
        self.all_sprites.add(hub_end)
        self.nodes[self.map_data.glb_end.name] = hub_end

        hub: Any
        for hub in self.map_data.glb_hub:
            colonne_hub: int = hub.x - smallx
            pos_hubx: float = (colonne_hub * posx) + (posx / 2)
            line_hub: int = bigy - hub.y
            pos_huby: float = (line_hub * posy) + (posy / 2)
            self.infos_hub[hub.name] = (int(pos_hubx), int(pos_huby))

            radius_hub: int = min(theoretical_radius, maximum_allowed_radius)
            diameter_hub: int = radius_hub * 2

            color_hub: str | None = hub.color
            rgb_hub: pygame.Surface | pygame.Color | tuple[int, int, int]

            if color_hub == "rainbow":
                rgb_hub = pygame.transform.smoothscale(
                    self.rainbow_texture, (diameter_hub, diameter_hub)
                )
            else:
                try:
                    if color_hub is None:
                        color_enum_hub: HubColor = HubColor.GREY
                    else:
                        color_enum_hub = HubColor[color_hub.upper()]
                    rgb_hub = color_enum_hub.rgb
                except KeyError:
                    rgb_hub = (255, 255, 255)

            hub_zone: str = getattr(hub, 'zone', 'normal')
            visual_hub: VisualNode = VisualNode(
                int(pos_hubx), int(pos_huby),
                hub.name,
                rgb_hub,
                self.dict_x, self.dict_y,
                base_radius,
                hub.max_drones,
                zone_type=hub_zone
            )
            self.all_sprites.add(visual_hub)
            self.nodes[hub.name] = visual_hub

    def draw_connections(self, surface: pygame.Surface) -> None:
        c: Any
        for c in self.map_data.glb_connection:
            startx: int = self.infos_hub[c.connection_a][0]
            starty: int = self.infos_hub[c.connection_a][1]
            endx: int = self.infos_hub[c.connection_b][0]
            endy: int = self.infos_hub[c.connection_b][1]
            pygame.draw.line(
                surface,
                (200, 200, 200),
                (startx, starty),
                (endx, endy),
                5
            )

    def draw_drones(self, surface: pygame.Surface) -> None:
        self.drones_sprites.draw(surface)

    def calcul_nb_xy(self) -> tuple[dict[str, int], dict[str, int]]:
        dict_y: dict[str, int] = {}
        dict_x: dict[str, int] = {}

        dict_x[self.map_data.glb_start.id] = self.map_data.glb_start.x
        dict_y[self.map_data.glb_start.id] = self.map_data.glb_start.y

        dict_x[self.map_data.glb_end.id] = self.map_data.glb_end.x
        dict_y[self.map_data.glb_end.id] = self.map_data.glb_end.y

        hub: Any
        for hub in self.map_data.glb_hub:
            dict_x[hub.id] = hub.x
            dict_y[hub.id] = hub.y

        return dict_x, dict_y
