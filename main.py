import pygame
import sys
import random
import math
import json
import os
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional
import time

# Инициализация Pygame
pygame.init()
pygame.mixer.init()
pygame.font.init()

# Константы экрана
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# Цвета (расширенная палитра)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 50, 255)
YELLOW = (255, 255, 50)
CYAN = (50, 255, 255)
MAGENTA = (255, 50, 255)
ORANGE = (255, 165, 0)
PURPLE = (160, 32, 240)
PINK = (255, 192, 203)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)
LIGHT_BLUE = (173, 216, 230)
DARK_RED = (139, 0, 0)
DARK_GREEN = (0, 100, 0)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
BRONZE = (205, 127, 50)

# Типы врагов
class EnemyType(Enum):
    CHASER = "chaser"        # преследователь
    SHOOTER = "shooter"       # стрелок
    TANK = "tank"            # танк (много жизней)
    FAST = "fast"            # быстрый
    SWARM = "swarm"          # рой (маленькие)
    BOMBER = "bomber"        # самоубийца
    SPLITTER = "splitter"     # разделяется при смерти
    TELEPORTER = "teleporter" # телепортируется
    SHIELDED = "shielded"     # с щитом
    BOSS = "boss"            # босс

# Типы усилений
class PowerUpType(Enum):
    HEALTH = "health"           # восстановление здоровья
    SHIELD = "shield"           # временный щит
    DOUBLE_SHOT = "double_shot" # двойной выстрел
    TRIPLE_SHOT = "triple_shot" # тройной выстрел
    SPREAD_SHOT = "spread_shot" # веерный выстрел
    LASER = "laser"             # лазер
    SPEED_BOOST = "speed_boost" # ускорение
    INVINCIBILITY = "invincibility" # неуязвимость
    NUKE = "nuke"               # ядерный удар (уничтожает всех врагов)
    EXTRA_LIFE = "extra_life"    # дополнительная жизнь
    MONEY = "money"              # бонусные очки
    FREEZE = "freeze"            # заморозка врагов
    PIERCE = "pierce"            # пробивающие пули
    HOMING = "homing"            # самонаводящиеся пули

# Класс для частиц (эффекты)
class Particle:
    def __init__(self, x, y, color, velocity, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.vx, self.vy = velocity
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2  # гравитация
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self, screen):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        size = int(self.size * (self.lifetime / self.max_lifetime))
        if size > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)

