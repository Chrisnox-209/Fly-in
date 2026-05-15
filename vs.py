import warnings
warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API"
)
import pygame



pygame.init()


class Hub(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.image = pygame.Surface((200, 200), pygame.SRCALPHA)
        pygame.draw.circle(self.image, "red", (100, 100), 100)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)



screen = pygame.display.set_mode((2048, 1300))
icon = pygame.image.load("assets/icon.png").convert_alpha()
pygame.display.set_icon(icon)

pygame.display.set_caption("Fly_In")
backgound = pygame.image.load('assets/sky.jpg')
hub = Hub(150, 650)
all_sprites = pygame.sprite.Group()
all_sprites.add(hub)

running = True
while running:
    screen.blit(backgound, (0, 0))
    all_sprites.draw(screen)
    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
