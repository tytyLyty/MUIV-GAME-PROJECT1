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

# Класс для волн врагов
class WaveManager:
    def __init__(self):
        self.wave = 0
        self.enemies_in_wave = 0
        self.enemies_spawned = 0
        self.wave_active = False
        self.spawn_timer = 0
        self.wave_composition = []
        self.boss_wave = False
        
    def start_next_wave(self):
        """Начало новой волны"""
        self.wave += 1
        self.enemies_spawned = 0
        self.wave_active = True
        self.boss_wave = (self.wave % 5 == 0)  # Каждая 5-я волна - босс
        
        # Определение состава волны
        if self.boss_wave:
            self.enemies_in_wave = 1
            self.wave_composition = [EnemyType.BOSS]
        else:
            base_count = 5 + self.wave * 2
            self.enemies_in_wave = min(base_count, 30)
            self.wave_composition = self.generate_composition()
    
    def generate_composition(self):
        """Генерация состава волны"""
        composition = []
        available_types = [t for t in EnemyType if t != EnemyType.BOSS]
        
        for _ in range(self.enemies_in_wave):
            # Чем выше волна, тем больше шанс сложных врагов
            if self.wave > 10 and random.random() < 0.3:
                enemy_type = random.choice([EnemyType.TANK, EnemyType.SHIELDED, EnemyType.TELEPORTER])
            elif self.wave > 5 and random.random() < 0.5:
                enemy_type = random.choice([EnemyType.SHOOTER, EnemyType.SPLITTER, EnemyType.BOMBER])
            else:
                enemy_type = random.choice([EnemyType.CHASER, EnemyType.FAST, EnemyType.SWARM])
            
            composition.append(enemy_type)
        
        return composition
    
    def update(self, current_enemies):
        """Обновление менеджера волн"""
        if not self.wave_active:
            return None
        
        if self.enemies_spawned < self.enemies_in_wave:
            self.spawn_timer += 1
            if self.spawn_timer >= max(10, 30 - self.wave):
                self.spawn_timer = 0
                self.enemies_spawned += 1
                
                if self.boss_wave:
                    return Boss()
                else:
                    enemy_type = self.wave_composition[self.enemies_spawned - 1]
                    return Enemy(enemy_type)
        
        # Проверка завершения волны
        if len(current_enemies) == 0 and self.enemies_spawned >= self.enemies_in_wave:
            self.wave_active = False
            return "wave_complete"
        
        return None