# Класс для врага с расширенными возможностями
class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_type=EnemyType.CHASER, pos=None):
        super().__init__()
        self.type = enemy_type
        self.set_stats()
        
        # Создание изображения в зависимости от типа
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.draw_enemy()
        self.rect = self.image.get_rect()
        
        # Позиция
        if pos:
            self.rect.center = pos
        else:
            self.spawn_outside()
        
        # Специальные атрибуты
        self.health = self.max_health
        self.shoot_timer = random.randint(0, 60)
        self.teleport_timer = 0
        self.shield_active = False
        self.shield_hits = 0
        self.angle = 0
        self.particles = []
        
    def set_stats(self):
        """Установка характеристик в зависимости от типа"""
        stats = {
            EnemyType.CHASER: {"size": 30, "speed": 2, "health": 1, "color": RED, "points": 10},
            EnemyType.SHOOTER: {"size": 35, "speed": 1.5, "health": 2, "color": ORANGE, "points": 20, "shoot_cooldown": 90},
            EnemyType.TANK: {"size": 50, "speed": 1, "health": 5, "color": DARK_RED, "points": 50},
            EnemyType.FAST: {"size": 25, "speed": 4, "health": 1, "color": YELLOW, "points": 15},
            EnemyType.SWARM: {"size": 15, "speed": 3, "health": 1, "color": PINK, "points": 5},
            EnemyType.BOMBER: {"size": 30, "speed": 3.5, "health": 1, "color": MAGENTA, "points": 30},
            EnemyType.SPLITTER: {"size": 40, "speed": 1.5, "health": 2, "color": GREEN, "points": 25},
            EnemyType.TELEPORTER: {"size": 30, "speed": 2, "health": 1, "color": CYAN, "points": 40, "teleport_cooldown": 180},
            EnemyType.SHIELDED: {"size": 35, "speed": 1.5, "health": 2, "color": BLUE, "points": 35, "shield_hits": 3},
            EnemyType.BOSS: {"size": 120, "speed": 0.5, "health": 50, "color": PURPLE, "points": 500}
        }
        for key, value in stats[self.type].items():
            setattr(self, key, value)
        self.max_health = self.health
            
    def draw_enemy(self):
        """Отрисовка врага в зависимости от типа"""
        center = self.size // 2
        if self.type == EnemyType.CHASER:
            pygame.draw.circle(self.image, self.color, (center, center), center-2)
            pygame.draw.circle(self.image, BLACK, (center-5, center-5), 3)  # глаза
            pygame.draw.circle(self.image, BLACK, (center+5, center-5), 3)
        elif self.type == EnemyType.SHOOTER:
            pygame.draw.rect(self.image, self.color, (2, 2, self.size-4, self.size-4))
            pygame.draw.line(self.image, BLACK, (center, center), (center, 0), 2)  # пушка
        elif self.type == EnemyType.TANK:
            pygame.draw.rect(self.image, self.color, (2, 2, self.size-4, self.size-4))
            for i in range(4):  # гусеницы
                pygame.draw.rect(self.image, GRAY, (4, 4 + i*10, self.size-8, 4))
        elif self.type == EnemyType.FAST:
            pygame.draw.polygon(self.image, self.color, [(center, 2), (self.size-2, self.size-2), (2, self.size-2)])
        elif self.type == EnemyType.SWARM:
            for i in range(3):
                for j in range(3):
                    pygame.draw.circle(self.image, self.color, (5 + i*5, 5 + j*5), 2)
        elif self.type == EnemyType.BOMBER:
            pygame.draw.circle(self.image, self.color, (center, center), center-2)
            pygame.draw.circle(self.image, BLACK, (center, center), 5)  # бомба
        elif self.type == EnemyType.SPLITTER:
            pygame.draw.circle(self.image, self.color, (center, center), center-2)
            pygame.draw.line(self.image, BLACK, (center-5, center), (center+5, center), 2)
            pygame.draw.line(self.image, BLACK, (center, center-5), (center, center+5), 2)
        elif self.type == EnemyType.TELEPORTER:
            pygame.draw.circle(self.image, self.color, (center, center), center-2)
            pygame.draw.circle(self.image, BLACK, (center-3, center-3), 2)
            pygame.draw.circle(self.image, BLACK, (center+3, center+3), 2)
        elif self.type == EnemyType.SHIELDED:
            pygame.draw.circle(self.image, self.color, (center, center), center-2)
            pygame.draw.circle(self.image, CYAN, (center, center), center, 2)  # щит
        elif self.type == EnemyType.BOSS:
            pygame.draw.rect(self.image, self.color, (0, 0, self.size, self.size))
            pygame.draw.rect(self.image, GOLD, (10, 10, self.size-20, self.size-20), 3)
            for i in range(4):
                pygame.draw.circle(self.image, RED, (20 + i*25, 20), 5)
    
    def spawn_outside(self):
        """Появление за пределами экрана"""
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top':
            self.rect.x = random.randint(0, SCREEN_WIDTH - self.size)
            self.rect.y = -self.size
        elif side == 'bottom':
            self.rect.x = random.randint(0, SCREEN_WIDTH - self.size)
            self.rect.y = SCREEN_HEIGHT
        elif side == 'left':
            self.rect.x = -self.size
            self.rect.y = random.randint(0, SCREEN_HEIGHT - self.size)
        else:
            self.rect.x = SCREEN_WIDTH
            self.rect.y = random.randint(0, SCREEN_HEIGHT - self.size)
    
    def update(self, player, enemies, bullets):
        """Обновление врага"""
        if self.type == EnemyType.TELEPORTER:
            self.teleport_timer += 1
            if self.teleport_timer >= self.teleport_cooldown:
                self.teleport()
                self.teleport_timer = 0
        
        # Движение к игроку
        if self.type != EnemyType.SHOOTER or self.type != EnemyType.TANK:
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 0:
                speed = self.speed * (1.5 if self.type == EnemyType.BOMBER else 1)
                self.rect.x += (dx / dist) * speed
                self.rect.y += (dy / dist) * speed
        
        # Стрельба для SHOOTER
        if self.type == EnemyType.SHOOTER:
            self.shoot_timer += 1
            if self.shoot_timer >= self.shoot_cooldown:
                self.shoot_timer = 0
                bullet = EnemyBullet(self.rect.centerx, self.rect.centery, player.rect.center)
                bullets.add(bullet)
        
        # Вращение для BOMBER (эффект)
        if self.type == EnemyType.BOMBER:
            self.angle += 5
            self.image = pygame.transform.rotate(self.image, self.angle)
            self.rect = self.image.get_rect(center=self.rect.center)
        
        # Создание частиц для некоторых врагов
        if random.random() < 0.1:
            self.particles.append(Particle(
                self.rect.centerx, self.rect.centery,
                self.color, (random.uniform(-1, 1), random.uniform(-1, 1)), 10
            ))
        
        # Обновление частиц
        self.particles = [p for p in self.particles if p.update()]
    
    def teleport(self):
        """Телепортация врага"""
        new_x = random.randint(50, SCREEN_WIDTH - 50)
        new_y = random.randint(50, SCREEN_HEIGHT - 50)
        self.rect.center = (new_x, new_y)
        # Эффект телепортации
        for _ in range(20):
            self.particles.append(Particle(
                self.rect.centerx, self.rect.centery,
                CYAN, (random.uniform(-2, 2), random.uniform(-2, 2)), 20
            ))
    
    def hit(self, damage=1):
        """Получение урона"""
        if self.type == EnemyType.SHIELDED and not self.shield_active:
            self.shield_hits -= 1
            if self.shield_hits <= 0:
                self.shield_active = True
            return False
        else:
            self.health -= damage
            return self.health <= 0

