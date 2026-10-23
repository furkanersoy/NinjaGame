import argparse
import json
import sys
import math
import random
from pathlib import Path

import pygame

from scripts.subjects import load_image, load_images, Animation
from scripts.entities import Player, Enemy
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.killAnimation import Particle
from scripts.spark import Spark

class Game:
    def __init__(self, map_path=None):
        pygame.init()

        self.project_root = Path(__file__).resolve().parent
        maps_dir = self.project_root / 'data' / 'maps'
        self.level_ids = sorted(
            int(path.stem) for path in maps_dir.glob('*.json') if path.stem.isdigit()
        )
        if not self.level_ids:
            raise FileNotFoundError(f'No numbered map files found in {maps_dir}')
        self.custom_map = None
        if map_path:
            self.custom_map = Path(map_path)
            if not self.custom_map.is_absolute():
                self.custom_map = self.project_root / self.custom_map
            self.map_paths = [self.custom_map]
        else:
            self.map_paths = [maps_dir / f'{map_id}.json' for map_id in self.level_ids]

        self.save_path = Path.home() / '.ninjagame' / 'save.json'
        self.save_data = self._read_save()
        try:
            saved_level = max(0, int(self.save_data.get('level_index', 0)))
        except (TypeError, ValueError):
            saved_level = 0
        self.level_index = 0 if self.custom_map else min(saved_level, len(self.map_paths) - 1)
        self.music_volume = self._clamp_volume(self.save_data.get('music_volume', 0.2), 0.2)
        self.sfx_volume = self._clamp_volume(self.save_data.get('sfx_volume', 0.6), 0.6)
        self.controls = {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'jump': pygame.K_UP, 'dash': pygame.K_x}
        saved_controls = self.save_data.get('controls', {})
        if not isinstance(saved_controls, dict):
            saved_controls = {}
        for control in self.controls:
            try:
                self.controls[control] = int(saved_controls.get(control, self.controls[control]))
            except (TypeError, ValueError):
                pass
        self.paused = False
        self.pause_selection = 0
        self.awaiting_binding = False
        self.completed = False

        pygame.display.set_caption('Ninja Game')
        self.screen = pygame.display.set_mode((960, 720), pygame.RESIZABLE)
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()
        
        self.movement = [False, False]
        self.climb = False
        
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'),
            'background': load_image('background2.png'),
            'clouds': load_images('clouds'),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),
            'player/run': Animation(load_images('entities/player/run'), img_dur=4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'gun': load_image('gun.png'),
            'projectile': load_image('projectile.png'),
        }
        
        self.sfx = {
            'jump': pygame.mixer.Sound(self.project_root / 'data' / 'sfx' / 'jump.wav'),
            'dash': pygame.mixer.Sound(self.project_root / 'data' / 'sfx' / 'dash.wav'),
            'hit': pygame.mixer.Sound(self.project_root / 'data' / 'sfx' / 'hit.wav'),
            'shoot': pygame.mixer.Sound(self.project_root / 'data' / 'sfx' / 'shoot.wav'),
            'ambience': pygame.mixer.Sound(self.project_root / 'data' / 'sfx' / 'ambience.wav'),
        }
        
        self._apply_volumes()
        
        self.clouds = Clouds(self.assets['clouds'], count=16)
        
        self.player = Player(self, (50, 50), (8, 15))
        
        self.tilemap = Tilemap(self, tile_size=16)
        
        self.load_level(self.level_index)
        
        self.screenshake = 0

    @staticmethod
    def _clamp_volume(value, default):
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return default
        
    def _read_save(self):
        try:
            with self.save_path.open('r', encoding='utf-8') as save_file:
                data = json.load(save_file)
                return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _write_save(self):
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        self.save_data.update({
            'music_volume': self.music_volume,
            'sfx_volume': self.sfx_volume,
            'controls': self.controls,
        })
        if not self.custom_map:
            self.save_data['level_index'] = self.level_index
        with self.save_path.open('w', encoding='utf-8') as save_file:
            json.dump(self.save_data, save_file, indent=2)

    def _apply_volumes(self):
        pygame.mixer.music.set_volume(self.music_volume)
        base_volumes = {'jump': 1.0, 'dash': 0.1 / 0.6, 'hit': 1.0, 'shoot': 0.4 / 0.6, 'ambience': 0.2 / 0.6}
        for name, sound in self.sfx.items():
            sound.set_volume(min(1.0, base_volumes[name] * self.sfx_volume))

    def load_level(self, level_index):
        self.tilemap.load(self.map_paths[level_index])
        self.player.climb_energy = self.player.max_climb_energy
        self.player.wall_slide = False
        self.player.velocity = [0, 0]
        self.player.dashing = 0
        
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))
            
        self.enemies = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                self.player.air_time = 0
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))
            
        self.projectiles = []
        self.particles = []
        self.sparks = []
        
        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30
        
    def run(self):
        pygame.mixer.music.load(self.project_root / 'data' / 'music.wav')
        self._apply_volumes()
        pygame.mixer.music.play(-1)
        
        self.sfx['ambience'].play(-1)
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if self.awaiting_binding:
                        if event.key != pygame.K_ESCAPE:
                            control_name = ('left', 'right', 'jump', 'dash')[self.pause_selection - 1]
                            self.controls[control_name] = event.key
                            self._write_save()
                        self.awaiting_binding = False
                        continue
                    if self.completed and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.level_index = 0
                        self.completed = False
                        self.save_data['completed'] = False
                        self._write_save()
                        self.load_level(self.level_index)
                    elif event.key == pygame.K_ESCAPE and not self.completed:
                        self.paused = not self.paused
                        if self.paused:
                            self.movement = [False, False]
                            self.climb = False
                    elif self.paused:
                        if event.key in (pygame.K_UP, pygame.K_w):
                            self.pause_selection = (self.pause_selection - 1) % 8
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            self.pause_selection = (self.pause_selection + 1) % 8
                        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                            change = 0.05 if event.key == pygame.K_RIGHT else -0.05
                            if self.pause_selection == 5:
                                self.music_volume = max(0.0, min(1.0, self.music_volume + change))
                            elif self.pause_selection == 6:
                                self.sfx_volume = max(0.0, min(1.0, self.sfx_volume + change))
                            self._apply_volumes()
                            self._write_save()
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            if self.pause_selection == 0:
                                self.paused = False
                            elif 1 <= self.pause_selection <= 4:
                                self.awaiting_binding = True
                            elif self.pause_selection == 7:
                                pygame.quit()
                                sys.exit()
                    elif not self.completed:
                        if event.key == self.controls['left']:
                            self.movement[0] = True
                        elif event.key == self.controls['right']:
                            self.movement[1] = True
                        elif event.key == self.controls['jump']:
                            self.climb = True
                            if not self.player.wall_slide and self.player.jump():
                                self.sfx['jump'].play()
                        elif event.key == self.controls['dash']:
                            self.player.dash()
                if event.type == pygame.KEYUP:
                    if event.key == self.controls['left']:
                        self.movement[0] = False
                    elif event.key == self.controls['right']:
                        self.movement[1] = False
                    elif event.key == self.controls['jump']:
                        self.climb = False

            if self.paused or self.completed:
                self.display_2.blit(self.assets['background'], (0, 0))
                overlay = pygame.Surface(self.display_2.get_size(), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 190))
                self.display_2.blit(overlay, (0, 0))
                title = 'Bölüm Tamamlandı!' if self.completed else 'Duraklatıldı'
                title_image = pygame.font.Font(None, 36).render(title, True, (255, 255, 255))
                self.display_2.blit(title_image, title_image.get_rect(center=(160, 27)))
                if self.completed:
                    hint = pygame.font.Font(None, 22).render('Yeniden başlamak için Enter', True, (220, 220, 220))
                    self.display_2.blit(hint, hint.get_rect(center=(160, 110)))
                else:
                    options = [
                        'Devam Et',
                        f'Sola git: {pygame.key.name(self.controls["left"])}',
                        f'Sağa git: {pygame.key.name(self.controls["right"])}',
                        f'Zıpla/tırman: {pygame.key.name(self.controls["jump"])}',
                        f'Atıl: {pygame.key.name(self.controls["dash"])}',
                        f'Müzik: {int(self.music_volume * 100)}%',
                        f'Ses efektleri: {int(self.sfx_volume * 100)}%',
                        'Oyundan çık',
                    ]
                    font = pygame.font.Font(None, 26)
                    for index, label in enumerate(options):
                        color = (255, 220, 90) if index == self.pause_selection else (230, 230, 230)
                        image = font.render(label, True, color)
                        self.display_2.blit(image, image.get_rect(center=(160, 58 + index * 21)))
                    help_text = 'Yeni tuşa basın (Esc iptal)' if self.awaiting_binding else 'Enter: seç | ←/→: ses düzeyi'
                    hint = pygame.font.Font(None, 18).render(help_text, True, (180, 180, 180))
                    self.display_2.blit(hint, hint.get_rect(center=(160, 235)))
                self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), (0, 0))
                pygame.display.update()
                self.clock.tick(60)
                continue

            self.display.fill((0, 0, 0, 0))
            self.display_2.blit(self.assets['background'], (0, 0))
            
            self.screenshake = max(0, self.screenshake - 1)
            
            if not self.enemies and not self.custom_map:
                self.transition += 1
                if self.transition > 30:
                    if self.level_index + 1 < len(self.map_paths):
                        self.level_index += 1
                        self._write_save()
                        self.load_level(self.level_index)
                    elif not self.completed:
                        self.completed = True
                        self.save_data['completed'] = True
                        self._write_save()
            if self.transition < 0:
                self.transition += 1
            
            if self.dead:
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    self.load_level(self.level_index)
            
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))
            
            self.clouds.update()
            self.clouds.render(self.display_2, offset=render_scroll)
            
            self.tilemap.render(self.display, offset=render_scroll)
            
            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)
            
            if not self.dead:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                self.player.render(self.display, offset=render_scroll)

            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                img = self.assets['projectile']
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for i in range(4):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                elif projectile[2] > 360:
                    self.projectiles.remove(projectile)
                elif abs(self.player.dashing) < 50:
                    if self.player.rect().collidepoint(projectile[0]):
                        self.projectiles.remove(projectile)
                        self.dead += 1
                        self.sfx['hit'].play()
                        self.screenshake = max(16, self.screenshake)
                        for i in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                            self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                        
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)
                    
            display_mask = pygame.mask.from_surface(self.display)
            display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_sillhouette, offset)
            
            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)
            
            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))
                
            self.display_2.blit(self.display, (0, 0))

            if self.player.climb_energy < self.player.max_climb_energy:
                pygame.draw.rect(self.display_2, (25, 25, 25), (8, 8, 74, 9))
                energy_width = round(70 * self.player.climb_energy / self.player.max_climb_energy)
                pygame.draw.rect(self.display_2, (70, 210, 125), (10, 10, energy_width, 5))
            
            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset)
            pygame.display.update()
            self.clock.tick(60)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ninja Game')
    parser.add_argument('--map', help='Editör haritasını oyunda önizle (örn. editor/world.json)')
    args = parser.parse_args()
    Game(map_path=args.map).run()
