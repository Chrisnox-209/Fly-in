import pygame
import math
from pygame.sprite import Group
from typing import Any, cast
import warnings
import random
from enum import Enum


from pygame.font import Font
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
            couleur = pygame.Color(0)
            couleur.hsva = (teinte, 100, 100, 100)
            return couleur
        return cast(tuple[int, int, int], self.value)


class VisualNode(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, name: str, color: Any,
                 dict_x: dict[str, int], dict_y: dict[str, int],
                 base_radius: float, capacity_drones: int) -> None:
        super().__init__()
        self.dict_x: dict[str, int] = dict_x
        self.dict_y: dict[str, int] = dict_y
        self.name: str = name

        # 1. On calcule le pourcentage d'agrandissement
        percentage: float = 60 + (capacity_drones - 1) * 5.5

        # 2. On calcule le rayon théorique (qui peut exploser avec 36 drones)
        theoretical_radius: Any = math.ceil(
            (base_radius * 0.8) * percentage / 100)

        # 3. LA PROTECTION : On garde le plus petit entre le
        # théorique et le maximum autorisé
        # (On autorise un maximum de 90% du base_radius
        # pour que les cercles ne se touchent jamais)
        maximum_allowed_radius: Any = math.ceil(base_radius * 0.9)
        radius: Any | Any = min(theoretical_radius, maximum_allowed_radius)
        self.radius: Any = radius

        if isinstance(color, pygame.Surface):
            self.image = pygame.Surface((
                radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (
                255, 255, 255, 255), (radius, radius), radius)
            self.image.blit(color, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        else:
            self.image = pygame.Surface(
                (radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(self.image, color, (radius, radius), radius)

        self.rect: pygame.Rect = self.image.get_rect()
        self.rect.center = (x, y)


class VisualDrone(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int,
                 dict_x: dict[str, int],
                 dict_y: dict[str, int],
                 radius: int,
                 flight_plan: list,
                 info_hub: dict,
                 step: int = 0,) -> None:
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
        self.flight_plan: list = flight_plan
        self.step: int = step
        self.info_hub: dict = info_hub
        self.speed = 20

        self.radius: int = radius
        my_drone_paths: list[str] = random.choice(drone_images)
        self.sprites: list[pygame.Surface] = []

        width: int = self.radius
        height: float = self.radius / 1.21
        for path in my_drone_paths:
            img: pygame.Surface = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (width, height))
            self.sprites.append(img)

        self.current_sprite: float = 0
        self.propellers: float = 0

        self.image: Any = self.sprites[self.current_sprite]
        self.rect: Any = self.image.get_rect()

        self.x = float(x)
        self.y = float(y)
        self.rect.center = (int(self.x), int(self.y))

        self.angle: float = 270
        original_image: pygame.Surface = self.sprites[int(self.current_sprite)]
        self.image = pygame.transform.rotate(original_image, self.angle)

    def drone_angle(self, target_x: float, target_y: float) -> None:
        dx: float = target_x - self.x
        dy: float = target_y - self.y
        if dx == 0 and dy == 0:
            return

        calculate_angle: float = math.degrees(math.atan2(-dy, dx))
        offset = -90
        self.angle = calculate_angle + offset

    def update(self) -> None:
        pos_x: int
        pos_y: int
        if self.step == 0:
            self.propellers = 0
        if self.step >= len(self.flight_plan):
            self.propellers = 0
        else:
            hub: str = self.flight_plan[self.step]
            pos_x, pos_y = self.info_hub[hub]
            self.drone_angle(pos_x, pos_y)
            dx: float = pos_x - self.x
            dy: float = pos_y - self.y
            distance: float = math.hypot(dx, dy)
            if distance <= self.speed:
                self.step += 1
                self.propellers = 0.6
            else:
                self.x += (dx / distance) * self.speed
                self.y += (dy / distance) * self.speed
                self.propellers = 2

        self.current_sprite += self.propellers
        if int(self.current_sprite) >= len(self.sprites):
            self.current_sprite = 0

        original_image: Any = self.sprites[int(self.current_sprite)]
        self.image = pygame.transform.rotate(original_image, self.angle)
        self.rect = self.image.get_rect(center=(self.x, self.y))


class Buttom_Gm:
    def __init__(self, x: int, y: int, width: int,
                 height: int, text: str, color_btn: Any) -> None:
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.text: str = text
        self.color_btn: Any = color_btn
        self.font: Font = pygame.font.SysFont("arial", 24, bold=True)

    def draw(self, screen: Any) -> None:
        draw_rect: pygame.Rect = self.rect.copy()
        pygame.draw.rect(
            screen,
            self.color_btn,
            draw_rect,
            border_radius=12,
        )

        text_btn: pygame.Surface = self.font.render(
            self.text, True, (255, 255, 255))
        text_rect: pygame.Rect = text_btn.get_rect()
        text_rect.center = self.rect.center
        screen.blit(text_btn, text_rect)


class GraphRenderer:
    def __init__(self, map_data: Any) -> None:
        pygame.init()
        self.screen: pygame.Surface = pygame.display.set_mode((2832, 1504))
        self.rainbow_texture: pygame.Surface = pygame.image.load(
            "assets/rainbow.jpg").convert_alpha()
        icon: pygame.Surface = pygame.image.load(
            "assets/icon.png").convert_alpha()
        pygame.display.set_icon(icon)
        pygame.display.set_caption("Fly_In")

        self.dict_x: dict[str, int]
        self.dict_y: dict[str, int]
        self.all_sprites: Group[VisualNode] = pygame.sprite.Group()
        self.drones_sprites: Group[VisualDrone] = pygame.sprite.Group()
        self.map_data: Any = map_data
        self.dict_x, self.dict_y = self.calcul_nb_xy()
        self.infos_hub: dict[str, tuple[int, int]] = {}
        self.nodes: dict[str, VisualNode] = {}

        bigx: Any = max(self.dict_x.values())
        smallx: Any = min(self.dict_x.values())
        bigy: Any = max(self.dict_y.values())
        smally: Any = min(self.dict_y.values())

        gird_x: Any | Any = abs(bigx - smallx) + 1
        gird_y: Any | Any = abs(bigy - smally) + 1

        posx: float = 2832 / gird_x
        posy: float = 1504 / gird_y

        pos_min: Any | Any = min(posx, posy)
        base_radius: Any | Any = pos_min / 2

        # ### START HUB
        x_start: Any = self.map_data.glb_start.x
        y_start: Any = self.map_data.glb_start.y

        colonne: Any | Any = x_start - smallx
        pos_startx = (colonne * posx) + (posx // 2)

        line: Any | Any = bigy - y_start
        pos_starty = (line * posy) + (posy // 2)

        # calul taille hub pour rainbow
        percentage: Any = 50 + (self.map_data.glb_start.max_drones - 1) * 5.5
        theoretical_radius: Any = math.ceil(
            (base_radius * 0.8) * percentage / 100)
        maximum_allowed_radius: Any = math.ceil(base_radius * 0.9)
        radius_start: Any | Any = min(theoretical_radius,
                                      maximum_allowed_radius)
        diameter_start: Any | Any = radius_start * 2

        # ### Gestion des couleurs
        color_start: Any = self.map_data.glb_start.color
        rgb_start: pygame.Surface | pygame.Color | tuple[int, int, int]
        if color_start == "rainbow":
            rgb_start = pygame.transform.smoothscale(
                self.rainbow_texture, (diameter_start, diameter_start))
        else:
            try:
                if color_start is None:
                    color_enum: HubColor = HubColor.GREY
                else:
                    color_enum = HubColor[color_start.upper()]
                rgb_start = color_enum.rgb
            except KeyError:
                rgb_start = (255, 255, 255)

        self.infos_hub[self.map_data.glb_start.name] = (int(pos_startx),
                                                        int(pos_starty))
        hub_start = VisualNode(pos_startx, pos_starty,
                               self.map_data.glb_start.name,
                               rgb_start,
                               self.dict_x, self.dict_y,
                               base_radius,
                               self.map_data.glb_start.max_drones)
        self.all_sprites.add(hub_start)
        self.nodes[self.map_data.glb_start.name] = hub_start

        # ### END HUB
        x_end: Any = self.map_data.glb_end.x
        y_end: Any = self.map_data.glb_end.y

        colonne = x_end - smallx
        pos_endx = (colonne * posx) + (posx // 2)

        line = bigy - y_end
        pos_endy = (line * posy) + (posy // 2)

        # ### Gestion des couleurs
        radius_end: Any | Any = min(theoretical_radius, maximum_allowed_radius)
        diameter_end: Any | Any = radius_end * 2

        color_end: Any = self.map_data.glb_end.color
        rgb_end: pygame.Surface | pygame.Color | tuple[int, int, int]
        if color_end == "rainbow":
            rgb_end = pygame.transform.smoothscale(
                self.rainbow_texture, (diameter_end, diameter_end))
        else:
            try:
                if color_end is None:
                    color_enum = HubColor.GREY
                else:
                    color_enum = HubColor[color_end.upper()]
                rgb_end = color_enum.rgb
            except KeyError:
                rgb_end = (255, 255, 255)

        self.infos_hub[self.map_data.glb_end.name] = (int(pos_endx),
                                                      int(pos_endy))
        hub_end = VisualNode(pos_endx, pos_endy,
                             self.map_data.glb_end.name,
                             rgb_end,
                             self.dict_x, self.dict_y,
                             base_radius,
                             self.map_data.glb_end.max_drones)
        self.all_sprites.add(hub_end)
        self.nodes[self.map_data.glb_end.name] = hub_end

        # ### OTHER HUB

        for hub in self.map_data.glb_hub:
            colonne = hub.x - smallx
            pos_hubx = (colonne * posx) + (posx // 2)

            line = bigy - hub.y
            pos_huby = (line * posy) + (posy // 2)
            self.infos_hub[hub.name] = (int(pos_hubx), int(pos_huby))

            # ### Gestion des couleurs
            radius_hub: Any | Any = min(theoretical_radius,
                                        maximum_allowed_radius)
            diameter_hub: Any | Any = radius_hub * 2

            color_hub: Any = hub.color
            rgb_hub: pygame.Surface | pygame.Color | tuple[int, int, int]
            if color_hub == "rainbow":
                rgb_hub = pygame.transform.smoothscale(
                    self.rainbow_texture, (diameter_hub, diameter_hub))
            else:
                try:
                    if color_hub is None:
                        color_enum = HubColor.GREY
                    else:
                        color_enum = HubColor[color_hub.upper()]
                    rgb_hub = color_enum.rgb
                except KeyError:
                    rgb_hub = (255, 255, 255)

            visual_hub = VisualNode(pos_hubx, pos_huby, hub.name,
                                    rgb_hub,
                                    self.dict_x, self.dict_y,
                                    base_radius, hub.max_drones)
            self.all_sprites.add(visual_hub)
            self.nodes[hub.name] = visual_hub

    def draw_connections(self, surface: Any) -> None:
        for c in self.map_data.glb_connection:
            startx: Any = self.infos_hub[c.connection_a][0]
            starty: Any = self.infos_hub[c.connection_a][1]
            endx: Any = self.infos_hub[c.connection_b][0]
            endy: Any = self.infos_hub[c.connection_b][1]
            pygame.draw.line(surface,
                             (255, 255, 255),
                             (startx, starty),
                             (endx, endy), 5)

    def draw_drones(self, surface: pygame.Surface) -> None:
        self.drones_sprites.draw(surface)

    def calcul_nb_xy(self) -> tuple[dict[str, int], dict[str, int]]:
        dict_y: dict[str, int] = {}
        dict_x: dict[str, int] = {}

        dict_x[self.map_data.glb_start.id] = self.map_data.glb_start.x
        dict_y[self.map_data.glb_start.id] = self.map_data.glb_start.y

        dict_x[self.map_data.glb_end.id] = self.map_data.glb_end.x
        dict_y[self.map_data.glb_end.id] = self.map_data.glb_end.y

        for hub in self.map_data.glb_hub:
            dict_x[hub.id] = hub.x
            dict_y[hub.id] = hub.y
        return dict_x, dict_y