# Класс для пули врага
class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_pos):
        super().__init__()
        self.image = pygame.Surface((5, 5))
        self.image.fill(ORANGE)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        # Направление к игроку
        dx = target_pos[0] - x
        dy = target_pos[1] - y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.vx = (dx / dist) * 5
            self.vy = (dy / dist) * 5
        else:
            self.vx = self.vy = 0
    
    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if (self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or
            self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT):
            self.kill()

# Класс для усилений
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, power_type=None):
        super().__init__()
        if not power_type:
            power_type = random.choice(list(PowerUpType))
        self.type = power_type
        self.size = 25
        
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.draw_powerup()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        # Движение вниз
        self.speed = 2
        self.angle = 0
        
        # Время жизни (в кадрах)
        self.lifetime = 600  # 10 секунд
    
    def draw_powerup(self):
        """Отрисовка усиления в зависимости от типа"""
        center = self.size // 2
        colors = {
            PowerUpType.HEALTH: GREEN,
            PowerUpType.SHIELD: CYAN,
            PowerUpType.DOUBLE_SHOT: YELLOW,
            PowerUpType.TRIPLE_SHOT: ORANGE,
            PowerUpType.SPREAD_SHOT: MAGENTA,
            PowerUpType.LASER: RED,
            PowerUpType.SPEED_BOOST: BLUE,
            PowerUpType.INVINCIBILITY: WHITE,
            PowerUpType.NUKE: PURPLE,
            PowerUpType.EXTRA_LIFE: PINK,
            PowerUpType.MONEY: GOLD,
            PowerUpType.FREEZE: LIGHT_BLUE,
            PowerUpType.PIERCE: GRAY,
            PowerUpType.HOMING: DARK_GREEN
        }
        color = colors[self.type]
        
        # Рисуем символ в зависимости от типа
        pygame.draw.circle(self.image, color, (center, center), center-2)
        if self.type == PowerUpType.HEALTH:
            pygame.draw.line(self.image, WHITE, (center-5, center), (center+5, center), 2)
            pygame.draw.line(self.image, WHITE, (center, center-5), (center, center+5), 2)
        elif self.type == PowerUpType.SHIELD:
            pygame.draw.circle(self.image, WHITE, (center, center), center-5, 2)
        elif self.type == PowerUpType.DOUBLE_SHOT:
            pygame.draw.line(self.image, WHITE, (center-8, center-4), (center, center), 2)
            pygame.draw.line(self.image, WHITE, (center, center), (center+8, center+4), 2)
        elif self.type == PowerUpType.NUKE:
            pygame.draw.circle(self.image, WHITE, (center, center), 5)
            for i in range(8):
                angle = i * 45
                x = center + math.cos(math.radians(angle)) * 12
                y = center + math.sin(math.radians(angle)) * 12
                pygame.draw.line(self.image, WHITE, (center, center), (x, y), 1)
    
    def update(self):
        self.rect.y += self.speed
        self.angle += 2
        self.lifetime -= 1
        
        if self.lifetime <= 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()

