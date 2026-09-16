"""
Cloud Runner - an original 2D platformer game.
Built with Pygame, structured to be compiled to WebAssembly using pygbag
so it can run in a browser (and be hosted on AWS S3 / EC2 + Nginx).

Controls:
  Arrow keys / A,D  -> move left/right
  Space / W / Up    -> jump
  R                 -> restart after game over / win
"""

import asyncio
import random
import pygame

pygame.init()

# ---------- Config ----------
WIDTH, HEIGHT = 800, 450
FPS = 60
GRAVITY = 0.8
JUMP_STRENGTH = -15
MOVE_SPEED = 5

SKY = (107, 195, 255)
GROUND_COLOR = (94, 60, 40)
GROUND_TOP = (60, 168, 78)
PLAYER_COLOR = (230, 76, 60)
PLAYER_ACCENT = (255, 214, 92)
ENEMY_COLOR = (120, 80, 160)
COIN_COLOR = (255, 205, 60)
FLAG_POLE = (200, 200, 200)
FLAG_CLOTH = (60, 200, 120)
TEXT_COLOR = (20, 20, 30)
WHITE = (255, 255, 255)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cloud Runner")
clock = pygame.time.Clock()
font_big = pygame.font.SysFont("arial", 42, bold=True)
font_med = pygame.font.SysFont("arial", 24, bold=True)
font_small = pygame.font.SysFont("arial", 18)


class Platform:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface, camera_x):
        r = self.rect.move(-camera_x, 0)
        pygame.draw.rect(surface, GROUND_COLOR, r)
        pygame.draw.rect(surface, GROUND_TOP, (r.x, r.y, r.width, 8))


class Coin:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.collected = False
        self.bob = random.uniform(0, 6.28)

    def draw(self, surface, camera_x, t):
        if self.collected:
            return
        offset = int(3 * pygame.math.Vector2(0, 1).rotate(0).y)
        y = self.rect.y + int(3 * pygame_sin(t + self.bob))
        pygame.draw.circle(
            surface, COIN_COLOR,
            (self.rect.centerx - camera_x, y + self.rect.height // 2),
            10
        )
        pygame.draw.circle(
            surface, (200, 150, 20),
            (self.rect.centerx - camera_x, y + self.rect.height // 2),
            10, 2
        )


def pygame_sin(t):
    import math
    return math.sin(t)


class Enemy:
    def __init__(self, x, y, left_bound, right_bound):
        self.rect = pygame.Rect(x, y, 30, 30)
        self.left_bound = left_bound
        self.right_bound = right_bound
        self.speed = 2
        self.alive = True

    def update(self):
        if not self.alive:
            return
        self.rect.x += self.speed
        if self.rect.right > self.right_bound or self.rect.left < self.left_bound:
            self.speed *= -1

    def draw(self, surface, camera_x):
        if not self.alive:
            return
        r = self.rect.move(-camera_x, 0)
        pygame.draw.ellipse(surface, ENEMY_COLOR, r)
        eye_y = r.y + 10
        pygame.draw.circle(surface, WHITE, (r.x + 8, eye_y), 4)
        pygame.draw.circle(surface, WHITE, (r.x + 22, eye_y), 4)
        pygame.draw.circle(surface, (0, 0, 0), (r.x + 8, eye_y), 2)
        pygame.draw.circle(surface, (0, 0, 0), (r.x + 22, eye_y), 2)


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 40)
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing_right = True
        self.lives = 3
        self.score = 0
        self.alive = True

    def handle_input(self, keys):
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -MOVE_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = MOVE_SPEED
            self.facing_right = True
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False

    def update(self, platforms):
        self.vel_y += GRAVITY
        if self.vel_y > 18:
            self.vel_y = 18

        self.rect.x += self.vel_x
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel_x > 0:
                    self.rect.right = p.rect.left
                elif self.vel_x < 0:
                    self.rect.left = p.rect.right

        self.rect.y += int(self.vel_y)
        self.on_ground = False
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel_y > 0:
                    self.rect.bottom = p.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = p.rect.bottom
                    self.vel_y = 0

        if self.rect.top > HEIGHT + 200:
            self.lose_life()

    def lose_life(self):
        self.lives -= 1
        if self.lives <= 0:
            self.alive = False
        else:
            self.rect.topleft = (100, 250)
            self.vel_y = 0

    def draw(self, surface, camera_x):
        r = self.rect.move(-camera_x, 0)
        pygame.draw.rect(surface, PLAYER_COLOR, r, border_radius=6)
        # cap
        pygame.draw.rect(surface, PLAYER_ACCENT, (r.x, r.y, r.width, 10), border_radius=4)
        # eyes (direction indicator)
        eye_x = r.x + (r.width - 8) if self.facing_right else r.x + 2
        pygame.draw.circle(surface, WHITE, (eye_x + 4, r.y + 18), 5)
        pygame.draw.circle(surface, (0, 0, 0), (eye_x + 4, r.y + 18), 2)


def build_level():
    platforms = [
        Platform(0, 400, 600, 50),
        Platform(650, 400, 300, 50),
        Platform(1000, 340, 150, 20),
        Platform(1200, 400, 400, 50),
        Platform(1650, 300, 150, 20),
        Platform(1850, 400, 500, 50),
        Platform(2400, 250, 150, 20),
        Platform(2600, 400, 600, 50),
    ]
    coins = [
        Coin(300, 350), Coin(340, 350), Coin(380, 350),
        Coin(1020, 300), Coin(1060, 300),
        Coin(1300, 350), Coin(1340, 350), Coin(1380, 350),
        Coin(1680, 260),
        Coin(1900, 350), Coin(1940, 350),
        Coin(2420, 210), Coin(2460, 210),
        Coin(2700, 350), Coin(2740, 350), Coin(2780, 350),
    ]
    enemies = [
        Enemy(700, 370, 650, 900),
        Enemy(1250, 370, 1200, 1550),
        Enemy(1900, 370, 1850, 2300),
        Enemy(2650, 370, 2600, 3100),
    ]
    level_length = 3200
    flag_x = level_length - 100
    return platforms, coins, enemies, level_length, flag_x


def draw_background(surface, camera_x):
    surface.fill(SKY)
    # simple parallax clouds
    for i in range(6):
        cx = (i * 300 - int(camera_x * 0.3)) % (WIDTH + 300) - 150
        pygame.draw.ellipse(surface, WHITE, (cx, 60 + (i % 3) * 30, 90, 40))
        pygame.draw.ellipse(surface, WHITE, (cx + 40, 50 + (i % 3) * 30, 70, 35))


def draw_hud(surface, player, level_length, camera_x):
    score_text = font_med.render(f"Score: {player.score}", True, (20, 20, 30))
    lives_text = font_med.render(f"Lives: {player.lives}", True, (20, 20, 30))
    surface.blit(score_text, (16, 12))
    surface.blit(lives_text, (16, 40))

    progress = max(0, min(1, (player.rect.x) / level_length))
    bar_w = 200
    pygame.draw.rect(surface, (255, 255, 255), (WIDTH - bar_w - 20, 16, bar_w, 14), border_radius=6)
    pygame.draw.rect(surface, (60, 200, 120), (WIDTH - bar_w - 20, 16, int(bar_w * progress), 14), border_radius=6)


def draw_center_message(surface, title, subtitle):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(160)
    overlay.fill((10, 10, 20))
    surface.blit(overlay, (0, 0))

    title_surf = font_big.render(title, True, WHITE)
    sub_surf = font_small.render(subtitle, True, WHITE)
    surface.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
    surface.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))


