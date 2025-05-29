# استيراد المكتبات الضرورية
import pygame
import sys
import random
import math
import os
from typing import List, Tuple
import arabic_reshaper
from bidi.algorithm import get_display
from abc import ABC, abstractmethod
import time
import colorsys
import heapq  # إضافة مكتبة للمساعدة في خوارزمية البحث

# تهيئة مكتبة pygame
pygame.init()

# === فئة الألوان والمظهر ===
class Theme:
    """فئة لإدارة الألوان والمظهر"""
    COLORS = {
        'background': (15, 23, 42),     # خلفية داكنة
        'primary': (56, 189, 248),      # أزرق فاتح
        'secondary': (168, 85, 247),    # بنفسجي
        'success': (34, 197, 94),       # أخضر
        'danger': (239, 68, 68),        # أحمر
        'warning': (245, 158, 11),      # برتقالي
        'text': (248, 250, 252),        # نص فاتح
        'grid': (71, 85, 105),          # شبكة
        'wall': (30, 41, 59),           # جدران
        'coin': (250, 204, 21),         # ذهبي
        'panel': (51, 65, 85, 230)      # لوحة شفافة
    }

    @staticmethod
    def get_gradient_color(progress: float, start_color: tuple, end_color: tuple) -> tuple:
        """إنشاء لون متدرج"""
        return tuple(int(start + (end - start) * progress) for start, end in zip(start_color, end_color))

    @staticmethod
    def create_neon_surface(width: int, height: int, color: tuple, radius: int = 20) -> pygame.Surface:
        """إنشاء سطح بتأثير نيون"""
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        center = (width // 2, height // 2)
        
        for i in range(radius, 0, -1):
            alpha = int(255 * (1 - i / radius))
            current_color = (*color, alpha)
            pygame.draw.circle(surface, current_color, center, i)
        
        return surface

# === فئة الخلفية المتحركة ===
class AnimatedBackground:
    """فئة لإدارة الخلفية المتحركة"""
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.particles = []
        self.create_particles()
        self.last_update = time.time()

    def create_particles(self):
        """إنشاء جزيئات الخلفية"""
        for _ in range(50):
            self.particles.append({
                'pos': [random.randint(0, self.width), random.randint(0, self.height)],
                'vel': [random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)],
                'size': random.randint(2, 4),
                'color': Theme.COLORS['primary'],
                'alpha': random.randint(50, 150)
            })

    def update(self, width: int, height: int):
        """تحديث حركة الجزيئات"""
        current_time = time.time()
        delta_time = (current_time - self.last_update) * 60
        self.last_update = current_time
        self.width = width
        self.height = height

        for p in self.particles:
            p['pos'][0] += p['vel'][0] * delta_time
            p['pos'][1] += p['vel'][1] * delta_time

            if p['pos'][0] < 0 or p['pos'][0] > self.width:
                p['vel'][0] *= -1
            if p['pos'][1] < 0 or p['pos'][1] > self.height:
                p['vel'][1] *= -1

    def draw(self, screen: pygame.Surface):
        """رسم الخلفية المتحركة"""
        for p in self.particles:
            pygame.draw.circle(screen, (*p['color'], p['alpha']), 
                             (int(p['pos'][0]), int(p['pos'][1])), p['size'])

# === فئة واجهة المستخدم ===
class UI:
    """فئة لإدارة واجهة المستخدم"""
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.top_bar = pygame.Surface((width, 60), pygame.SRCALPHA)
        self.side_bar = pygame.Surface((300, height - 60), pygame.SRCALPHA)
        self.update_surfaces()

    def update_surfaces(self):
        """تحديث أسطح واجهة المستخدم"""
        # تحديث الشريط العلوي
        self.top_bar.fill(Theme.COLORS['panel'])
        pygame.draw.line(self.top_bar, Theme.COLORS['primary'], 
                        (0, 59), (self.width, 59), 2)

        # تحديث الشريط الجانبي
        self.side_bar.fill(Theme.COLORS['panel'])
        pygame.draw.line(self.side_bar, Theme.COLORS['primary'], 
                        (0, 0), (0, self.height), 2)

    def draw(self, screen: pygame.Surface):
        """رسم واجهة المستخدم"""
        screen.blit(self.top_bar, (0, 0))
        screen.blit(self.side_bar, (self.width - 300, 60))

# === فئة معالجة النصوص ===
class TextRenderer:
    """فئة لمعالجة وعرض النصوص"""
    _font_cache = {}  # تخزين مؤقت للخطوط

    @staticmethod
    def load_font(size: int) -> pygame.font.Font:
        """تحميل الخط المناسب"""
        if size in TextRenderer._font_cache:
            return TextRenderer._font_cache[size]

        # قائمة مسارات الخطوط العربية في ويندوز
        arabic_font_paths = [
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\tahoma.ttf",
            "C:\\Windows\\Fonts\\segoeui.ttf",
            "C:\\Windows\\Fonts\\calibri.ttf",
        ]

        # محاولة تحميل خط عربي
        for font_path in arabic_font_paths:
            try:
                font = pygame.font.Font(font_path, size)
                TextRenderer._font_cache[size] = font
                return font
            except:
                continue

        # إذا فشل تحميل الخطوط العربية، نستخدم الخط الافتراضي
        try:
            font = pygame.font.SysFont("arial", size)
            TextRenderer._font_cache[size] = font
            return font
        except:
            # آخر محاولة: استخدام الخط الافتراضي للنظام
            font = pygame.font.Font(None, size)
            TextRenderer._font_cache[size] = font
            return font

    @staticmethod
    def render_text(text: str, font: pygame.font.Font, color: tuple, is_arabic: bool = False) -> pygame.Surface:
        """معالجة وعرض النص"""
        try:
            if is_arabic:
                # معالجة النص العربي
                reshaped_text = arabic_reshaper.reshape(text)
                bidi_text = get_display(reshaped_text)
                return font.render(bidi_text, True, color)
            return font.render(text, True, color)
        except:
            # في حالة فشل معالجة النص العربي
            return font.render(text, True, color)