# Класс игрока с улучшенными возможностями
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.size = 40
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        # Основные характеристики
        self.base_speed = 5
        self.speed = self.base_speed
        self.max_health = 5
        self.health = self.max_health
        self.shield = 0
        self.score = 0
        self.money = 0
        self.level = 1
        self.exp = 0
        self.exp_to_next = 100
        
        # Оружие
        self.shoot_cooldown = 0
        self.shoot_delay = 15
        self.weapon_level = 1
        self.weapon_type = "normal"  # normal, double, triple, spread, laser, homing
        self.pierce = False
        self.homing = False
        
        # Бонусы
        self.invincible = False
        self.invincible_timer = 0
        self.frozen_enemies = False
        self.freeze_timer = 0
        self.speed_boost = False
        self.speed_boost_timer = 0
        
        # Анимация
        self.angle = 0
        self.particles = []
        self.trail = []
        
        # Инвентарь (активные бонусы)
        self.active_powerups = {}
        
        self.draw_player()
    
    def draw_player(self):
        """Отрисовка игрока"""
        center = self.size // 2
        # Основной корпус
        pygame.draw.rect(self.image, CYAN, (5, 5, self.size-10, self.size-10))
        # Пушка
        pygame.draw.rect(self.image, WHITE, (center-3, 2, 6, 10))
        # Глаза
        pygame.draw.circle(self.image, BLACK, (center-5, center-5), 2)
        pygame.draw.circle(self.image, BLACK, (center+5, center-5), 2)
        # Двигатели
        if self.speed_boost:
            pygame.draw.rect(self.image, YELLOW, (10, self.size-5, 5, 5))
            pygame.draw.rect(self.image, YELLOW, (self.size-15, self.size-5, 5, 5))
    
    def update(self):
        # Движение
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += self.speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += self.speed
        
        # Диагональное движение с нормализацией
        if dx != 0 and dy != 0:
            dx *= 0.7071  # 1/√2
            dy *= 0.7071
        
        self.rect.x = max(0, min(self.rect.x + dx, SCREEN_WIDTH - self.size))
        self.rect.y = max(0, min(self.rect.y + dy, SCREEN_HEIGHT - self.size))
        
        # Обновление таймеров
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False
        
        if self.frozen_enemies:
            self.freeze_timer -= 1
            if self.freeze_timer <= 0:
                self.frozen_enemies = False
        
        if self.speed_boost:
            self.speed_boost_timer -= 1
            if self.speed_boost_timer <= 0:
                self.speed_boost = False
                self.speed = self.base_speed
        
        # След (trail)
        self.trail.append((self.rect.centerx, self.rect.centery))
        if len(self.trail) > 10:
            self.trail.pop(0)
        
        # Частицы
        if random.random() < 0.2:
            self.particles.append(Particle(
                self.rect.centerx, self.rect.centery + self.size//2,
                CYAN, (random.uniform(-1, 1), random.uniform(1, 3)), 15
            ))
        
        self.particles = [p for p in self.particles if p.update()]
    
    def shoot(self):
        """Стрельба с учётом типа оружия"""
        if self.shoot_cooldown > 0:
            return []
        
        bullets = []
        self.shoot_cooldown = self.shoot_delay
        
        if self.weapon_type == "normal":
            bullets.append(Bullet(self.rect.centerx, self.rect.top, self))
        
        elif self.weapon_type == "double":
            bullets.append(Bullet(self.rect.centerx - 10, self.rect.top, self))
            bullets.append(Bullet(self.rect.centerx + 10, self.rect.top, self))
        
        elif self.weapon_type == "triple":
            bullets.append(Bullet(self.rect.centerx, self.rect.top, self))
            bullets.append(Bullet(self.rect.centerx - 15, self.rect.top - 5, self))
            bullets.append(Bullet(self.rect.centerx + 15, self.rect.top - 5, self))
        
        elif self.weapon_type == "spread":
            for angle in [-30, -15, 0, 15, 30]:
                bullets.append(Bullet(self.rect.centerx, self.rect.top, self, angle))
        
        elif self.weapon_type == "laser":
            bullets.append(LaserBeam(self.rect.centerx, self.rect.top, self))
        
        elif self.weapon_type == "homing":
            bullets.append(HomingBullet(self.rect.centerx, self.rect.top, self))
        
        return bullets
    
    def hit(self, damage=1):
        """Получение урона"""
        if self.invincible:
            return False
        
        if self.shield > 0:
            self.shield -= 1
            return False
        
        self.health -= damage
        self.invincible = True
        self.invincible_timer = 90
        
        # Создание частиц при попадании
        for _ in range(20):
            self.particles.append(Particle(
                self.rect.centerx, self.rect.centery,
                RED, (random.uniform(-3, 3), random.uniform(-3, 3)), 30
            ))
        
        return self.health <= 0
    
    def add_powerup(self, powerup_type):
        """Применение усиления"""
        if powerup_type == PowerUpType.HEALTH:
            self.health = min(self.health + 2, self.max_health)
        elif powerup_type == PowerUpType.SHIELD:
            self.shield += 2
        elif powerup_type == PowerUpType.DOUBLE_SHOT:
            self.weapon_type = "double"
        elif powerup_type == PowerUpType.TRIPLE_SHOT:
            self.weapon_type = "triple"
        elif powerup_type == PowerUpType.SPREAD_SHOT:
            self.weapon_type = "spread"
        elif powerup_type == PowerUpType.LASER:
            self.weapon_type = "laser"
        elif powerup_type == PowerUpType.HOMING:
            self.weapon_type = "homing"
        elif powerup_type == PowerUpType.SPEED_BOOST:
            self.speed_boost = True
            self.speed_boost_timer = 300
            self.speed = self.base_speed * 2
        elif powerup_type == PowerUpType.INVINCIBILITY:
            self.invincible = True
            self.invincible_timer = 300
        elif powerup_type == PowerUpType.NUKE:
            return "nuke"  # специальный сигнал
        elif powerup_type == PowerUpType.EXTRA_LIFE:
            self.max_health += 1
            self.health = self.max_health
        elif powerup_type == PowerUpType.MONEY:
            self.money += 100
        elif powerup_type == PowerUpType.FREEZE:
            self.frozen_enemies = True
            self.freeze_timer = 180
        elif powerup_type == PowerUpType.PIERCE:
            self.pierce = True
        
        return None
    
    def add_exp(self, amount):
        """Добавление опыта и повышение уровня"""
        self.exp += amount
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level += 1
            self.exp_to_next = int(self.exp_to_next * 1.5)
            return True
        return False

