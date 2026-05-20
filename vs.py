import pygame
import sys
from parser import ParseMaps
import warnings
warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API"
)


class VisualNode(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, color: str = "red") -> None:
        super().__init__()

        radius = 50
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


class GraphRenderer:
    def __init__(self, map_data) -> None:
        pygame.init()
        self.screen: pygame.Surface = pygame.display.set_mode((2048, 1300))
        
        icon = pygame.image.load("assets/icon.png").convert_alpha()
        pygame.display.set_icon(icon)

        pygame.display.set_caption("Fly_In")
        # self.background = pygame.image.load('assets/sky.jpg')
        
        self.all_sprites = pygame.sprite.Group()
        self.map_data = map_data
        
        # --- C'EST ICI QUE LA MAGIE DEVRA OPÉRER ---
        # Tu vas devoir créer tes VisualNodes dynamiquement.
        # Pour tester que la fenêtre marche, on en met un en dur :
        node_test = VisualNode(150, 650, "blue")
        self.all_sprites.add(node_test)

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
    ma_carte = ParseMaps.parse("maps/easy/01_linear_path.txt")
    
    

    for hub in ma_carte.glb_hub:
        print(hub.color)

    # Étape 2 : Passer les données au Renderer
    graph = GraphRenderer(ma_carte)
    
    # Pour tester en attendant d'avoir tes données :
    # graph = GraphRenderer(map_data=None) 
    graph.run()