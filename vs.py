import pygame

pygame.init()

screen = pygame.display.set_mode((2048, 1252))
icon = pygame.image.load("assets/icon.png").convert_alpha()
pygame.display.set_icon(icon)

pygame.display.set_caption("Fly_In")
backgound = pygame.image.load('assets/sky.jpg')

running = True
while running:
    screen.blit(backgound, (0, 0))
    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