# Улучшенный класс пули
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, player, angle=0):
        super().__init__()
        self.player = player
        self.size = 8
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        self.angle = angle
        self.speed = 10
        self.damage = 1
        self.pierce = player.pierce
        self.hits = []
        
        # Вектор движения
        rad = math.radians(angle)
        self.vx = math.sin(rad) * self.speed * 0.5
        self.vy = -math.cos(rad) * self.speed
    
    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()

# Класс для самонаводящейся пули
class HomingBullet(Bullet):
    def __init__(self, x, y, player):
        super().__init__(x, y, player)
        self.image.fill(GREEN)
        self.target = None
        self.homing_strength = 0.1
    
    def update(self, enemies):
        # Поиск ближайшего врага
        if not self.target or self.target not in enemies:
            closest_dist = float('inf')
            for enemy in enemies:
                dist = math.hypot(self.rect.centerx - enemy.rect.centerx,
                                 self.rect.centery - enemy.rect.centery)
                if dist < closest_dist:
                    closest_dist = dist
                    self.target = enemy
        
        # Наведение на цель
        if self.target:
            dx = self.target.rect.centerx - self.rect.centerx
            dy = self.target.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.vx += (dx / dist) * self.homing_strength
                self.vy += (dy / dist) * self.homing_strength
                
                # Нормализация скорости
                speed = math.hypot(self.vx, self.vy)
                if speed > self.speed:
                    self.vx = (self.vx / speed) * self.speed
                    self.vy = (self.vy / speed) * self.speed
        
        super().update()

