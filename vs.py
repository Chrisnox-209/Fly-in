import pygame
import sys
from parser import ParseMaps
import warnings
from collections import Counter
warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API"
)


class VisualNode(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, color: str,
                 dict_x: dict, dict_y: dict) -> None:
        super().__init__()
        self.dict_x = dict_x
        self.dict_y = dict_y



        if len(dict_x) <= 10:
            radius = 120
        else:
            radius = 50
        #2 à 10 120px

        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    @staticmethod  
    def calcul_coef(dict_x, dict_y):
        compte_y: Counter = Counter(dict_y.values())
        compte_x: Counter = Counter(dict_x.values())         
        
        y_keys = list(compte_y.keys())
        y_values = list(compte_y.values())
        
        if y_values[0] < 8 and y_keys[0] == 0:
            return 200
        return 1


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
             
        


        print(self.dict_x)
        bigx = max(self.dict_x.values())
        smallx = min(self.dict_x.values())
        bigy = max(self.dict_y.values())
        smally = min(self.dict_y.values())

        gird_x = abs(bigx - smallx) + 1
        gird_y = abs(bigy - smally) + 1

        # nb_hub = len(self.dict_x)
        # print(nb_hub)
        # print(f"{gird_x} - {gird_y}")

        posx = 2832 / gird_x
        posy = 1504 / gird_y

        # ### START HUB
        x_start = self.map_data.glb_start.x
        y_start = self.map_data.glb_start.y
        
        colonne = x_start - smallx
        pos_startx = (colonne * posx) + (posx / 2)

        
        
        line = y_start - smally
        pos_starty = (line * posy) + (posy / 2)

        
        hub_start = VisualNode(pos_startx, pos_starty, self.map_data.glb_start.color, self.dict_x, self.dict_y)
        self.all_sprites.add(hub_start)
            
        # start_x = abs(self.map_data.glb_startx - 
        # posx
        # posy
        # smallx
        # smally
        # hub_start = VisualNode(x, y, self.map_data.glb_start.color, self.dict_x, self.dict_y)
        # self.all_sprites.add(hub_start)

        # ### END HUB

        
        # ### OTHER HUB

            
            
            # hub = VisualNode(x, y, hub.color, self.dict_x, self.dict_y)
            # self.all_sprites.add(hub)

            
            
        #     hub_ = VisualNode(x, y, hub.color)

        # all_sprites.add(hub)
        # node_test = VisualNode(150, 650, "blue")
        # self.all_sprites.add(node_test)


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
        

    def run(self):
        running = True
        while running:
            # self.screen.blit(self.background, (0, 0))
            self.screen.fill("black") # Fond noir provisoire
            
            # --- 1. DESSINER LES CONNEXIONS ---
            # Tu devras boucler sur tes connexions et utiliser pygame.draw.line()
            
            # --- 2. DESSINER LES HUBS ---
            # On dessine les sprites par-dessus les lignes
            self.all_sprites.draw(self.screen)
            
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    # Étape 1 : Parser ton fichier
    ma_carte = ParseMaps.parse("03_basic_capacity.txt")


    # Étape 2 : Passer les données au Renderer
    graph: GraphRenderer = GraphRenderer(ma_carte)


    # Pour tester en attendant d'avoir tes données :
    # graph = GraphRenderer(map_data=None) 
    graph.run()