async def main():
    platforms, coins, enemies, level_length, flag_x = build_level()
    player = Player(100, 250)
    camera_x = 0
    t = 0
    won = False
    game_over = False

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        t += dt * 3

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                if game_over or won:
                    platforms, coins, enemies, level_length, flag_x = build_level()
                    player = Player(100, 250)
                    camera_x = 0
                    won = False
                    game_over = False

        keys = pygame.key.get_pressed()

        if not game_over and not won:
            player.handle_input(keys)
            player.update(platforms)

            for enemy in enemies:
                enemy.update()
                if enemy.alive and player.rect.colliderect(enemy.rect):
                    if player.vel_y > 0 and player.rect.bottom - enemy.rect.top < 16:
                        enemy.alive = False
                        player.vel_y = JUMP_STRENGTH * 0.6
                        player.score += 50
                    else:
                        player.lose_life()
                        player.rect.x -= 40

            for coin in coins:
                if not coin.collected and player.rect.colliderect(coin.rect):
                    coin.collected = True
                    player.score += 10

            if player.rect.x >= flag_x:
                won = True

            if not player.alive:
                game_over = True

            target_cam = player.rect.centerx - WIDTH // 3
            camera_x += (target_cam - camera_x) * 0.1
            camera_x = max(0, min(camera_x, level_length - WIDTH))

        draw_background(screen, camera_x)

        for p in platforms:
            p.draw(screen, camera_x)
        for c in coins:
            c.draw(screen, camera_x, t)
        for e in enemies:
            e.draw(screen, camera_x)

        # flag
        fx = flag_x - camera_x
        pygame.draw.rect(screen, FLAG_POLE, (fx, 250, 6, 150))
        pygame.draw.polygon(screen, FLAG_CLOTH, [(fx + 6, 250), (fx + 46, 265), (fx + 6, 280)])

        player.draw(screen, camera_x)
        draw_hud(screen, player, level_length, camera_x)

        if game_over:
            draw_center_message(screen, "Game Over", "Press R to restart")
        elif won:
            draw_center_message(screen, "You Win! 🎉", f"Final Score: {player.score} — Press R to play again")

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