# Класс для лазера
class LaserBeam(pygame.sprite.Sprite):
    def __init__(self, x, y, player):
        super().__init__()
        self.player = player
        self.image = pygame.Surface((5, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y - 15)
        self.lifetime = 5
        self.damage = 3
    
    def update(self):
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()

# Класс для босса (особый враг)
class Boss(Enemy):
    def __init__(self):
        super().__init__(EnemyType.BOSS)
        self.size = 150
        self.health = 200
        self.max_health = 200
        self.phase = 1  # фазы боя
        self.attack_pattern = 0
        self.attack_timer = 0
        self.minions = []
        
        # Создание изображения босса
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.draw_boss()
    
    def draw_boss(self):
        """Отрисовка босса"""
        # Основной корпус
        pygame.draw.rect(self.image, PURPLE, (0, 0, self.size, self.size))
        pygame.draw.rect(self.image, GOLD, (5, 5, self.size-10, self.size-10), 3)
        
        # Пушки
        for i in range(4):
            x = 20 + i * 35
            pygame.draw.rect(self.image, RED, (x, 10, 15, 30))
        
        # Глаза
        pygame.draw.circle(self.image, RED, (self.size//3, self.size//3), 10)
        pygame.draw.circle(self.image, RED, (2*self.size//3, self.size//3), 10)
        pygame.draw.circle(self.image, BLACK, (self.size//3-3, self.size//3-3), 5)
        pygame.draw.circle(self.image, BLACK, (2*self.size//3-3, self.size//3-3), 5)
        
        # Индикатор здоровья
        health_width = self.size - 20
        health_height = 10
        health_x = 10
        health_y = self.size - 20
        health_percent = self.health / self.max_health
        pygame.draw.rect(self.image, GRAY, (health_x, health_y, health_width, health_height))
        pygame.draw.rect(self.image, GREEN, (health_x, health_y, int(health_width * health_percent), health_height))
    
    def update(self, player, enemies, bullets):
        super().update(player, enemies, bullets)
        
        # Изменение фазы при потере здоровья
        if self.health < self.max_health * 0.5 and self.phase == 1:
            self.phase = 2
            self.speed *= 1.5
            self.color = DARK_RED
        
        if self.health < self.max_health * 0.25 and self.phase == 2:
            self.phase = 3
            self.shoot_cooldown = 30
        
        # Атаки босса
        self.attack_timer += 1
        if self.attack_timer >= 60:  # Каждую секунду
            self.attack_timer = 0
            self.attack_pattern = (self.attack_pattern + 1) % 4
            
            if self.attack_pattern == 0:
                # Круговая атака
                for angle in range(0, 360, 30):
                    bullet = EnemyBullet(self.rect.centerx, self.rect.centery, 
                                       (self.rect.centerx + math.cos(math.radians(angle)) * 100,
                                        self.rect.centery + math.sin(math.radians(angle)) * 100))
                    bullets.add(bullet)
            
            elif self.attack_pattern == 1 and self.phase >= 2:
                # Атака миньонами
                for _ in range(3):
                    enemy = Enemy(EnemyType.FAST, (self.rect.centerx, self.rect.centery))
                    enemies.add(enemy)
                    self.minions.append(enemy)
            
            elif self.attack_pattern == 2:
                # Лазерная атака
                for i in range(5):
                    x = self.rect.centerx - 50 + i * 25
                    bullet = EnemyBullet(x, self.rect.bottom, player.rect.center)
                    bullets.add(bullet)
            
            elif self.attack_pattern == 3 and self.phase >= 3:
                # Ядерная атака
                for _ in range(12):
                    angle = random.randint(0, 360)
                    bullet = EnemyBullet(self.rect.centerx, self.rect.centery,
                                       (self.rect.centerx + math.cos(math.radians(angle)) * 200,
                                        self.rect.centery + math.sin(math.radians(angle)) * 200))
                    bullets.add(bullet)
    
    def show_gameover(screen, player):
        """Отображение экрана окончания игры"""
        font_large = pygame.font.Font(None, 72)
        font_small = pygame.font.Font(None, 36)
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        game_over_text = font_large.render("GAME OVER", True, RED)
        score_text = font_small.render(f"Score: {player.score}", True, WHITE)
        restart_text = font_small.render("Press SPACE to restart or ESC to quit", True, WHITE)
        
        screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 100))
        screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, SCREEN_HEIGHT//2))
        screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 50))
        
        pygame.display.flip()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False
                    elif event.key == pygame.K_SPACE:
                        return True
    def game():
    """Основная игровая функция"""
    # Создание игровых объектов
    player = Player()
    all_sprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    
    all_sprites.add(player)
    
    # Игровые переменные
    score = 0
    wave = 1
    enemy_spawn_timer = 0
    boss_spawned = False
    
    running = True
    while running:
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    new_bullets = player.shoot()
                    for bullet in new_bullets:
                        all_sprites.add(bullet)
                        bullets.add(bullet)
        
        # Обновление игрока
        player.update()

        # Спавн врагов
        enemy_spawn_timer += 1
        if enemy_spawn_timer >= 120:  # Каждые 2 секунды
            enemy_spawn_timer = 0
            if len(enemies) < 8:
                enemy_type = random.choice([EnemyType.CHASER, EnemyType.SHOOTER, EnemyType.TELEPORTER])
                enemy = Enemy(enemy_type)
                enemy.spawn_outside()
                enemies.add(enemy)
                all_sprites.add(enemy)
        
        # Спавн босса
        if score > wave * 500 and not boss_spawned:
            boss = Boss()
            enemies.add(boss)
            all_sprites.add(boss)
            boss_spawned = True
        
        # Обновление врагов
        for enemy in enemies:
            enemy.update(player, enemies, enemy_bullets)
            
            # Враги стреляют
            if hasattr(enemy, 'type') and enemy.type == EnemyType.SHOOTER and random.random() < 0.02:
                bullet = EnemyBullet(enemy.rect.centerx, enemy.rect.centery, player.rect.center)
                enemy_bullets.add(bullet)
                all_sprites.add(bullet)
                
                # Обновление пуль
        for bullet in bullets:
            bullet.update()
            if bullet.rect.bottom < 0:
                bullet.kill()
        
        for bullet in enemy_bullets:
            bullet.update()
            if (bullet.rect.right < 0 or bullet.rect.left > SCREEN_WIDTH or
                bullet.rect.bottom < 0 or bullet.rect.top > SCREEN_HEIGHT):
                bullet.kill()
        
        # Проверка столкновений
        # Пули игрока с врагами
        for bullet in bullets:
            hit_enemies = pygame.sprite.spritecollide(bullet, enemies, False)
            for enemy in hit_enemies:
                if enemy.hit():
                    score += enemy.points
                    enemy.kill()
                    # Шанс выпадения усиления
                    if random.random() < 0.1:
                        powerup = PowerUp(enemy.rect.centerx, enemy.rect.centery)
                        powerups.add(powerup)
                        all_sprites.add(powerup)
                bullet.kill()

                # Вражеские пули с игроком
        hit_player = pygame.sprite.spritecollide(player, enemy_bullets, True)
        if hit_player:
            if player.hit():
                # Обновление рекорда перед выходом
                if score > HIGH_SCORE:
                    HIGH_SCORE = score
                    save_high_score(HIGH_SCORE)
                return show_gameover(screen, player)
        
        # Враги с игроком
        hit_enemies = pygame.sprite.spritecollide(player, enemies, False)
        if hit_enemies:
            if player.hit():
                # Обновление рекорда перед выходом
                if score > HIGH_SCORE:
                    HIGH_SCORE = score
                    save_high_score(HIGH_SCORE)
                return show_gameover(screen, player)
        
        # Усиления с игроком
        collected_powerups = pygame.sprite.spritecollide(player, powerups, True)
        for powerup in collected_powerups:
            player.add_powerup(powerup.type)
        
        # Отрисовка
        screen.fill(BLACK)
