import pygame
import math
from pygame.sprite import Group
from typing import Any, cast
import warnings
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
            teinte = (pygame.time.get_ticks() // 10) % 360
            couleur = pygame.Color(0)
            couleur.hsva = (teinte, 100, 100, 100)
            return couleur
        return cast(tuple[int, int, int], self.value)


class VisualNode(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, color: Any,
                 dict_x: dict[str, int], dict_y: dict[str, int],
                 base_radius: float, capacity_drones: int) -> None:
        super().__init__()
        self.dict_x: dict[str, int] = dict_x
        self.dict_y: dict[str, int] = dict_y

        # 1. On calcule le pourcentage d'agrandissement
        percentage: float = 50 + (capacity_drones - 1) * 5.5

        # 2. On calcule le rayon théorique (qui peut exploser avec 36 drones)
        theoretical_radius: Any = math.ceil(
            (base_radius * 0.8) * percentage / 100)

        # 3. LA PROTECTION : On garde le plus petit entre le
        # théorique et le maximum autorisé
        # (On autorise un maximum de 90% du base_radius
        # pour que les cercles ne se touchent jamais)
        maximum_allowed_radius: Any = math.ceil(base_radius * 0.9)
        radius: Any | Any = min(theoretical_radius, maximum_allowed_radius)

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
    def __init__(self, x: int, y: int, img_drone: str,
                 dict_x: dict[str, int], dict_y: dict[str, int]):
        super().__init__()
        self.dict_x: dict[str, int] = dict_x
        self.dict_y: dict[str, int] = dict_y
        self.image: pygame.Surface = pygame.image.load(
            "assets/bird.gif").convert_alpha()
        self.image = pygame.transform.scale(self.image, (100, 100))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


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

        pygame.init()

        bigx: Any = max(self.dict_x.values())
        smallx: Any = min(self.dict_x.values())
        bigy: Any = max(self.dict_y.values())
        smally: Any = min(self.dict_y.values())

        gird_x: Any | Any = abs(bigx - smallx) + 1
        gird_y: Any | Any = abs(bigy - smally) + 1

        posx: Any | Any = 2832 / gird_x
        posy: Any | Any = 1504 / gird_y

        pos_min: Any | Any = min(posx, posy)
        base_radius: Any | Any = pos_min / 2

        # ### START HUB
        x_start: Any = self.map_data.glb_start.x
        y_start: Any = self.map_data.glb_start.y

        colonne: Any | Any = x_start - smallx
        pos_startx: Any | Any = (colonne * posx) + (posx / 2)

        line: Any | Any = bigy - y_start
        pos_starty: Any | Any = (line * posy) + (posy / 2)

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
                color_enum: HubColor = HubColor[color_start.upper()]
                rgb_start = color_enum.rgb
            except KeyError:
                rgb_start = (255, 255, 255)

        self.infos_hub[self.map_data.glb_start.name] = (pos_startx, pos_starty)
        hub_start = VisualNode(pos_startx, pos_starty,
                               rgb_start,
                               self.dict_x, self.dict_y,
                               base_radius,
                               self.map_data.glb_start.max_drones)
        self.all_sprites.add(hub_start)

        # ### END HUB
        x_end: Any = self.map_data.glb_end.x
        y_end: Any = self.map_data.glb_end.y

        colonne = x_end - smallx
        pos_endx: Any | Any = (colonne * posx) + (posx / 2)

        line = bigy - y_end
        pos_endy: Any | Any = (line * posy) + (posy / 2)

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
                color_enum = HubColor[color_end.upper()]
                rgb_end = color_enum.rgb
            except KeyError:
                rgb_end = (255, 255, 255)

        self.infos_hub[self.map_data.glb_end.name] = (pos_endx, pos_endy)
        hub_end = VisualNode(pos_endx, pos_endy,
                             rgb_end,
                             self.dict_x, self.dict_y,
                             base_radius,
                             self.map_data.glb_end.max_drones)
        self.all_sprites.add(hub_end)

        # ### OTHER HUB

        for hub in self.map_data.glb_hub:
            colonne = hub.x - smallx
            pos_hubx: Any | Any = (colonne * posx) + (posx / 2)

            line = bigy - hub.y
            pos_huby: Any | Any = (line * posy) + (posy / 2)
            self.infos_hub[hub.name] = (pos_hubx, pos_huby)

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
                    color_enum = HubColor[color_hub.upper()]
                    rgb_hub = color_enum.rgb
                except KeyError:
                    rgb_hub = (255, 255, 255)

            hub = VisualNode(pos_hubx, pos_huby, rgb_hub,
                             self.dict_x, self.dict_y,
                             base_radius, hub.max_drones)
            self.all_sprites.add(hub)

    def draw_connections(self, surface: Any) -> None:
        for c in self.map_data.glb_connection:
            startx: Any = self.infos_hub[c.connection_a][0]
            starty: Any = self.infos_hub[c.connection_a][1]
            endx: Any = self.infos_hub[c.connection_b][0]
            endy: Any = self.infos_hub[c.connection_b][1]
            pygame.draw.line(self.screen, (255, 255, 255),
                             (startx, starty), (endx, endy), 5)

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