# === الترجمات ===
TRANSLATIONS = {
    "ar": {
        "game_title": "لعبة المتاهة الذكية",
        "score": "النقاط: {}",
        "level": "المستوى: {}",
        "time": "الوقت: {}",
        "pause": "إيقاف مؤقت",
        "resume": "استمرار",
        "restart": "إعادة المستوى",
        "language": "English",
        "auto_move_start": "تشغيل الحركة التلقائية",
        "auto_move_stop": "إيقاف الحركة التلقائية"
    },
    "en": {
        "game_title": "Smart Maze Game",
        "score": "Score: {}",
        "level": "Level: {}",
        "time": "Time: {}",
        "pause": "Pause",
        "resume": "Resume",
        "restart": "Restart Level",
        "language": "عربي",
        "auto_move_start": "Start Auto Move",
        "auto_move_stop": "Stop Auto Move"
    }
}

# === فئة العدو ===
class Enemy:
    """فئة لإدارة الأعداء في اللعبة"""
    def __init__(self, pos: List[int]):
        self.pos = list(pos)
        self.original_pos = list(pos)
        self.glow_offset = 0
        self.glow_direction = 1
        self.move_counter = 0
        self.safe_zone_radius = 2  # تقليل نصف قطر المنطقة الآمنة
        self.random_direction = self.get_random_direction()
        self.direction_change_counter = 0
        self.max_direction_steps = random.randint(3, 6)  # عدد خطوات عشوائي قبل تغيير الاتجاه

    def get_random_direction(self) -> List[int]:
        """الحصول على اتجاه عشوائي"""
        directions = [[1, 0], [-1, 0], [0, 1], [0, -1]]
        return random.choice(directions)

    def is_safe_distance(self, pos: List[int], player_pos: List[int]) -> bool:
        """التحقق من المسافة الآمنة من اللاعب"""
        distance = math.sqrt(
            (pos[0] - player_pos[0])**2 +
            (pos[1] - player_pos[1])**2
        )
        return distance >= self.safe_zone_radius

    def is_valid_move(self, new_pos: List[int], grid: List[List[int]], player_pos: List[int], goal_pos: tuple) -> bool:
        """التحقق من صحة الحركة"""
        # التحقق من حدود المتاهة والجدران
        if (new_pos[0] < 0 or new_pos[0] >= len(grid) or
            new_pos[1] < 0 or new_pos[1] >= len(grid[0]) or
            grid[new_pos[0]][new_pos[1]] == 1):
            return False

        # التحقق من عدم سد المسار بين اللاعب والهدف
        x1, y1 = player_pos
        x2, y2 = goal_pos
        x3, y3 = new_pos
        
        # حساب المسافة من الخط المستقيم
        numerator = abs((y2-y1)*x3 - (x2-x1)*y3 + x2*y1 - y2*x1)
        denominator = math.sqrt((y2-y1)**2 + (x2-x1)**2)
        if denominator == 0:
            return True
            
        distance_to_path = numerator / denominator
        return distance_to_path >= 2  # مسافة آمنة من المسار

    def update(self, grid: List[List[int]], player_pos: List[int], goal_pos: tuple):
        """تحديث حركة العدو"""
        # تحديث تأثير التوهج
        self.glow_offset += 0.1 * self.glow_direction
        if self.glow_offset >= 1:
            self.glow_direction = -1
        elif self.glow_offset <= 0:
            self.glow_direction = 1

        # تحديث الحركة
        self.move_counter += 1
        if self.move_counter >= 20:  # تحديث أسرع للحركة
            self.move_counter = 0
            
            # تغيير الاتجاه بعد عدد معين من الخطوات
            self.direction_change_counter += 1
            if self.direction_change_counter >= self.max_direction_steps:
                self.random_direction = self.get_random_direction()
                self.direction_change_counter = 0
                self.max_direction_steps = random.randint(3, 6)

            # محاولة التحرك في الاتجاه الحالي
            new_pos = [
                self.pos[0] + self.random_direction[0],
                self.pos[1] + self.random_direction[1]
            ]

            # التحقق من صحة الحركة
            if (self.is_valid_move(new_pos, grid, player_pos, goal_pos) and
                self.is_safe_distance(new_pos, player_pos)):
                self.pos = new_pos
            else:
                # إذا كانت الحركة غير صالحة، نغير الاتجاه
                self.random_direction = self.get_random_direction()

    def get_glow_color(self, base_color: tuple) -> tuple:
        """الحصول على لون التوهج"""
        glow_intensity = 0.5 + self.glow_offset * 0.5
        return tuple(int(c * glow_intensity) for c in base_color)

