from __future__ import annotations

import argparse
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import pygame


WIDTH = 960
HEIGHT = 540
FPS = 60
TARGET_KILLS = 12
MAX_LIVES = 3

INK = (7, 13, 31)
ICE = (177, 237, 244)
CYAN = (81, 235, 227)
GOLD = (255, 213, 126)
CORAL = (255, 122, 127)
WHITE = (244, 249, 255)
MUTED = (169, 188, 207)


def asset_directory() -> Path:
    """Keep assets next to the script in development and next to the EXE in a build."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "assets"
    return Path(__file__).resolve().parent / "assets"


def load_font(size: int, bold: bool = False) -> pygame.font.Font:
    return pygame.font.SysFont("arial", size, bold=bold)


@dataclass
class Projectile:
    x: float
    y: float
    vx: float
    vy: float
    hostile: bool
    image: pygame.Surface | None = None

    @property
    def rect(self) -> pygame.Rect:
        if self.hostile:
            return pygame.Rect(int(self.x - 17), int(self.y - 7), 34, 14)
        return pygame.Rect(int(self.x - 15), int(self.y - 5), 30, 10)

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt


@dataclass
class Enemy:
    x: float
    y: float
    speed: float
    phase: float
    fire_delay: float
    health: int = 2

    def update(self, dt: float, elapsed: float) -> None:
        self.x -= self.speed * dt
        self.y += math.sin(elapsed * 2.7 + self.phase) * 37 * dt

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - 70), int(self.y - 42), 140, 84)


class AuroraZero:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.random = random.Random()
        self.assets_dir = asset_directory()
        self.backgrounds = self._load_backgrounds()
        self.enemy_image = self._load_image("Enemy3.png", size=(150, 88))
        self.enemy_shot_image = self._load_image("Enemy3Shot.png", size=(54, 16))
        self.music_enabled = self._load_music()

        self.font_small = load_font(16)
        self.font_medium = load_font(22, bold=True)
        self.font_large = load_font(58, bold=True)
        self.font_huge = load_font(72, bold=True)

        self.state = "menu"
        self.player_x = 150.0
        self.player_y = HEIGHT / 2
        self.lives = MAX_LIVES
        self.kills = 0
        self.score = 0
        self.elapsed = 0.0
        self.background_scroll = 0.0
        self.shot_cooldown = 0.0
        self.spawn_cooldown = 0.0
        self.invulnerable = 0.0
        self.player_shots: list[Projectile] = []
        self.enemy_shots: list[Projectile] = []
        self.enemies: list[Enemy] = []
        self.particles: list[list[float | tuple[int, int, int]]] = []

    def _load_image(self, filename: str, size: tuple[int, int] | None = None) -> pygame.Surface:
        path = self.assets_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Asset obrigatório não encontrado: {path}")
        image = pygame.image.load(str(path)).convert_alpha()
        if size:
            image = pygame.transform.smoothscale(image, size)
        return image

    def _load_backgrounds(self) -> list[pygame.Surface]:
        layers: list[pygame.Surface] = []
        for index in range(5):
            image = self._load_image(f"Level3Bg{index}.png")
            layers.append(pygame.transform.smoothscale(image, (WIDTH, HEIGHT)))
        return layers

    def _load_music(self) -> bool:
        path = self.assets_dir / "Level3.mp3"
        if not path.is_file():
            print(f"Áudio não encontrado; o jogo continuará sem música: {path}", file=sys.stderr)
            return False
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(0.28)
            pygame.mixer.music.play(-1)
            return True
        except pygame.error as exc:
            print(f"Não foi possível iniciar a música: {exc}", file=sys.stderr)
            return False

    def reset_game(self) -> None:
        self.state = "playing"
        self.player_x = 150.0
        self.player_y = HEIGHT / 2
        self.lives = MAX_LIVES
        self.kills = 0
        self.score = 0
        self.elapsed = 0.0
        self.shot_cooldown = 0.0
        self.spawn_cooldown = 0.3
        self.invulnerable = 0.0
        self.player_shots.clear()
        self.enemy_shots.clear()
        self.enemies.clear()
        self.particles.clear()

    def _player_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.player_x - 25), int(self.player_y - 16), 50, 32)

    def _spawn_enemy(self) -> None:
        difficulty = min(self.elapsed / 65, 1.0)
        self.enemies.append(
            Enemy(
                x=WIDTH + 90,
                y=self.random.uniform(82, HEIGHT - 70),
                speed=self.random.uniform(140, 205) + difficulty * 75,
                phase=self.random.uniform(0, math.tau),
                fire_delay=self.random.uniform(0.75, 1.45),
            )
        )

    def _lose_life(self) -> None:
        if self.invulnerable > 0 or self.state != "playing":
            return
        self.lives -= 1
        self.invulnerable = 1.35
        self.player_x = 150
        self.player_y = HEIGHT / 2
        self.enemy_shots.clear()
        self._burst(self.player_x, self.player_y, CORAL, 24)
        if self.lives <= 0:
            self.state = "lost"

    def _burst(
        self,
        x: float,
        y: float,
        color: tuple[int, int, int],
        amount: int = 12,
    ) -> None:
        for _ in range(amount):
            angle = self.random.random() * math.tau
            speed = self.random.uniform(35, 180)
            self.particles.append(
                [x, y, math.cos(angle) * speed, math.sin(angle) * speed, self.random.uniform(0.18, 0.55), color]
            )

    def _handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_v:
                self.music_enabled = not self.music_enabled
                if pygame.mixer.get_init():
                    pygame.mixer.music.set_volume(0.28 if self.music_enabled else 0)
            elif self.state == "menu" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.reset_game()
            elif self.state in ("won", "lost"):
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                    self.reset_game()
                elif event.key == pygame.K_ESCAPE:
                    self.state = "menu"
            elif self.state == "playing":
                if event.key == pygame.K_p:
                    self.state = "paused"
                elif event.key == pygame.K_ESCAPE:
                    self.state = "menu"
            elif self.state == "paused":
                if event.key == pygame.K_p or event.key == pygame.K_RETURN:
                    self.state = "playing"
                elif event.key == pygame.K_ESCAPE:
                    self.state = "menu"
        return True

    def _update(self, dt: float) -> None:
        self.background_scroll += dt
        if self.state != "playing":
            return

        self.elapsed += dt
        self.shot_cooldown = max(0, self.shot_cooldown - dt)
        self.spawn_cooldown -= dt
        self.invulnerable = max(0, self.invulnerable - dt)

        keys = pygame.key.get_pressed()
        movement = pygame.Vector2(
            float(keys[pygame.K_RIGHT] or keys[pygame.K_d])
            - float(keys[pygame.K_LEFT] or keys[pygame.K_a]),
            float(keys[pygame.K_DOWN] or keys[pygame.K_s])
            - float(keys[pygame.K_UP] or keys[pygame.K_w]),
        )
        if movement.length_squared():
            movement.normalize_ip()
            self.player_x += movement.x * 310 * dt
            self.player_y += movement.y * 310 * dt
        self.player_x = max(40, min(WIDTH - 50, self.player_x))
        self.player_y = max(56, min(HEIGHT - 44, self.player_y))

        if keys[pygame.K_SPACE] and self.shot_cooldown <= 0:
            self.player_shots.append(Projectile(self.player_x + 25, self.player_y, 560, 0, False))
            self.shot_cooldown = 0.22

        if self.kills < TARGET_KILLS and self.spawn_cooldown <= 0:
            self._spawn_enemy()
            self.spawn_cooldown = max(0.58, 1.35 - self.elapsed / 170)

        for enemy in self.enemies:
            enemy.update(dt, self.elapsed)
            enemy.fire_delay -= dt
            if enemy.fire_delay <= 0:
                direction = pygame.Vector2(self.player_x - enemy.x, self.player_y - enemy.y)
                if direction.length_squared():
                    direction.normalize_ip()
                velocity = direction * (270 + min(self.elapsed, 60))
                self.enemy_shots.append(
                    Projectile(enemy.x - 45, enemy.y, velocity.x, velocity.y, True, self.enemy_shot_image)
                )
                enemy.fire_delay = self.random.uniform(1.0, 1.7)

        for shot in self.player_shots:
            shot.update(dt)
        for shot in self.enemy_shots:
            shot.update(dt)
        for particle in self.particles:
            particle[0] = float(particle[0]) + float(particle[2]) * dt
            particle[1] = float(particle[1]) + float(particle[3]) * dt
            particle[4] = float(particle[4]) - dt

        self.player_shots = [shot for shot in self.player_shots if shot.x < WIDTH + 40]
        self.enemy_shots = [
            shot for shot in self.enemy_shots if -40 < shot.x < WIDTH + 40 and -40 < shot.y < HEIGHT + 40
        ]
        self.particles = [particle for particle in self.particles if float(particle[4]) > 0]

        player_rect = self._player_rect()
        for shot in list(self.enemy_shots):
            if shot.rect.colliderect(player_rect):
                self.enemy_shots.remove(shot)
                self._lose_life()
                break

        for enemy in list(self.enemies):
            if enemy.rect.colliderect(player_rect):
                self._lose_life()
                if self.state != "playing":
                    break
            for shot in list(self.player_shots):
                if shot.rect.colliderect(enemy.rect):
                    self.player_shots.remove(shot)
                    enemy.health -= 1
                    self._burst(shot.x, shot.y, GOLD, 5)
                    if enemy.health <= 0:
                        self.enemies.remove(enemy)
                        self.kills += 1
                        self.score += 100
                        self._burst(enemy.x, enemy.y, CYAN, 22)
                        if self.kills >= TARGET_KILLS:
                            self.state = "won"
                    break
            if self.state != "playing":
                break

        for enemy in list(self.enemies):
            if enemy.x < -100:
                self.enemies.remove(enemy)
                self._lose_life()

    def _draw_background(self) -> None:
        self.screen.fill(INK)
        speeds = (0, 2.5, 7, 16, 31)
        for layer, speed in zip(self.backgrounds, speeds):
            width = layer.get_width()
            offset = int(self.background_scroll * speed) % width if speed else 0
            self.screen.blit(layer, (-offset, 0))
            if offset:
                self.screen.blit(layer, (width - offset, 0))

    def _draw_player(self) -> None:
        if self.invulnerable > 0 and int(self.invulnerable * 12) % 2:
            return
        x, y = int(self.player_x), int(self.player_y)
        flame = 10 + int(5 * (0.5 + 0.5 * math.sin(self.elapsed * 24)))
        pygame.draw.polygon(self.screen, GOLD, [(x - 21, y - 3), (x - 36 - flame, y), (x - 21, y + 4)])
        pygame.draw.polygon(self.screen, (28, 76, 110), [(x - 21, y - 12), (x + 22, y), (x - 20, y + 12)])
        pygame.draw.polygon(self.screen, CYAN, [(x - 10, y - 9), (x + 27, y), (x - 10, y + 9)])
        pygame.draw.polygon(self.screen, WHITE, [(x + 11, y - 5), (x + 30, y), (x + 11, y + 5)])
        pygame.draw.ellipse(self.screen, (15, 33, 64), (x - 4, y - 5, 15, 10))
        pygame.draw.ellipse(self.screen, (141, 255, 250), (x - 1, y - 3, 8, 6))

    def _draw_shots(self) -> None:
        for shot in self.player_shots:
            pygame.draw.rect(self.screen, CYAN, shot.rect, border_radius=4)
            glow = pygame.Rect(shot.rect.x + 2, shot.rect.y + 2, shot.rect.width - 4, 2)
            pygame.draw.rect(self.screen, WHITE, glow, border_radius=2)
        for shot in self.enemy_shots:
            if shot.image:
                angle = math.degrees(math.atan2(-shot.vy, shot.vx))
                image = pygame.transform.rotate(shot.image, angle)
                self.screen.blit(image, image.get_rect(center=(int(shot.x), int(shot.y))))
            else:
                pygame.draw.circle(self.screen, CORAL, (int(shot.x), int(shot.y)), 7)

    def _draw_particles(self) -> None:
        for x, y, _vx, _vy, life, color in self.particles:
            radius = max(1, int(5 * min(1, float(life) / 0.3)))
            pygame.draw.circle(self.screen, color, (int(float(x)), int(float(y))), radius)

    def _draw_hud(self) -> None:
        bar = pygame.Surface((WIDTH, 54), pygame.SRCALPHA)
        bar.fill((5, 12, 28, 196))
        self.screen.blit(bar, (0, 0))
        self._text("AURORA ZERO", 24, 17, self.font_small, CYAN)
        self._text(f"DRONES  {self.kills:02d}/{TARGET_KILLS}", 286, 16, self.font_small, WHITE)
        self._text(f"PONTOS  {self.score:04d}", 505, 16, self.font_small, GOLD)
        hearts = "◆ " * self.lives
        self._text(hearts.rstrip(), WIDTH - 128, 15, self.font_medium, CORAL)

    def _text(
        self,
        text: str,
        x: int,
        y: int,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        *,
        center: bool = False,
    ) -> pygame.Rect:
        image = font.render(text, True, color)
        rect = image.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(image, rect)
        return rect

    def _panel(self, rect: pygame.Rect, color: tuple[int, int, int, int] = (5, 12, 29, 222)) -> None:
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill(color)
        self.screen.blit(panel, rect.topleft)
        pygame.draw.rect(self.screen, (102, 199, 219, 100), rect, width=1, border_radius=8)

    def _draw_menu(self) -> None:
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((3, 9, 24, 112))
        self.screen.blit(shade, (0, 0))

        self._text("MISSÃO DE DEFESA // SETOR POLAR", 70, 50, self.font_small, CYAN)
        self._text("AURORA ZERO", 65, 78, self.font_huge, WHITE)
        self._text("A última linha entre a colônia e a tempestade.", 70, 159, self.font_medium, ICE)
        self._text(
            "Derrube 12 drones para vencer. Você tem 3 vidas.",
            70,
            199,
            self.font_small,
            MUTED,
        )

        panel = pygame.Rect(70, 253, 820, 159)
        self._panel(panel)
        self._text("CONTROLES", 94, 271, self.font_small, GOLD)
        controls = [
            ("W A S D  /  SETAS", "Mover a nave"),
            ("ESPAÇO", "Disparar"),
            ("P", "Pausar / continuar"),
            ("ESC", "Voltar ao menu"),
        ]
        for index, (key, action) in enumerate(controls):
            y = 302 + index * 25
            self._text(key, 97, y, self.font_small, CYAN)
            self._text(action, 320, y, self.font_small, WHITE)
        self._text("V  alterna a música", 650, 374, self.font_small, MUTED)

        pulse = 0.74 + 0.26 * math.sin(pygame.time.get_ticks() / 400)
        prompt_color = tuple(int(component * pulse) for component in GOLD)
        self._text("PRESSIONE ENTER PARA COMEÇAR", WIDTH // 2, 464, self.font_medium, prompt_color, center=True)

    def _draw_overlay(self, title: str, subtitle: str, accent: tuple[int, int, int], prompt: str) -> None:
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((2, 7, 19, 175))
        self.screen.blit(shade, (0, 0))
        panel = pygame.Rect(210, 169, 540, 206)
        self._panel(panel, (5, 12, 29, 238))
        self._text(title, WIDTH // 2, 219, self.font_large, accent, center=True)
        self._text(subtitle, WIDTH // 2, 274, self.font_small, WHITE, center=True)
        self._text(prompt, WIDTH // 2, 326, self.font_small, GOLD, center=True)

    def _draw(self) -> None:
        self._draw_background()
        self._draw_shots()
        for enemy in self.enemies:
            self.screen.blit(self.enemy_image, self.enemy_image.get_rect(center=enemy.rect.center))
            if enemy.health == 1:
                pygame.draw.rect(self.screen, CORAL, (enemy.x - 25, enemy.y - 53, 50, 3), border_radius=2)
        self._draw_particles()
        if self.state != "menu":
            self._draw_player()
            self._draw_hud()
        if self.state == "menu":
            self._draw_menu()
        elif self.state == "paused":
            self._draw_overlay("PAUSADO", "Respire. Os drones esperam.", CYAN, "P ou ENTER continua  •  ESC volta ao menu")
        elif self.state == "won":
            self._draw_overlay("SETOR SEGURO", f"{self.score:04d} pontos  •  {self.kills} drones abatidos", CYAN, "ENTER joga novamente  •  ESC volta ao menu")
        elif self.state == "lost":
            self._draw_overlay("SINAL PERDIDO", f"{self.kills}/{TARGET_KILLS} drones abatidos  •  {self.score:04d} pontos", CORAL, "ENTER tenta novamente  •  ESC volta ao menu")

    def run(self) -> None:
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000, 0.04)
            running = self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Aurora Zero — jogo 2D de combate espacial.")
    parser.add_argument("--self-test", action="store_true", help="carrega os assets e desenha um quadro sem abrir uma janela.")
    args = parser.parse_args()

    if args.self_test:
        import os

        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    pygame.init()
    pygame.display.set_caption("Aurora Zero")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    game = AuroraZero(screen)

    if args.self_test:
        game._draw()
        pygame.display.flip()
        pygame.quit()
        print("Self-test concluído: assets carregados e primeiro quadro desenhado.")
        return

    try:
        game.run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
