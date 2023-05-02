import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join
from pygame.sprite import Sprite

'''
Initialize pygame and set the display name
'''
pygame.init()

pygame.display.set_caption("Dilly - Dally")


'''
Define the default width, height, frames per second, 
player velocity, and program window.
'''
WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VELOCITY = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))


def flip_sprite_image(sprites):
    'Flip sprites on their x-axis.'
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def load_sprite_sheets(dir1, dir2, width, height, direction= False):
    '''
    Load, split, and flip sprite sheets. Remove .png from the end
    of the file for easier access.
    '''
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip_sprite_image(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites

def get_block(size):
    '''
    Select preferred terrain block to use as the floor, 
    obstacles, etc...
    '''
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(0, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class Player(pygame.sprite.Sprite):
    '''
    Using the sprite class in pygame will allow easier handling of
    pixel-perfect collision using built in methods. Set class variables
    for default color, default gravity, character selection, and the default
    animation delay (the time between sprite changes).
    '''
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "NinjaFrog", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        '''
        Initialize the player class. Define default variables regarding x and y
        axis velocity, pixel mask, and player direction facing. Create animation, 
        fall, and jump counters to facilitate player abilities in later functions.
        '''
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_velocity = 0
        self.y_velocity = 0
        self.mask = None
        self.direction = "right"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0

    def jump(self):
        '''
        Allows player to jump by subtracting gravity from the
        y velocity.
        '''
        self.y_velocity = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0
            
    
    def move(self, dx, dy): #Takes in a displacement in the x or y direction and adds to current position
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True
        self.hit_count = 0

    def move_left(self, velocity):
        self.x_velocity = -velocity
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, velocity):
        self.x_velocity = velocity
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_velocity += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_velocity, self.y_velocity)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_velocity = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_velocity *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        if self.y_velocity < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_velocity > self.GRAVITY * 2:
            sprite_sheet = "fall"   
        elif self.x_velocity != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft= (self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)


    def draw(self, window, offset_x):
        window.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name= None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft= (self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

def get_background(name): #Loops through a tile to create a matrix of tiles to create a background
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height, = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = [i * width, j * height]
            tiles.append(pos)

    return tiles, image

def draw(window, background, bg_image, player, objects, offset_x): #Draws all components used within main()
    for tile in background:
        window.blit(bg_image, tuple(tile))

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    pygame.display.update()

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)
    
    return collided_objects

def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break
    
    player.move(-dx, 0)
    player.update()
    return collided_object

def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_velocity = 0
    collide_left = collide(player, objects, -PLAYER_VELOCITY * 2)
    collide_right = collide(player, objects, PLAYER_VELOCITY * 2)

    if keys[pygame.K_a] and not collide_left:
        player.move_left(PLAYER_VELOCITY)
    if keys[pygame.K_d] and not collide_right:
        player.move_right(PLAYER_VELOCITY)
    
    vertical_collide = handle_vertical_collision(player, objects, player.y_velocity)
    to_check = [collide_left, collide_right, *vertical_collide]
    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()

def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Purple.png")

    block_size = 96

    player = Player(100, 100, 50, 50)
    fire1 = Fire(200, HEIGHT - block_size - 64, 16, 32)
    fire1.on()
    fire2 = Fire(300, HEIGHT - block_size - 64, 16, 32)
    fire2.on()
    fire3 = Fire(400, HEIGHT - block_size - 64, 16, 32)
    fire3.on()
    fire4 = Fire(500, HEIGHT - block_size - 64, 16, 32)
    fire4.on()
    fire5 = Fire(1300, HEIGHT - block_size - 64, 16, 32)
    fire5.on()
    fire6 = Fire(1400, HEIGHT - block_size - 64, 16, 32)
    fire6.on()
    fire7 = Fire(1500, HEIGHT - block_size - 64, 16, 32)
    fire7.on()
    fire8 = Fire(1600, HEIGHT - block_size - 64, 16, 32)
    fire8.on()
    fire9 = Fire(1700, HEIGHT - block_size - 64, 16, 32)
    fire9.on()
    fire10 = Fire(1800, HEIGHT - block_size - 64, 16, 32)
    fire10.on()
    fire11 = Fire(1900, HEIGHT - block_size - 64, 16, 32)
    fire11.on()
    
    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(-WIDTH // block_size, WIDTH * 10 // block_size)]
    objects = [*floor, Block(0, HEIGHT - block_size * 2, block_size),
               Block(block_size * 2, HEIGHT - block_size * 4, block_size), 
               Block(block_size * 3, HEIGHT - block_size * 4, block_size),
               Block(block_size * 4, HEIGHT - block_size * 6, block_size),
               Block(block_size * 5, HEIGHT - block_size * 6, block_size),
               Block(block_size * 6, HEIGHT - block_size * 5, block_size),
               Block(block_size * 7, HEIGHT - block_size * 4, block_size),
               Block(block_size * 8, HEIGHT - block_size * 3, block_size),
               Block(block_size * 9, HEIGHT - block_size * 3, block_size),
               Block(block_size * 11, HEIGHT - block_size * 4, block_size), 
               Block(block_size * 12, HEIGHT - block_size * 4, block_size),
               Block(block_size * 15, HEIGHT - block_size * 6, block_size),
               Block(block_size * 16, HEIGHT - block_size * 6, block_size),
               Block(block_size * 18, HEIGHT - block_size * 5, block_size),
               Block(block_size * 19, HEIGHT - block_size * 4, block_size),
               Block(block_size * 20, HEIGHT - block_size * 3, block_size),
               Block(block_size * 22, HEIGHT - block_size * 2, block_size),
               fire1, fire2, fire3, fire4, fire5, fire6, fire7, fire8, fire9,
               fire10, fire11]
    
    offset_x = 0
    scroll_area_width = 200

    run = True #Start of game run loop
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                 player.jump()  

        player.loop(FPS)
        fire1.loop()
        fire2.loop()
        fire3.loop()
        fire4.loop()
        fire5.loop()
        fire6.loop()
        fire7.loop()
        fire8.loop()
        fire9.loop()
        fire10.loop()
        fire11.loop()
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width and player.x_velocity > 0) or (
            player.rect.left - offset_x <= scroll_area_width) and player.x_velocity <0):
            offset_x += player.x_velocity

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)