# === تعريف المستويات ===
LEVELS = [
    {   # المستوى الأول - سهل
        "grid": [
            [0,0,0,1,0,0,0,0],
            [1,1,0,1,0,1,0,0],
            [0,0,0,0,0,0,0,1],
            [0,1,1,0,1,1,0,0],
            [0,0,0,0,0,1,0,0],
            [1,1,0,1,0,0,0,1],
            [0,0,0,1,0,1,0,0],
            [0,1,0,0,0,0,0,0]
        ],
        "start": (0, 0),
        "goal": (7, 7),
        "enemies": [(3, 4), (5, 2)],  # تغيير مواقع الأعداء
        "coins": 5,
        "time_limit": 60
    },
    {   # المستوى الثاني - متوسط
        "grid": [
            [0,0,0,1,0,0,0,0,0,0],
            [1,1,0,1,0,1,1,1,0,0],
            [0,0,0,0,0,0,0,1,0,1],
            [0,1,1,0,1,1,0,0,0,0],
            [0,0,0,0,0,1,1,1,1,0],
            [1,1,0,1,0,0,0,1,0,0],
            [0,1,0,1,1,1,0,0,0,1],
            [0,1,0,0,0,0,0,1,0,0],
            [0,0,0,1,1,1,0,1,1,0],
            [1,1,0,0,0,0,0,0,0,0]
        ],
        "start": (0, 0),
        "goal": (9, 9),
        "enemies": [(2, 5), (4, 7), (7, 3)],  # تغيير مواقع الأعداء
        "coins": 8,
        "time_limit": 90
    },
    {   # المستوى الثالث - صعب
        "grid": [
            [0,0,0,1,0,0,0,0,0,0,0,0],
            [1,1,0,1,0,1,1,1,0,1,0,0],
            [0,0,0,0,0,0,0,1,0,1,0,1],
            [0,1,1,0,1,1,0,0,0,0,1,0],
            [0,0,0,0,0,1,1,1,1,0,0,0],
            [1,1,0,1,0,0,0,1,0,1,1,0],
            [0,1,0,1,1,1,0,0,0,1,0,0],
            [0,1,0,0,0,0,0,1,0,0,0,1],
            [0,0,0,1,1,1,0,1,1,0,1,0],
            [1,1,0,0,0,0,0,0,0,0,0,0]
        ],
        "start": (0, 0),
        "goal": (9, 11),
        "enemies": [(2, 6), (5, 8), (7, 5), (4, 3)],  # تغيير مواقع الأعداء
        "coins": 10,
        "time_limit": 120
    }
]