# Класс для магазина улучшений
class Shop:
    def __init__(self):
        self.items = [
            {"name": "+Здоровье", "cost": 50, "effect": "health"},
            {"name": "+Скорость", "cost": 75, "effect": "speed"},
            {"name": "Двойной выстрел", "cost": 100, "effect": "double"},
            {"name": "Тройной выстрел", "cost": 150, "effect": "triple"},
            {"name": "Щит", "cost": 80, "effect": "shield"},
            {"name": "Самонаведение", "cost": 200, "effect": "homing"},
            {"name": "Лазер", "cost": 250, "effect": "laser"},
            {"name": "Пробивание", "cost": 120, "effect": "pierce"},
        ]
        self.selected = 0
    
    def draw(self, screen, player):
        """Отрисовка магазина"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        # Заголовок
        font_big = pygame.font.Font(None, 72)
        text = font_big.render("МАГАЗИН", True, GOLD)
        screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 50))
        
        # Информация о деньгах
        font = pygame.font.Font(None, 36)
        money_text = font.render(f"Монеты: {player.money}", True, GOLD)
        screen.blit(money_text, (50, 150))
        
        # Список товаров
        y = 220
        for i, item in enumerate(self.items):
            color = YELLOW if i == self.selected else WHITE
            can_afford = player.money >= item["cost"]
            if not can_afford:
                color = GRAY
            
            text = font.render(f"{item['name']} - {item['cost']} монет", True, color)
            screen.blit(text, (100, y + i * 40))
        
        # Инструкции
        inst_font = pygame.font.Font(None, 24)
        inst_text = inst_font.render("Стрелки вверх/вниз - выбор, Пробел - купить, ESC - выйти", True, WHITE)
        screen.blit(inst_text, (SCREEN_WIDTH//2 - inst_text.get_width()//2, SCREEN_HEIGHT - 50))
        
        pygame.display.flip()
    
    def handle_input(self, player):
        """Обработка ввода в магазине"""
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_UP]:
            self.selected = (self.selected - 1) % len(self.items)
            pygame.time.wait(150)
        if keys[pygame.K_DOWN]:
            self.selected = (self.selected + 1) % len(self.items)
            pygame.time.wait(150)
        if keys[pygame.K_SPACE]:
            item = self.items[self.selected]
            if player.money >= item["cost"]:
                player.money -= item["cost"]
                self.apply_effect(player, item["effect"])
                return True
        if keys[pygame.K_ESCAPE]:
            return "exit"
        
        return None
    
    def apply_effect(self, player, effect):
        """Применение эффекта покупки"""
        if effect == "health":
            player.max_health += 1
            player.health = player.max_health
        elif effect == "speed":
            player.base_speed += 1
            player.speed = player.base_speed
        elif effect == "double":
            player.weapon_type = "double"
        elif effect == "triple":
            player.weapon_type = "triple"
        elif effect == "shield":
            player.shield += 2
        elif effect == "homing":
            player.weapon_type = "homing"
        elif effect == "laser":
            player.weapon_type = "laser"
        elif effect == "pierce":
            player.pierce = True

# Функции для отрисовки интерфейса
def draw_ui(screen, player, wave_manager):
    """Отрисовка интерфейса"""
    # Здоровье
    for i in range(player.max_health):
        x = 20 + i * 30
        y = 20
        if i < player.health:
            pygame.draw.rect(screen, GREEN, (x, y, 25, 25))
        else:
            pygame.draw.rect(screen, RED, (x, y, 25, 25), 2)
    
    # Щит
    for i in range(player.shield):
        x = 20 + i * 30
        y = 50
        pygame.draw.circle(screen, CYAN, (x + 12, y + 12), 12, 2)
    
    # Очки и монеты
    font = pygame.font.Font(None, 30)
    score_text = font.render(f"Очки: {player.score}", True, WHITE)
    screen.blit(score_text, (SCREEN_WIDTH - 200, 20))
    
    money_text = font.render(f"Монеты: {player.money}", True, GOLD)
    screen.blit(money_text, (SCREEN_WIDTH - 200, 50))
    
    # Уровень и опыт
    level_text = font.render(f"Уровень: {player.level}", True, CYAN)
    screen.blit(level_text, (SCREEN_WIDTH - 200, 80))
    
    exp_percent = player.exp / player.exp_to_next
    pygame.draw.rect(screen, GRAY, (SCREEN_WIDTH - 200, 110, 150, 15))
    pygame.draw.rect(screen, CYAN, (SCREEN_WIDTH - 200, 110, int(150 * exp_percent), 15))
    
    # Волна
    wave_text = font.render(f"Волна: {wave_manager.wave}", True, MAGENTA)
    screen.blit(wave_text, (SCREEN_WIDTH//2 - 50, 20))
    
    if wave_manager.wave_active:
        enemies_left = wave_manager.enemies_in_wave - len(pygame.sprite.Group())
        enemies_text = font.render(f"Врагов: {enemies_left}", True, RED)
        screen.blit(enemies_text, (SCREEN_WIDTH//2 - 50, 50))
    
    # Активные бонусы
    y = SCREEN_HEIGHT - 100
    if player.speed_boost:
        pygame.draw.rect(screen, BLUE, (SCREEN_WIDTH - 150, y, 30, 30))
    if player.invincible:
        pygame.draw.rect(screen, WHITE, (SCREEN_WIDTH - 110, y, 30, 30))
    if player.frozen_enemies:
        pygame.draw.rect(screen, LIGHT_BLUE, (SCREEN_WIDTH - 70, y, 30, 30))

def draw_particles(screen, particles):
    """Отрисовка всех частиц"""
    for particle in particles:
        particle.draw(screen)

def show_menu(screen):
    """Улучшенное меню"""
    screen.fill(BLACK)
    
    # Анимированный фон
    stars = []
    for _ in range(100):
        stars.append([random.randint(0, SCREEN_WIDTH), 
                     random.randint(0, SCREEN_HEIGHT),
                     random.randint(1, 3)])
    
    # Заголовок
    font_big = pygame.font.Font(None, 100)
    title = font_big.render("HeAVeYDr1v3r", True, CYAN)
    title_shadow = font_big.render("HeAVeYDr1v3r", True, BLUE)
    
    screen.blit(title_shadow, (SCREEN_WIDTH//2 - title.get_width()//2 + 5, 205))
    screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 200))
    
    # Опции меню
    font = pygame.font.Font(None, 50)
    start_text = font.render("Начать игру", True, GREEN)
    quit_text = font.render("Выход", True, RED)
    
    screen.blit(start_text, (SCREEN_WIDTH//2 - start_text.get_width()//2, 350))
    screen.blit(quit_text, (SCREEN_WIDTH//2 - quit_text.get_width()//2, 420))
    
    # Управление
    small_font = pygame.font.Font(None, 30)
    controls = [
        "Управление: WASD / Стрелки",
        "Стрельба: Пробел",
        "Пауза: P",
        "Магазин: M (между волнами)",
        "Уничтожайте врагов, собирайте усиления!"
    ]
    
    y = 500
    for control in controls:
        text = small_font.render(control, True, WHITE)
        screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, y))
        y += 35
    
    pygame.display.flip()
    
    # Ожидание выбора
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return True
                if event.key == pygame.K_ESCAPE:
                    return False
        
        # Анимация звёзд
        screen.fill(BLACK, (0, 0, SCREEN_WIDTH, 150))
        screen.fill(BLACK, (0, 450, SCREEN_WIDTH, 150))
        
        for star in stars:
            star[1] += star[2]
            if star[1] > SCREEN_HEIGHT:
                star[1] = 0
                star[0] = random.randint(0, SCREEN_WIDTH)
            pygame.draw.circle(screen, WHITE, (star[0], star[1]), star[2])
        
        pygame.display.flip()
        clock.tick(FPS)
    
    return True

def show_pause(screen):
    """Экран паузы"""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(150)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    
    font = pygame.font.Font(None, 72)
    text = font.render("ПАУЗА", True, WHITE)
    screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2 - 50))
    
    small_font = pygame.font.Font(None, 36)
    continue_text = small_font.render("Нажмите P для продолжения", True, WHITE)
    screen.blit(continue_text, (SCREEN_WIDTH//2 - continue_text.get_width()//2, SCREEN_HEIGHT//2 + 20))
    
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    waiting = False
                if event.key == pygame.K_ESCAPE:
                    return False
        clock.tick(FPS)
    
    return True

def show_gameover(screen, player):
    """Улучшенный экран Game Over"""
    screen.fill(BLACK)
    
    font_big = pygame.font.Font(None, 100)
    gameover = font_big.render("GAME OVER", True, RED)
    screen.blit(gameover, (SCREEN_WIDTH//2 - gameover.get_width()//2, 200))
    
    font = pygame.font.Font(None, 50)
    stats = [
        f"Счёт: {player.score}",
        f"Монеты: {player.money}",
        f"Уровень: {player.level}",
        f"Волна: {wave_manager.wave}"
    ]
    
    y = 300
    for stat in stats:
        text = font.render(stat, True, WHITE)
        screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, y))
        y += 50
    
    small_font = pygame.font.Font(None, 36)
    restart_text = small_font.render("Нажмите R для рестарта или ESC для выхода", True, WHITE)
    screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, 500))
    
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
                if event.key == pygame.K_ESCAPE:
                    return False
        clock.tick(FPS)
    
    return False

# Основная игровая функция
def game():
    global clock, wave_manager
    
    # Создание групп спрайтов
    all_sprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    
    # Создание игрока
    player = Player()
    all_sprites.add(player)
    
    # Создание менеджера волн
    wave_manager = WaveManager()
    wave_manager.start_next_wave()
    
    # Список частиц
    particles = []
    
    # Магазин
    shop = Shop()
    in_shop = False
    
    # Переменные игры
    game_over = False
    paused = False
    nuke_active = False
    nuke_timer = 0
    
    # Основной игровой цикл
    while not game_over:
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_p:
                    paused = not paused
                    if paused:
                        if not show_pause(screen):
                            return False
                        paused = False
                if event.key == pygame.K_m and not wave_manager.wave_active:
                    in_shop = not in_shop
                if event.key == pygame.K_SPACE and not paused and not in_shop:
                    new_bullets = player.shoot()
                    for bullet in new_bullets:
                        all_sprites.add(bullet)
                        bullets.add(bullet)
        
        if paused or in_shop:
            if in_shop:
                result = shop.handle_input(player)
                if result == "exit":
                    in_shop = False
                shop.draw(screen, player)
            pygame.display.flip()
            clock.tick(FPS)
            continue
        
        # Обновление
        all_sprites.update()
        
        # Обновление врагов с передачей дополнительных параметров
        for enemy in enemies:
            enemy.update(player, enemies, enemy_bullets)
        
        # Обновление пуль врага
        enemy_bullets.update()
        
        # Обновление усилений
        powerups.update()
        
        # Обновление менеджера волн
        result = wave_manager.update(enemies)
        if isinstance(result, Enemy):
            enemies.add(result)
            all_sprites.add(result)
        elif result == "wave_complete":
            player.money += 50 * wave_manager.wave  # Бонус за волну
            
        # Проверка столкновений пуль с врагами
        hits = pygame.sprite.groupcollide(enemies, bullets, False, not player.pierce)
        for enemy, bullet_list in hits.items():
            for bullet in bullet_list:
                if enemy.hit(bullet.damage):
                    # Враг уничтожен
                    player.score += enemy.points
                    player.money += enemy.points // 2
                    
                    # Шанс выпадения усиления
                    if random.random() < 0.1:
                        powerup = PowerUp(enemy.rect.centerx, enemy.rect.centery)
                        powerups.add(powerup)
                        all_sprites.add(powerup)
                    
                    # Создание взрыва
                    for _ in range(20):
                        particles.append(Particle(
                            enemy.rect.centerx, enemy.rect.centery,
                            enemy.color, (random.uniform(-3, 3), random.uniform(-3, 3)), 30
                        ))
                    
                    enemy.kill()
                    
                    # Опыт
                    if player.add_exp(enemy.points):
                        # Повышение уровня
                        player.health = min(player.health + 1, player.max_health)
        
        # Проверка столкновений пуль врага с игроком
        hits = pygame.sprite.spritecollide(player, enemy_bullets, True)
        if hits:
            player.hit()
            if player.health <= 0:
                game_over = True
        
        # Проверка столкновений игрока с врагами
        if not player.invincible:
            hits = pygame.sprite.spritecollide(player, enemies, False)
            if hits:
                player.hit()
                if player.health <= 0:
                    game_over = True
        
        # Проверка столкновений игрока с усилениями
        hits = pygame.sprite.spritecollide(player, powerups, True)
        for powerup in hits:
            result = player.add_powerup(powerup.type)
            if result == "nuke":
                nuke_active = True
                nuke_timer = 10
    
    # Game Over
    return show_gameover(screen, player)

# Запуск игры
if __name__ == "__main__":
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("HeAVeYDr1v3r — Мега-версия")
    clock = pygame.time.Clock()
    
    while True:
        if not show_menu(screen):
            break
        
        if not game():
            break
    
    pygame.quit()
    sys.exit()
