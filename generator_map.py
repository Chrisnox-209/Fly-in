import pygame
import sys
import math
from parser import ParseMaps
import warnings
from collections import Counter
warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API"
)


class VisualNode(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, color: str,
                 dict_x: dict, dict_y: dict, base_radius, capacity_drones: int) -> None:
        super().__init__()
        self.dict_x = dict_x
        self.dict_y = dict_y

        # 1. On calcule le pourcentage d'agrandissement
        percentage = 50 + (capacity_drones - 1) * 5.5

        # 2. On calcule le rayon théorique (qui peut exploser avec 36 drones)
        theoretical_radius = math.ceil((base_radius * 0.8) * percentage / 100)

        # 3. LA PROTECTION : On garde le plus petit entre le théorique et le maximum autorisé
        # (On autorise un maximum de 90% du base_radius pour que les cercles ne se touchent jamais)
        maximum_allowed_radius = math.ceil(base_radius * 0.9)
        radius = min(theoretical_radius, maximum_allowed_radius)

        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


class GraphRenderer:
    def __init__(self, map_data) -> None:

        self.screen: pygame.Surface = pygame.display.set_mode((2832, 1504))

        icon = pygame.image.load("assets/icon.png").convert_alpha()
        pygame.display.set_icon(icon)

        pygame.display.set_caption("Fly_In")
        # self.background = pygame.image.load('assets/sky.jpg')

        self.all_sprites = pygame.sprite.Group()
        self.map_data = map_data
        self.dict_x, self.dict_y = self.calcul_nb_xy()
        pygame.init()


        bigx = max(self.dict_x.values())
        smallx = min(self.dict_x.values())
        bigy = max(self.dict_y.values())
        smally = min(self.dict_y.values())

        gird_x = abs(bigx - smallx) + 1
        gird_y = abs(bigy - smally) + 1

        posx = 2832 / gird_x
        posy = 1504 / gird_y

        pos_min = min(posx, posy)
        base_radius = pos_min / 2

        # ### START HUB
        x_start = self.map_data.glb_start.x
        y_start = self.map_data.glb_start.y

        colonne = x_start - smallx
        pos_startx = (colonne * posx) + (posx / 2)

        line = bigy - y_start
        pos_starty = (line * posy) + (posy / 2)

        hub_start = VisualNode(pos_startx, pos_starty, self.map_data.glb_start.color, self.dict_x, self.dict_y, base_radius, self.map_data.glb_start.max_drones)
        self.all_sprites.add(hub_start)

        # ### END HUB
        x_end = self.map_data.glb_end.x
        y_end = self.map_data.glb_end.y

        colonne = x_end - smallx
        pos_endx = (colonne * posx) + (posx / 2)

        line = bigy - y_end
        pos_endy = (line * posy) + (posy / 2)

        hub_end = VisualNode(pos_endx, pos_endy, self.map_data.glb_end.color, self.dict_x, self.dict_y, base_radius, self.map_data.glb_end.max_drones)
        self.all_sprites.add(hub_end)

        # ### OTHER HUB

        for hub in self.map_data.glb_hub:
            colonne = hub.x - smallx
            pos_hubx = (colonne * posx) + (posx / 2)

            line = bigy - hub.y
            pos_huby = (line * posy) + (posy / 2)

            hub = VisualNode(pos_hubx, pos_huby, hub.color, self.dict_x, self.dict_y, base_radius, hub.max_drones)
            self.all_sprites.add(hub)


    def calcul_nb_xy(self) -> tuple[dict, dict]:
        dict_y: dict = {}
        dict_x: dict = {}

        dict_x[self.map_data.glb_start.id] = self.map_data.glb_start.x
        dict_y[self.map_data.glb_start.id] = self.map_data.glb_start.y

        dict_x[self.map_data.glb_end.id] = self.map_data.glb_end.x
        dict_y[self.map_data.glb_end.id] = self.map_data.glb_end.y

        for hub in self.map_data.glb_hub:
            dict_x[hub.id] = hub.x
            dict_y[hub.id] = hub.y
        return dict_x, dict_y