# === فئة المتاهة ===
class Maze:
    """فئة لإدارة المتاهة"""
    def __init__(self, level_data: dict, cell_size: int):
        self.grid = level_data["grid"]
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        self.cell_size = cell_size
        self.start = level_data["start"]
        self.goal = level_data["goal"]
        self.player_pos = list(self.start)
        self.time_limit = level_data["time_limit"]
        
        # إنشاء العملات
        self.coins = set()
        self.generate_coins(level_data["coins"])
        
        # إنشاء الأعداء
        self.enemies = [Enemy(pos) for pos in level_data["enemies"]]

    def generate_coins(self, count: int):
        """توليد العملات في مواقع عشوائية"""
        while len(self.coins) < count:
            x = random.randint(0, self.rows-1)
            y = random.randint(0, self.cols-1)
            if (self.grid[x][y] == 0 and 
                (x, y) != tuple(self.player_pos) and 
                (x, y) != self.goal):
                self.coins.add((x, y))

    def draw(self, screen: pygame.Surface, offset_x: int, offset_y: int):
        """رسم المتاهة وعناصرها"""
        # رسم الخلايا
        for r in range(self.rows):
            for c in range(self.cols):
                x = c * self.cell_size + offset_x
                y = r * self.cell_size + offset_y
                cell_rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                
                if self.grid[r][c] == 1:
                    # رسم الجدران
                    pygame.draw.rect(screen, Theme.COLORS['wall'], cell_rect)
                    # إضافة إطار للجدران
                    pygame.draw.rect(screen, Theme.COLORS['primary'], cell_rect, 2)
                else:
                    # رسم الممرات مع شبكة خفيفة
                    pygame.draw.rect(screen, Theme.COLORS['background'], cell_rect)
                    pygame.draw.rect(screen, Theme.COLORS['grid'], cell_rect, 1)
        
        # رسم العملات بحجم أكبر وتأثير توهج
        for coin in self.coins:
            x = coin[1] * self.cell_size + self.cell_size//2 + offset_x
            y = coin[0] * self.cell_size + self.cell_size//2 + offset_y
            coin_size = int(self.cell_size * 0.4)
            coin_surface = Theme.create_neon_surface(coin_size, coin_size, Theme.COLORS['coin'])
            screen.blit(coin_surface, 
                       (x - coin_size//2, y - coin_size//2))
        
        # رسم نقطة النهاية بتأثير متوهج
        goal_x = self.goal[1] * self.cell_size + self.cell_size//2 + offset_x
        goal_y = self.goal[0] * self.cell_size + self.cell_size//2 + offset_y
        goal_surface = Theme.create_neon_surface(self.cell_size, self.cell_size, Theme.COLORS['success'])
        screen.blit(goal_surface, 
                   (goal_x - self.cell_size//2, goal_y - self.cell_size//2))
        
        # رسم اللاعب بتأثير متوهج وحجم مناسب
        player_x = self.player_pos[1] * self.cell_size + self.cell_size//2 + offset_x
        player_y = self.player_pos[0] * self.cell_size + self.cell_size//2 + offset_y
        player_size = int(self.cell_size * 0.8)
        player_surface = Theme.create_neon_surface(player_size, player_size, Theme.COLORS['primary'])
        screen.blit(player_surface, 
                   (player_x - player_size//2, player_y - player_size//2))
        
        # رسم الأعداء بتأثير متوهج وحجم مناسب
        for enemy in self.enemies:
            x = enemy.pos[1] * self.cell_size + self.cell_size//2 + offset_x
            y = enemy.pos[0] * self.cell_size + self.cell_size//2 + offset_y
            enemy_size = int(self.cell_size * 0.7)
            enemy_surface = Theme.create_neon_surface(enemy_size, enemy_size, Theme.COLORS['danger'])
            screen.blit(enemy_surface, 
                       (x - enemy_size//2, y - enemy_size//2))

    def move_player(self, dx: int, dy: int) -> bool:
        """تحريك اللاعب"""
        new_pos = [
            self.player_pos[0] + dx,
            self.player_pos[1] + dy
        ]
        
        # التحقق من صحة الحركة
        if (0 <= new_pos[0] < self.rows and 
            0 <= new_pos[1] < self.cols and 
            self.grid[new_pos[0]][new_pos[1]] == 0):
            
            # التحقق من الاصطدام بالأعداء قبل الحركة
            for enemy in self.enemies:
                if new_pos == enemy.pos or (self.player_pos == enemy.pos):
                    return False
            
            self.player_pos = new_pos
            
            # التحقق من الاصطدام بالأعداء بعد الحركة
            for enemy in self.enemies:
                if self.player_pos == enemy.pos:
                    return False
            
            return True
        return False

    def update(self):
        """تحديث حالة المتاهة"""
        # تحديث الأعداء
        for enemy in self.enemies:
            enemy.update(self.grid, self.player_pos, self.goal)
        
        # التحقق من جمع العملات
        player_pos_tuple = tuple(self.player_pos)
        if player_pos_tuple in self.coins:
            self.coins.remove(player_pos_tuple)
            return 10  # قيمة العملة
        return 0

    def check_goal_reached(self) -> bool:
        """التحقق من الوصول إلى الهدف"""
        return tuple(self.player_pos) == self.goal

# === فئة العميل الذكي ===
class SmartAgent:
    """فئة للعميل الذكي الذي يتحرك تلقائياً"""
    def __init__(self, maze):
        self.maze = maze
        self.path = []
        self.wait_counter = 0
        self.last_enemy_positions = None
        self.move_delay = 30
        self.thinking_time = 45
        self.is_thinking = False
        self.think_counter = 0
        
    def manhattan_distance(self, pos1, pos2):
        """حساب المسافة بين نقطتين"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def is_safe_position(self, pos, enemies):
        """التحقق مما إذا كان الموقع آمناً (بعيداً عن الأعداء)"""
        SAFE_DISTANCE = 2
        for enemy in enemies:
            if self.manhattan_distance(pos, enemy.pos) < SAFE_DISTANCE:
                return False
        return True

    def find_path(self):
        """البحث عن مسار آمن إلى الهدف"""
        if self.is_thinking:
            self.think_counter += 1
            if self.think_counter < self.thinking_time:
                return
            self.is_thinking = False
            self.think_counter = 0

        start = tuple(self.maze.player_pos)
        goal = self.maze.goal

        # التحقق من تغير مواقع الأعداء
        current_enemy_positions = tuple(tuple(enemy.pos) for enemy in self.maze.enemies)
        if self.last_enemy_positions == current_enemy_positions and self.path:
            return
        self.last_enemy_positions = current_enemy_positions

        # قائمة المواقع المفتوحة والمغلقة
        open_list = []
        closed_set = set()
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.manhattan_distance(start, goal)}
        heapq.heappush(open_list, (f_score[start], start))

        while open_list:
            current = heapq.heappop(open_list)[1]

            if current == goal:
                # تم العثور على المسار
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                self.path = path[1:]  # حذف الموقع الحالي
                return

            closed_set.add(current)

            # فحص الاتجاهات الممكنة
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                next_pos = (current[0] + dx, current[1] + dy)

                if (next_pos[0] < 0 or next_pos[0] >= len(self.maze.grid) or
                    next_pos[1] < 0 or next_pos[1] >= len(self.maze.grid[0]) or
                    self.maze.grid[next_pos[0]][next_pos[1]] == 1 or
                    next_pos in closed_set):
                    continue

                # التحقق من سلامة الموقع
                if not self.is_safe_position(next_pos, self.maze.enemies):
                    continue

                tentative_g_score = g_score[current] + 1

                if next_pos not in g_score or tentative_g_score < g_score[next_pos]:
                    came_from[next_pos] = current
                    g_score[next_pos] = tentative_g_score
                    f_score[next_pos] = tentative_g_score + self.manhattan_distance(next_pos, goal)
                    heapq.heappush(open_list, (f_score[next_pos], next_pos))

    def check_collision(self) -> bool:
        """التحقق من الاصطدام مع الأعداء"""
        player_pos = tuple(self.maze.player_pos)
        for enemy in self.maze.enemies:
            if tuple(enemy.pos) == player_pos:
                return True
        return False

    def update(self) -> bool:
        """تحديث حركة العميل"""
        # التحقق من الاصطدام قبل أي حركة
        if self.check_collision():
            return True  # حدث اصطدام

        # إذا كان في وضع التفكير، استمر في العد
        if self.is_thinking:
            self.find_path()
            return False

        # إذا كان هناك تأخير، انتظر
        if self.wait_counter > 0:
            self.wait_counter -= 1
            return False

        # البحث عن مسار جديد إذا لم يكن هناك مسار
        if not self.path:
            self.is_thinking = True
            self.think_counter = 0
            return False

        # التحرك للموقع التالي في المسار
        if self.path:
            next_pos = self.path[0]
            dx = next_pos[0] - self.maze.player_pos[0]
            dy = next_pos[1] - self.maze.player_pos[1]
            if self.maze.move_player(dx, dy):
                self.path.pop(0)
                self.wait_counter = self.move_delay
            else:
                # إعادة حساب المسار إذا كان هناك عائق
                self.path = []
                self.is_thinking = True
                self.think_counter = 0

            # التحقق من الاصطدام بعد الحركة
            return self.check_collision()

        return False

    def a_star_solve(self):
        """تنفيذ A* للعثور على مسار من البداية إلى الهدف."""
        start = tuple(self.maze.player_pos)  # الحصول على موقع البداية للاعب.
        goal = self.maze.goal  # الحصول على موقع الهدف في المتاهة.
        open_list = []  # تهيئة قائمة مفتوحة لتتبع العقد التي يجب استكشافها.
        heapq.heappush(open_list, (0, start, [start]))  # إضافة العقدة البداية إلى القائمة المفتوحة مع المسار.
        g_score = {start: 0}  # تهيئة دالة g لتتبع تكلفة المسار من البداية إلى العقدة الحالية.
        visited = set()  # إنشاء مجموعة لتتبع العقد التي تم زيارتها.

        while open_list:  # الاستمرار حتى لا توجد عقد أخرى للاستكشاف.
            _, current, path = heapq.heappop(open_list)  # إزالة العقدة ذات التكلفة الأقل.
            if current == goal:  # التحقق مما إذا كانت العقدة الحالية هي الهدف.
                return path  # إرجاع المسار إذا تم الوصول إلى الهدف.
            visited.add(current)  # وضع علامة على العقدة الحالية كتمت زيارتها.

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:  # استكشاف جميع الاتجاهات الممكنة.
                next_pos = (current[0] + dx, current[1] + dy)  # حساب الموقع التالي.
                if (0 <= next_pos[0] < len(self.maze.grid) and
                    0 <= next_pos[1] < len(self.maze.grid[0]) and
                    self.maze.grid[next_pos[0]][next_pos[1]] == 0 and
                    next_pos not in visited):  # التحقق مما إذا كان الموقع التالي صالحًا ولم يتم زيارته.
                    tentative_g_score = g_score[current] + 1  # حساب تكلفة المسار المؤقتة.
                    if next_pos not in g_score or tentative_g_score < g_score[next_pos]:  # التحقق من تحسين المسار.
                        g_score[next_pos] = tentative_g_score  # تحديث تكلفة المسار.
                        f_score = tentative_g_score + self.manhattan_distance(next_pos, goal)  # حساب دالة f.
                        heapq.heappush(open_list, (f_score, next_pos, path + [next_pos]))  # إضافة العقدة إلى القائمة المفتوحة.
        return []  # إرجاع مسار فارغ إذا لم يتم العثور على حل.

# === تحديث فئة اللعبة الرئيسية ===
class ModernMazeGame:
    def __init__(self):
        """تهيئة اللعبة"""
        # إعداد النافذة
        info = pygame.display.Info()
        self.width = min(1200, info.current_w - 100)
        self.height = min(800, info.current_h - 100)
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("لعبة المتاهة الذكية")
        
        # إعداد المكونات
        self.ui = UI(self.width, self.height)
        self.language = "ar"
        self.font = TextRenderer.load_font(32)
        self.title_font = TextRenderer.load_font(48)
        
        # تهيئة متغيرات حالة اللعبة
        self.score = 0
        self.current_level = 0
        self.time_left = 60
        self.is_paused = False
        self.start_time = pygame.time.get_ticks()
        self.game_over = False  # إضافة متغير جديد لحالة خسارة اللعبة
        
        # تحميل المستوى الأول
        self.cell_size = 50
        self.maze = Maze(LEVELS[0], self.cell_size)
        self.agent = SmartAgent(self.maze)
        self.auto_move = False
        
        # حساب الإزاحة لتوسيط المتاهة
        self.calculate_offsets()
        
        # إنشاء الأزرار
        self.create_buttons()

        self.total_levels = len(LEVELS)
        self.level_complete = False
        self.game_complete = False
        self.level_transition_timer = 0
        self.transition_delay = 60

    def calculate_offsets(self):
        """حساب إزاحات المتاهة للتوسيط"""
        maze_width = self.maze.cols * self.cell_size
        maze_height = self.maze.rows * self.cell_size
        self.offset_x = (self.width - 300 - maze_width) // 2  # 300 للشريط الجانبي
        self.offset_y = (self.height - maze_height) // 2

    def create_buttons(self):
        """إنشاء الأزرار"""
        button_width = 250  # زيادة عرض الأزرار
        button_height = 50
        x = self.width - 275  # تعديل موقع الأزرار
        
        self.pause_button = ModernButton(
            x, 100, button_width, button_height,
            TRANSLATIONS[self.language]["pause"], self.font,
            is_arabic=(self.language == "ar")
        )
        
        self.restart_button = ModernButton(
            x, 170, button_width, button_height,
            TRANSLATIONS[self.language]["restart"], self.font,
            is_arabic=(self.language == "ar")
        )
        
        self.language_button = ModernButton(
            x, 240, button_width, button_height,
            TRANSLATIONS[self.language]["language"], self.font,
            is_arabic=(self.language == "ar")
        )
        
        self.auto_button = ModernButton(
            x, 310, button_width, button_height,
            TRANSLATIONS[self.language]["auto_move_start"], self.font,
            is_arabic=(self.language == "ar")
        )

        # Add a dropdown or buttons for selecting the algorithm
        self.algorithm_buttons = [
            ModernButton(x, 380, button_width, button_height, "BFS", self.font, is_arabic=(self.language == "ar")),
            ModernButton(x, 450, button_width, button_height, "DFS", self.font, is_arabic=(self.language == "ar")),
            ModernButton(x, 520, button_width, button_height, "A*", self.font, is_arabic=(self.language == "ar"))
        ]

    def draw_game_info(self):
        """رسم معلومات اللعبة"""
        # تحديث الوقت المتبقي
        current_time = pygame.time.get_ticks()
        elapsed = (current_time - self.start_time) / 1000
        self.time_left = max(0, 60 - elapsed)

        texts = [
            TRANSLATIONS[self.language]["score"].format(self.score),
            TRANSLATIONS[self.language]["level"].format(self.current_level + 1),
            TRANSLATIONS[self.language]["time"].format(int(self.time_left))
        ]
        
        for i, text in enumerate(texts):
            surface = TextRenderer.render_text(
                text,
                self.font,
                Theme.COLORS['text'],
                is_arabic=(self.language == "ar")
            )
            x = 20 if self.language == "en" else self.width - 320 - surface.get_width()
            self.screen.blit(surface, (x, 20 + i * 30))

    def load_level(self, level_number: int):
        """تحميل مستوى جديد"""
        if level_number < self.total_levels:
            self.current_level = level_number
            self.maze = Maze(LEVELS[level_number], self.cell_size)
            self.agent = SmartAgent(self.maze)
            self.calculate_offsets()
            self.start_time = pygame.time.get_ticks()
            self.level_complete = False
            self.auto_move = False
            self.is_paused = False
        else:
            self.game_complete = True
            self.score = 0  # تصفير النقاط عند إكمال جميع المستويات

    def check_level_completion(self):
        """التحقق من إكمال المستوى"""
        if not self.level_complete and self.maze.check_goal_reached():
            self.level_complete = True
            self.level_transition_timer = self.transition_delay
            # مكافأة إضافية لإكمال المستوى
            self.score += 100

    def handle_level_transition(self):
        """معالجة الانتقال بين المستويات"""
        if self.level_complete:
            if self.level_transition_timer > 0:
                self.level_transition_timer -= 1
            else:
                self.load_level(self.current_level + 1)

    def draw_level_complete(self):
        """رسم رسالة إكمال المستوى"""
        if self.level_complete and not self.game_complete:
            text = "!مستوى مكتمل" if self.language == "ar" else "Level Complete!"
            surface = TextRenderer.render_text(
                text,
                self.title_font,
                Theme.COLORS['success'],
                is_arabic=(self.language == "ar")
            )
            x = (self.width - surface.get_width()) // 2
            y = (self.height - surface.get_height()) // 2
            self.screen.blit(surface, (x, y))
        elif self.game_complete:
            text = "!أحسنت! أكملت جميع المستويات" if self.language == "ar" else "Congratulations! All Levels Complete!"
            surface = TextRenderer.render_text(
                text,
                self.title_font,
                Theme.COLORS['success'],
                is_arabic=(self.language == "ar")
            )
            x = (self.width - surface.get_width()) // 2
            y = (self.height - surface.get_height()) // 2
            self.screen.blit(surface, (x, y))

    def check_collision_with_enemies(self):
        """التحقق من الاصطدام بالأعداء"""
        player_pos = tuple(self.maze.player_pos)
        for enemy in self.maze.enemies:
            if tuple(enemy.pos) == player_pos:
                self.game_over = True
                self.score = 0  # تصفير النقاط عند الخسارة
                return True
        return False

    def draw_game_over(self):
        """رسم رسالة نهاية اللعبة"""
        if self.game_over:
            text = "!انتهت اللعبة" if self.language == "ar" else "Game Over!"
            surface = TextRenderer.render_text(
                text,
                self.title_font,
                Theme.COLORS['danger'],
                is_arabic=(self.language == "ar")
            )
            x = (self.width - surface.get_width()) // 2
            y = (self.height - surface.get_height()) // 2
            self.screen.blit(surface, (x, y))

    def restart_game(self):
        """إعادة تشغيل اللعبة"""
        self.score = 0
        self.current_level = 0
        self.game_over = False
        self.load_level(0)

    def draw(self):
        """رسم اللعبة"""
        # رسم الخلفية
        self.screen.fill(Theme.COLORS['background'])
        
        # رسم المتاهة
        self.maze.draw(self.screen, self.offset_x, self.offset_y)
        
        # رسم واجهة المستخدم
        self.ui.draw(self.screen)
        
        # رسم معلومات اللعبة
        self.draw_game_info()
        
        # رسم الأزرار
        self.pause_button.draw(self.screen)
        self.restart_button.draw(self.screen)
        self.language_button.draw(self.screen)
        self.auto_button.draw(self.screen)
        
        # رسم الأزرار الجديدة
        for i, button in enumerate(self.algorithm_buttons):
            button.draw(self.screen)
        
        # رسم رسالة إكمال المستوى إذا كان مكتملاً
        self.draw_level_complete()
        
        # رسم رسالة نهاية اللعبة
        self.draw_game_over()
        
        pygame.display.flip()

    def toggle_language(self):
        """تبديل اللغة"""
        self.language = "en" if self.language == "ar" else "ar"
        # تحديث نصوص الأزرار مع اللغة الجديدة
        self.pause_button.set_text(
            TRANSLATIONS[self.language]["pause" if not self.is_paused else "resume"],
            is_arabic=(self.language == "ar")
        )
        self.restart_button.set_text(
            TRANSLATIONS[self.language]["restart"],
            is_arabic=(self.language == "ar")
        )
        self.language_button.set_text(
            TRANSLATIONS[self.language]["language"],
            is_arabic=(self.language == "ar")
        )
        self.auto_button.set_text(
            TRANSLATIONS[self.language]["auto_move_stop" if self.auto_move else "auto_move_start"],
            is_arabic=(self.language == "ar")
        )

    def run(self):
        """تشغيل اللعبة"""
        clock = pygame.time.Clock()
        running = True
        
        while running:
            # معالجة الأحداث
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.width = max(800, event.w)
                    self.height = max(600, event.h)
                    self.screen = pygame.display.set_mode(
                        (self.width, self.height), pygame.RESIZABLE
                    )
                    self.ui = UI(self.width, self.height)
                    self.calculate_offsets()
                    self.create_buttons()
                elif event.type == pygame.KEYDOWN and not self.is_paused and not self.game_over:
                    moved = False
                    if event.key == pygame.K_LEFT:
                        moved = self.maze.move_player(0, -1)
                    elif event.key == pygame.K_RIGHT:
                        moved = self.maze.move_player(0, 1)
                    elif event.key == pygame.K_UP:
                        moved = self.maze.move_player(-1, 0)
                    elif event.key == pygame.K_DOWN:
                        moved = self.maze.move_player(1, 0)
                    
                    # إذا فشلت الحركة بسبب الاصطدام بعدو
                    if not moved:
                        # التحقق من أن السبب هو الاصطدام بعدو
                        if self.check_collision_with_enemies():
                            self.game_over = True
                            self.score = 0
                
                # معالجة أحداث الأزرار
                if self.pause_button.handle_event(event):
                    self.is_paused = not self.is_paused
                    self.pause_button.set_text(
                        TRANSLATIONS[self.language]["resume" if self.is_paused else "pause"],
                        is_arabic=(self.language == "ar")
                    )
                if self.restart_button.handle_event(event):
                    if self.game_over:
                        self.restart_game()
                    else:
                        self.maze = Maze(LEVELS[self.current_level], self.cell_size)
                        self.agent = SmartAgent(self.maze)  # إعادة تهيئة العميل الذكي
                        self.calculate_offsets()
                if self.language_button.handle_event(event):
                    self.toggle_language()
                if self.auto_button.handle_event(event):
                    self.auto_move = not self.auto_move
                    self.auto_button.set_text(
                        TRANSLATIONS[self.language]["auto_move_stop" if self.auto_move else "auto_move_start"],
                        is_arabic=(self.language == "ar")
                    )
                for i, button in enumerate(self.algorithm_buttons):
                    if button.handle_event(event):
                        if i == 0:  # BFS
                            path = self.bfs_solve()
                        elif i == 1:  # DFS
                            path = self.dfs_solve()
                        elif i == 2:  # A*
                            path = self.a_star_solve()
                        
                        # If a path is found, set it for the agent
                        if path:
                            self.agent.path = path
                            self.auto_move = True
                            self.auto_button.set_text(
                                TRANSLATIONS[self.language]["auto_move_stop"],
                                is_arabic=(self.language == "ar")
                            )
            
            if not self.is_paused and self.auto_move and not self.game_over:
                # تحديث العميل الذكي والتحقق من الاصطدام
                if self.agent.update():  # إذا حدث اصطدام
                    self.game_over = True
                    self.score = 0
            
            if not self.is_paused and not self.game_over:
                # تحديث حالة اللعبة
                if not self.level_complete and not self.game_complete:
                    points = self.maze.update()
                    self.score += points
                    if self.check_collision_with_enemies():
                        self.game_over = True
                        self.score = 0
                    else:
                        self.check_level_completion()
                else:
                    self.handle_level_transition()
            
            # رسم اللعبة
            self.draw()
            clock.tick(60)
        
        pygame.quit()
        sys.exit()

    # === خوارزمية البحث بالعرض (BFS) ===
    # هذه الخوارزمية تستخدم للبحث عن أقصر مسار في المتاهة من البداية إلى الهدف.
    # تعمل عن طريق استكشاف جميع الجيران في المستوى الحالي قبل الانتقال إلى المستوى التالي.
    def bfs_solve(self):        
        """تنفيذ BFS للعثور على مسار من البداية إلى الهدف."""
        start = tuple(self.maze.player_pos)  # الحصول على موقع البداية للاعب.
        goal = self.maze.goal  # الحصول على موقع الهدف في المتاهة.
        queue = [(start, [start])]  # تهيئة قائمة انتظار بموقع البداية والمسار.
        visited = set()  # إنشاء مجموعة لتتبع العقد التي تم زيارتها.

        while queue:  # الاستمرار حتى لا توجد عقد أخرى للاستكشاف.
            (current, path) = queue.pop(0)  # إزالة العنصر الأول (FIFO).
            if current == goal:  # التحقق مما إذا كانت العقدة الحالية هي الهدف.
                return path  # إرجاع المسار إذا تم الوصول إلى الهدف.
            visited.add(current)  # وضع علامة على العقدة الحالية كتمت زيارتها.

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:  # استكشاف جميع الاتجاهات الممكنة.
                next_pos = (current[0] + dx, current[1] + dy)  # حساب الموقع التالي.
                if (0 <= next_pos[0] < len(self.maze.grid) and
                    0 <= next_pos[1] < len(self.maze.grid[0]) and
                    self.maze.grid[next_pos[0]][next_pos[1]] == 0 and
                    next_pos not in visited):  # التحقق مما إذا كان الموقع التالي صالحًا ولم يتم زيارته.
                    queue.append((next_pos, path + [next_pos]))  # إضافة الموقع التالي والمسار إلى قائمة الانتظار.
        return []  # إرجاع مسار فارغ إذا لم يتم العثور على حل.

    # === خوارزمية البحث بالعمق (DFS) ===
    # هذه الخوارزمية تستخدم للبحث عن مسار في المتاهة من البداية إلى الهدف.
    # تعمل عن طريق استكشاف مسار واحد حتى النهاية قبل الرجوع واستكشاف مسارات أخرى.
    def dfs_solve(self):
        """تنفيذ DFS للعثور على مسار من البداية إلى الهدف."""
        start = tuple(self.maze.player_pos)  # الحصول على موقع البداية للاعب.
        goal = self.maze.goal  # الحصول على موقع الهدف في المتاهة.
        stack = [(start, [start])]  # تهيئة مكدس بموقع البداية والمسار.
        visited = set()  # إنشاء مجموعة لتتبع العقد التي تم زيارتها.

        while stack:  # الاستمرار حتى لا توجد عقد أخرى للاستكشاف.
            (current, path) = stack.pop()  # إزالة العنصر الأخير (LIFO).
            if current == goal:  # التحقق مما إذا كانت العقدة الحالية هي الهدف.
                return path  # إرجاع المسار إذا تم الوصول إلى الهدف.
            visited.add(current)  # وضع علامة على العقدة الحالية كتمت زيارتها.

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:  # استكشاف جميع الاتجاهات الممكنة.
                next_pos = (current[0] + dx, current[1] + dy)  # حساب الموقع التالي.
                if (0 <= next_pos[0] < len(self.maze.grid) and
                    0 <= next_pos[1] < len(self.maze.grid[0]) and
                    self.maze.grid[next_pos[0]][next_pos[1]] == 0 and
                    next_pos not in visited):  # التحقق مما إذا كان الموقع التالي صالحًا ولم يتم زيارته.
                    stack.append((next_pos, path + [next_pos]))  # إضافة الموقع التالي والمسار إلى المكدس.
        return []  # إرجاع مسار فارغ إذا لم يتم العثور على حل.

    # === خوارزمية البحث A* ===
    # هذه الخوارزمية تستخدم للبحث عن أقصر مسار في المتاهة من البداية إلى الهدف.
    # تعمل عن طريق استخدام دالة تكلفة لتحديد المسار الأمثل بناءً على المسافة المتبقية إلى الهدف.
    def a_star_solve(self):
        """تنفيذ A* للعثور على مسار من البداية إلى الهدف."""
        start = tuple(self.maze.player_pos)  # الحصول على موقع البداية للاعب.
        goal = self.maze.goal  # الحصول على موقع الهدف في المتاهة.
        open_list = []  # تهيئة قائمة مفتوحة لتتبع العقد التي يجب استكشافها.
        heapq.heappush(open_list, (0, start, [start]))  # إضافة العقدة البداية إلى القائمة المفتوحة مع المسار.
        g_score = {start: 0}  # تهيئة دالة g لتتبع تكلفة المسار من البداية إلى العقدة الحالية.
        visited = set()  # إنشاء مجموعة لتتبع العقد التي تم زيارتها.

        while open_list:  # الاستمرار حتى لا توجد عقد أخرى للاستكشاف.
            _, current, path = heapq.heappop(open_list)  # إزالة العقدة ذات التكلفة الأقل.
            if current == goal:  # التحقق مما إذا كانت العقدة الحالية هي الهدف.
                return path  # إرجاع المسار إذا تم الوصول إلى الهدف.
            visited.add(current)  # وضع علامة على العقدة الحالية كتمت زيارتها.

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:  # استكشاف جميع الاتجاهات الممكنة.
                next_pos = (current[0] + dx, current[1] + dy)  # حساب الموقع التالي.
                if (0 <= next_pos[0] < len(self.maze.grid) and
                    0 <= next_pos[1] < len(self.maze.grid[0]) and
                    self.maze.grid[next_pos[0]][next_pos[1]] == 0 and
                    next_pos not in visited):  # التحقق مما إذا كان الموقع التالي صالحًا ولم يتم زيارته.
                    tentative_g_score = g_score[current] + 1  # حساب تكلفة المسار المؤقتة.
                    if next_pos not in g_score or tentative_g_score < g_score[next_pos]:  # التحقق من تحسين المسار.
                        g_score[next_pos] = tentative_g_score  # تحديث تكلفة المسار.
                        f_score = tentative_g_score + self.agent.manhattan_distance(next_pos, goal)  # حساب دالة f.
                        heapq.heappush(open_list, (f_score, next_pos, path + [next_pos]))  # إضافة العقدة إلى القائمة المفتوحة.
        return []  # إرجاع مسار فارغ إذا لم يتم العثور على حل.

# === فئة الزر المتطور ===
class ModernButton:
    """فئة لإنشاء أزرار متطورة"""
    def __init__(self, x: int, y: int, width: int, height: int, text: str, font: pygame.font.Font, is_arabic: bool = True):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.is_arabic = is_arabic
        self.is_hovered = False
        self.animation_progress = 0
        self.glow_surface = Theme.create_neon_surface(width + 20, height + 20, Theme.COLORS['primary'])
        
        # تحميل الخط المناسب للغة
        self.font_size = font.get_height()
        self.base_font = TextRenderer.load_font(self.font_size)
        
        # تحضير سطح النص
        self.update_text_surface()

    def get_fitted_font(self) -> pygame.font.Font:
        """الحصول على حجم الخط المناسب للنص داخل الزر"""
        current_size = self.font_size
        test_font = TextRenderer.load_font(current_size)
        
        # معالجة النص العربي
        display_text = self.text
        if self.is_arabic:
            try:
                display_text = get_display(arabic_reshaper.reshape(self.text))
            except:
                pass
        
        # تقليل حجم الخط حتى يناسب عرض الزر
        margin = 20  # هامش من جوانب الزر
        while test_font.size(display_text)[0] > self.rect.width - margin:
            current_size -= 1
            if current_size < 10:  # حد أدنى لحجم الخط
                break
            test_font = TextRenderer.load_font(current_size)
        
        return test_font

    def update_text_surface(self):
        """تحديث سطح النص مع معالجة النص العربي"""
        fitted_font = self.get_fitted_font()
        self.text_surface = TextRenderer.render_text(
            self.text,
            fitted_font,
            Theme.COLORS['text'],
            self.is_arabic
        )
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)

    def set_text(self, text: str, is_arabic: bool = True):
        """تغيير نص الزر"""
        self.text = text
        self.is_arabic = is_arabic
        self.update_text_surface()

    def draw(self, screen: pygame.Surface):
        """رسم الزر بتأثيرات متقدمة"""
        # تحديث التأثير عند التحويم
        if self.is_hovered:
            self.animation_progress = min(1, self.animation_progress + 0.1)
        else:
            self.animation_progress = max(0, self.animation_progress - 0.1)

        # رسم التوهج
        if self.animation_progress > 0:
            glow_alpha = int(self.animation_progress * 255)
            self.glow_surface.set_alpha(glow_alpha)
            screen.blit(self.glow_surface, 
                       (self.rect.x - 10, self.rect.y - 10))

        # رسم خلفية الزر
        color = Theme.get_gradient_color(
            self.animation_progress,
            Theme.COLORS['primary'],
            Theme.COLORS['secondary']
        )
        pygame.draw.rect(screen, color, self.rect, border_radius=12)

        # رسم النص
        screen.blit(self.text_surface, self.text_rect)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """معالجة أحداث الزر"""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and self.is_hovered:
            return True
        return False

# تشغيل اللعبة
if __name__ == "__main__":
    game = ModernMazeGame()
    game.run() 