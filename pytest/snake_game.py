import pygame
import random
import sys

# 游戏常量定义
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE
FONT_SIZE = 48

# 游戏状态常量
MENU = "menu"
DIFFICULTY = "difficulty"  # 新增难度选择状态
GAME = "game"
GAME_OVER = "game_over"
PAUSE = "pause"

# 颜色定义
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)  # 障碍物颜色
YELLOW = (255, 255, 0)  # 蛇头颜色
BLUE = (0, 0, 255)       # 加速食物
PURPLE = (128, 0, 128)   # 减速食物
PINK = (255, 192, 203)   # 缩短食物
ORANGE = (255, 165, 0)   # 无敌食物

# 方向常量
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

def get_font(size=20):
    """获取系统中文字体"""
    system_fonts = pygame.font.get_fonts()
    chinese_fonts = ['simhei', 'simsun', 'microsoftyahei', 'dengxian']
    
    for font in chinese_fonts:
        if font in system_fonts:
            return pygame.font.SysFont(font, size)
    
    return pygame.font.Font(None, size)

class Button:
    def __init__(self, x, y, width, height, text, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.font = get_font()  # 使用中文字体
        
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        text_surface = self.font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
        
    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class Obstacle:
    def __init__(self, screen):
        self.screen = screen
        self.positions = set()  # 用集合存储障碍物位置
        self.color = GRAY
        
    def generate(self, snake_pos, food_pos, border_holes, count=20):
        """生成随机障碍物
        
        Args:
            snake_pos: 蛇的初始位置
            food_pos: 食物的位置
            border_holes: 边框洞口位置
            count: 障碍物数量
        """
        self.positions.clear()
        
        # 添加墙壁作为障碍物
        for x in range(GRID_WIDTH):
            self.positions.add((x, 0))  # 顶部墙壁
            self.positions.add((x, GRID_HEIGHT - 1))  # 底部墙壁
        for y in range(GRID_HEIGHT):
            self.positions.add((0, y))  # 左侧墙壁
            self.positions.add((GRID_WIDTH - 1, y))  # 右侧墙壁
        
        # 移除洞口位置的墙壁
        for side, pos, size in border_holes:
            if side == 'top':
                for x in range(pos - size // (2 * GRID_SIZE), pos + size // (2 * GRID_SIZE)):
                    self.positions.discard((x, 0))
            elif side == 'bottom':
                for x in range(pos - size // (2 * GRID_SIZE), pos + size // (2 * GRID_SIZE)):
                    self.positions.discard((x, GRID_HEIGHT - 1))
            elif side == 'left':
                for y in range(pos - size // (2 * GRID_SIZE), pos + size // (2 * GRID_SIZE)):
                    self.positions.discard((0, y))
            elif side == 'right':
                for y in range(pos - size // (2 * GRID_SIZE), pos + size // (2 * GRID_SIZE)):
                    self.positions.discard((GRID_WIDTH - 1, y))
        
        # 定义蛇头周围的安全区域
        safe_zone = set()
        head_x, head_y = snake_pos[0]
        
        # 创建一个5x5的安全区域（可以根据需要调整大小）
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                safe_x = head_x + dx
                safe_y = head_y + dy
                if 0 <= safe_x < GRID_WIDTH and 0 <= safe_y < GRID_HEIGHT:
                    safe_zone.add((safe_x, safe_y))
        
        # 生成障碍物时避开安全区域
        attempts = 0
        max_attempts = 1000  # 防止无限循环
        
        while len(self.positions) < count + 2 * (GRID_WIDTH + GRID_HEIGHT) and attempts < max_attempts:
            pos = (random.randint(1, GRID_WIDTH-2), 
                  random.randint(1, GRID_HEIGHT-2))
            
            # 确保障碍物不会生成在：
            # 1. 蛇的位置
            # 2. 食物的位置
            # 3. 安全区域内
            # 4. 已有的障碍物位置
            if (pos not in snake_pos and 
                pos != food_pos and 
                pos not in safe_zone and 
                pos not in self.positions):
                self.positions.add(pos)
            
            attempts += 1
    
    def is_collision(self, pos):
        """检查是否与障碍物碰撞"""
        return pos in self.positions
    
    def render(self):
        """绘制障碍物"""
        for pos in self.positions:
            pygame.draw.rect(self.screen, self.color,
                           (pos[0] * GRID_SIZE, 
                            pos[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.dragging = False
        self.handle_width = 20
        self.handle_rect = pygame.Rect(self.get_handle_x(), y - height//2, 
                                     self.handle_width, height * 2)
    
    def get_handle_x(self):
        # 计算滑块手柄的x位置
        range_width = self.rect.width - self.handle_width
        value_ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        return self.rect.x + (range_width * value_ratio)
    
    def draw(self, surface):
        # 绘制滑动条背景
        pygame.draw.rect(surface, GRAY, self.rect)
        # 更新手柄位置
        self.handle_rect.x = self.get_handle_x()
        # 绘制滑块手柄
        pygame.draw.rect(surface, WHITE, self.handle_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.handle_rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            # 计算新的值
            x = min(max(event.pos[0], self.rect.x), self.rect.right - self.handle_width)
            ratio = (x - self.rect.x) / (self.rect.width - self.handle_width)
            self.value = self.min_val + ratio * (self.max_val - self.min_val)
            return True
        return False

class Border:
    def __init__(self, screen):
        self.screen = screen
        self.holes = []  # 存储洞口位置
        self.color = WHITE
        self.thickness = 6

    def generate_holes(self, difficulty):
        """生成随机洞口
        Args:
            difficulty: 游戏难度
        """
        self.holes = []
        sides = ['top', 'right', 'bottom', 'left']
        random.shuffle(sides)
        
        if difficulty == "easy":
            num_holes = 4
            large_hole_prob = 0.5
        elif difficulty == "medium":
            num_holes = 3
            large_hole_prob = 0.3
        else:  # hard
            num_holes = 2
            large_hole_prob = 0.2
        
        selected_sides = sides[:num_holes]
        
        for side in selected_sides:
            if random.random() < large_hole_prob:
                size = GRID_SIZE * 5
            else:
                size = GRID_SIZE * 3
            
            if side == 'top':
                x = random.randint(1, GRID_WIDTH-2)
                self.holes.append(('top', x, size))
                self.holes.append(('bottom', x, size))  # 对应底部洞口
            elif side == 'right':
                y = random.randint(1, GRID_HEIGHT-2)
                self.holes.append(('right', y, size))
                self.holes.append(('left', y, size))  # 对应左侧洞口
            elif side == 'bottom':
                x = random.randint(1, GRID_WIDTH-2)
                self.holes.append(('bottom', x, size))
                self.holes.append(('top', x, size))  # 对应顶部洞口
            elif side == 'left':
                y = random.randint(1, GRID_HEIGHT-2)
                self.holes.append(('left', y, size))
                self.holes.append(('right', y, size))  # 对应右侧洞口
    
    def render(self):
        """绘制边框和洞口"""
        lines = [
            ((0, 0), (WINDOW_WIDTH, 0)),
            ((WINDOW_WIDTH-self.thickness, 0), (WINDOW_WIDTH-self.thickness, WINDOW_HEIGHT)),
            ((0, WINDOW_HEIGHT-self.thickness), (WINDOW_WIDTH, WINDOW_HEIGHT-self.thickness)),
            ((0, 0), (0, WINDOW_HEIGHT))
        ]
        
        for start, end in lines:
            pygame.draw.line(self.screen, self.color, start, end, self.thickness)
        
        for side, pos, size in self.holes:
            if side == 'top':
                pygame.draw.rect(self.screen, BLACK,
                               (pos * GRID_SIZE - size//2, 0,
                                size, self.thickness))
                pygame.draw.rect(self.screen, YELLOW,
                               (pos * GRID_SIZE - size//2, 0,
                                size, self.thickness), 2)
            elif side == 'right':
                pygame.draw.rect(self.screen, BLACK,
                               (WINDOW_WIDTH-self.thickness, pos * GRID_SIZE - size//2,
                                self.thickness, size))
                pygame.draw.rect(self.screen, YELLOW,
                               (WINDOW_WIDTH-self.thickness, pos * GRID_SIZE - size//2,
                                self.thickness, size), 2)
            elif side == 'bottom':
                pygame.draw.rect(self.screen, BLACK,
                               (pos * GRID_SIZE - size//2, WINDOW_HEIGHT-self.thickness,
                                size, self.thickness))
                pygame.draw.rect(self.screen, YELLOW,
                               (pos * GRID_SIZE - size//2, WINDOW_HEIGHT-self.thickness,
                                size, self.thickness), 2)
            elif side == 'left':
                pygame.draw.rect(self.screen, BLACK,
                               (0, pos * GRID_SIZE - size//2,
                                self.thickness, size))
                pygame.draw.rect(self.screen, YELLOW,
                               (0, pos * GRID_SIZE - size//2,
                                self.thickness, size), 2)

class Game:
    def __init__(self, screen, game_font):
        self.screen = screen
        self.game_font = game_font
        self.state = MENU
        self.snake = Snake(screen)
        self.food = Food(screen)
        self.obstacle = Obstacle(screen)
        self.difficulty = None  # 新增难度属性
        self.border = Border(screen)  # 添加边框
        
        # 创建主菜单按钮
        self.start_button = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 - 25,
                                 200, 50, "开始游戏", GREEN)
        self.instructions_button = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 + 50,
                                          200, 50, "游戏说明", BLUE)
        
        # 创建难度选择按钮
        button_width = 150
        button_spacing = 20
        total_width = 3 * button_width + 2 * button_spacing
        start_x = (WINDOW_WIDTH - total_width) // 2
        
        self.easy_button = Button(start_x, WINDOW_HEIGHT//2 - 25,
                                button_width, 50, "简单", GREEN)
        self.medium_button = Button(start_x + button_width + button_spacing,
                                  WINDOW_HEIGHT//2 - 25,
                                  button_width, 50, "中", YELLOW)
        self.hard_button = Button(start_x + 2 * (button_width + button_spacing),
                                WINDOW_HEIGHT//2 - 25,
                                button_width, 50, "困难", RED)
        
        # 创建按钮
        self.restart_button = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 - 25,
                                   200, 50, "重新开始", RED)
        # 添加继续游戏和返回主菜单按钮
        self.continue_button = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 - 60,
                                    200, 50, "继续游戏", GREEN)
        self.to_menu_button = Button(WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 + 10,
                                   200, 50, "返回主菜单", RED)
        
        # 添加速度滑块
        self.speed_slider = Slider(WINDOW_WIDTH//4, WINDOW_HEIGHT//2 + 80, 
                                 WINDOW_WIDTH//2, 10, 5, 20, 10)
        self.game_speed = 10  # 初始游戏速度
        
        self.instructions_font = get_font(18)  # 使用较小的字体
    
    def start_new_game(self):
        """开始新游戏时初始化所有元素"""
        self.snake.reset()
        self.food.randomize_position()
        self.border.generate_holes(self.difficulty)  # 根据难度生成洞口
        
        # 根据难度设置障碍物数量
        obstacle_count = {
            "easy": 10,    # 简单模式：10个障碍物
            "medium": 20,  # 中等模式：20个障碍物
            "hard": 30     # 困难模式：30个障碍物
        }.get(self.difficulty, 20)  # 默认中等难度
        
        self.obstacle.generate([self.snake.get_head_position()],
                             self.food.position,
                             self.border.holes,
                             count=obstacle_count)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                if self.state == MENU:
                    if self.start_button.is_clicked(mouse_pos):
                        self.state = DIFFICULTY
                    elif self.instructions_button.is_clicked(mouse_pos):
                        self.state = "instructions"
                
                elif self.state == DIFFICULTY:
                    if self.easy_button.is_clicked(mouse_pos):
                        self.difficulty = "easy"
                        self.state = GAME
                        self.start_new_game()
                    elif self.medium_button.is_clicked(mouse_pos):
                        self.difficulty = "medium"
                        self.state = GAME
                        self.start_new_game()
                    elif self.hard_button.is_clicked(mouse_pos):
                        self.difficulty = "hard"
                        self.state = GAME
                        self.start_new_game()
                
                elif self.state == GAME_OVER and self.restart_button.is_clicked(mouse_pos):
                    self.state = DIFFICULTY
                    self.difficulty = None
                
                elif self.state == PAUSE:
                    if self.continue_button.is_clicked(mouse_pos):
                        self.state = GAME
                    elif self.to_menu_button.is_clicked(mouse_pos):
                        self.state = MENU
                        self.difficulty = None
            
            if event.type == pygame.KEYDOWN:
                if self.state == "instructions" and event.key == pygame.K_ESCAPE:
                    self.state = MENU
                elif self.state == DIFFICULTY and event.key == pygame.K_ESCAPE:
                    self.state = MENU
                elif self.state == GAME:
                    if event.key == pygame.K_ESCAPE:
                        self.state = PAUSE
                    elif event.key == pygame.K_UP and self.snake.direction != DOWN:
                        self.snake.direction = UP
                    elif event.key == pygame.K_DOWN and self.snake.direction != UP:
                        self.snake.direction = DOWN
                    elif event.key == pygame.K_LEFT and self.snake.direction != RIGHT:
                        self.snake.direction = LEFT
                    elif event.key == pygame.K_RIGHT and self.snake.direction != LEFT:
                        self.snake.direction = RIGHT
                elif self.state == PAUSE and event.key == pygame.K_ESCAPE:
                    self.state = GAME
        return True
        
    def update(self):
        if self.state == GAME:
            head_pos = self.snake.get_head_position()
            
            for side, pos, size in self.border.holes:
                if side == 'left' and head_pos[0] < 0:
                    if abs(head_pos[1] - pos) < size // GRID_SIZE:
                        new_y = pos
                        self.snake.positions = [(GRID_WIDTH - 1, new_y)] + self.snake.positions[:-1]
                        return
                elif side == 'right' and head_pos[0] >= GRID_WIDTH:
                    if abs(head_pos[1] - pos) < size // GRID_SIZE:
                        new_y = pos
                        self.snake.positions = [(0, new_y)] + self.snake.positions[:-1]
                        return
                elif side == 'top' and head_pos[1] < 0:
                    if abs(head_pos[0] - pos) < size // GRID_SIZE:
                        new_x = pos
                        self.snake.positions = [(new_x, GRID_HEIGHT - 1)] + self.snake.positions[:-1]
                        return
                elif side == 'bottom' and head_pos[1] >= GRID_HEIGHT:
                    if abs(head_pos[0] - pos) < size // GRID_SIZE:
                        new_x = pos
                        self.snake.positions = [(new_x, 0)] + self.snake.positions[:-1]
                        return
            
            if not self.snake.update():
                self.state = GAME_OVER
            
            if self.obstacle.is_collision(self.snake.get_head_position()):
                if not self.snake.invincible:
                    self.state = GAME_OVER
            
            head_pos = self.snake.get_head_position()
            food_size = int(self.food.current_size // GRID_SIZE)
            
            food_area = [(self.food.position[0] + dx, self.food.position[1] + dy)
                        for dx in range(food_size)
                        for dy in range(food_size)]
            
            if head_pos in food_area:
                score = self.food.food_types[self.food.current_type]['effect'](self)
                self.snake.score += score
                while True:
                    self.food.randomize_position()
                    food_size = int(self.food.current_size // GRID_SIZE)
                    new_food_area = [(self.food.position[0] + dx, self.food.position[1] + dy)
                                   for dx in range(food_size)
                                   for dy in range(food_size)]
                    if not any(self.obstacle.is_collision(pos) for pos in new_food_area) and \
                       not any(pos in self.snake.positions for pos in new_food_area):
                        break
    
    def render_instructions(self):
        """绘制游戏说明"""
        instructions = [
            ("游戏说明", WHITE),
            ("", WHITE),
            ("控制蛇移动，吃掉食物，避免撞到墙壁和障碍物。", WHITE),
            ("", WHITE),
            ("食物类型：", WHITE),
            ("  红色方块: 普通食物，增加1长度", RED),
            ("  蓝色方块: 加速食物，增加速度", BLUE),
            ("  紫色方块: 减速食物，降低速度", PURPLE),
            ("  粉色方块: 缩短食物，减少长度", PINK),
            ("  橙色方块: 无敌食物，获得短暂无敌", ORANGE),
            ("  大红色方块: 增加更多长度，大小随机", RED),
            ("", WHITE),
            ("边框和洞口：", WHITE),
            ("  黄色标记: 洞口，蛇可以穿过", YELLOW),
            ("", WHITE),
            ("按ESC键暂停游戏，调整速度或返回主菜单。", WHITE)
        ]
        
        y_offset = WINDOW_HEIGHT // 12  # 将说明再上移
        for text, color in instructions:
            instruction_text = self.instructions_font.render(text, True, color)
            instruction_rect = instruction_text.get_rect(center=(WINDOW_WIDTH//2, y_offset))
            self.screen.blit(instruction_text, instruction_rect)
            y_offset += 35  # 调整行间距

    def render(self):
        self.screen.fill(BLACK)
        
        if self.state == MENU:
            title_text = self.game_font.render("贪吃蛇游戏", True, WHITE)
            title_rect = title_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//3))
            self.screen.blit(title_text, title_rect)
            self.start_button.draw(self.screen)
            self.instructions_button.draw(self.screen)
        
        elif self.state == "instructions":
            self.render_instructions()
            back_text = self.game_font.render("按ESC返回主菜单", True, WHITE)
            back_rect = back_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT - 50))
            self.screen.blit(back_text, back_rect)
        
        elif self.state == DIFFICULTY:
            # 绘制难度选择标题
            title_text = self.game_font.render("选择难度", True, WHITE)
            title_rect = title_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//3))
            self.screen.blit(title_text, title_rect)
            
            # 绘制"请选择难度"提示文字
            info_text = self.game_font.render("障碍物依次增加", True, WHITE)
            info_rect = info_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//3 + 50))
            self.screen.blit(info_text, info_rect)
            
            # 绘制难度选择按钮
            self.easy_button.draw(self.screen)
            self.medium_button.draw(self.screen)
            self.hard_button.draw(self.screen)
            
        elif self.state == GAME:
            self.border.render()  # 绘制边框和洞口
            self.obstacle.render()  # 先绘制障碍物
            self.snake.render()     # 再绘制蛇
            self.food.render()      # 最后绘制食物
            # 显示分数
            score_text = self.game_font.render(f"分数: {self.snake.score}", True, WHITE)
            self.screen.blit(score_text, (10, 10))
            
        elif self.state == GAME_OVER:
            # 显示游戏结束和最终分数
            game_over_text = self.game_font.render("游戏结束!", True, WHITE)
            score_text = self.game_font.render(f"最终分数: {self.snake.score}", True, WHITE)
            game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//3))
            score_rect = score_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//3 + 60))
            self.screen.blit(game_over_text, game_over_rect)
            self.screen.blit(score_text, score_rect)
            self.restart_button.draw(self.screen)
            
        elif self.state == PAUSE:
            # 渲染游戏面（暂停时保持游戏画面不变）
            self.obstacle.render()
            self.snake.render()
            self.food.render()
            score_text = self.game_font.render(f"分数: {self.snake.score}", True, WHITE)
            self.screen.blit(score_text, (10, 10))
            
            # 添加半透明黑色遮罩
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            overlay.fill(BLACK)
            overlay.set_alpha(128)  # 设置透明度（0-255）
            self.screen.blit(overlay, (0, 0))
            
            # 显示暂停菜单
            pause_text = self.game_font.render("游戏暂停", True, WHITE)
            pause_rect = pause_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//3))
            self.screen.blit(pause_text, pause_rect)
            
            # 显示暂停菜单按钮
            self.continue_button.draw(self.screen)
            self.to_menu_button.draw(self.screen)
            
            # 绘制速度滑块
            speed_text = self.game_font.render(f"游戏速度: {int(self.speed_slider.value)}", True, WHITE)
            speed_rect = speed_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 60))
            self.screen.blit(speed_text, speed_rect)
            self.speed_slider.draw(self.screen)
        
        pygame.display.flip()

class Snake:
    def __init__(self, screen):
        self.screen = screen
        self.length = 1
        self.positions = [(GRID_WIDTH//2, GRID_HEIGHT//2)]
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        self.color = GREEN
        self.head_color = YELLOW
        self.score = 0
        self.invincible = False
        self.invincible_time = 0
        self.invincible_duration = 5000  # 无敌时间5秒

    def get_head_position(self):
        return self.positions[0]

    def update(self):
        # 更新无敌状态
        if self.invincible and pygame.time.get_ticks() - self.invincible_time > self.invincible_duration:
            self.invincible = False

        cur = self.get_head_position()
        x, y = self.direction
        new_x = cur[0] + x
        new_y = cur[1] + y
        
        # 移除边界检查，让 Game 类来处理边界情况
        new = (new_x, new_y)
        # 只检查是否撞到自己
        if new in self.positions[3:]:
            return False if not self.invincible else True
            
        self.positions.insert(0, new)
        if len(self.positions) > self.length:
            self.positions.pop()
        return True

    def reset(self):
        self.length = 1
        self.positions = [(GRID_WIDTH//2, GRID_HEIGHT//2)]
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        self.score = 0

    def render(self):
        # 绘制边框
        border_rect = pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, WHITE, border_rect, 2)
        
        # 绘制蛇身（除了头部）
        for p in self.positions[1:]:
            pygame.draw.rect(self.screen, self.color, 
                           (p[0] * GRID_SIZE, p[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE))
        
        # 绘制蛇头
        head_pos = self.positions[0]
        head_x = head_pos[0] * GRID_SIZE
        head_y = head_pos[1] * GRID_SIZE
        
        # 先画一个方块作为基础
        pygame.draw.rect(self.screen, self.head_color,
                        (head_x, head_y, GRID_SIZE, GRID_SIZE))
        
        # 根据方向绘制三角形指示方向
        if self.direction == UP:
            points = [(head_x + GRID_SIZE//2, head_y),
                     (head_x, head_y + GRID_SIZE//2),
                     (head_x + GRID_SIZE, head_y + GRID_SIZE//2)]
        elif self.direction == DOWN:
            points = [(head_x + GRID_SIZE//2, head_y + GRID_SIZE),
                     (head_x, head_y + GRID_SIZE//2),
                     (head_x + GRID_SIZE, head_y + GRID_SIZE//2)]
        elif self.direction == LEFT:
            points = [(head_x, head_y + GRID_SIZE//2),
                     (head_x + GRID_SIZE//2, head_y),
                     (head_x + GRID_SIZE//2, head_y + GRID_SIZE)]
        else:  # RIGHT
            points = [(head_x + GRID_SIZE, head_y + GRID_SIZE//2),
                     (head_x + GRID_SIZE//2, head_y),
                     (head_x + GRID_SIZE//2, head_y + GRID_SIZE)]
        
        pygame.draw.polygon(self.screen, BLACK, points)

class Food:
    def __init__(self, screen):
        self.screen = screen
        self.position = (0, 0)
        self.size_range = {
            'small': GRID_SIZE,
            'medium': GRID_SIZE * 1.5,
            'large': GRID_SIZE * 2
        }
        self.current_size = self.size_range['small']
        
        self.food_types = {
            'normal': {
                'color': RED,
                'probability': 0.5,
                'score': 1,
                'effect': self.normal_effect
            },
            'big_red': {
                'color': RED,
                'probability': 0.1,
                'score': 3,
                'effect': self.big_red_effect
            },
            'speed_up': {
                'color': BLUE,
                'probability': 0.1,
                'score': 2,
                'effect': self.speed_up_effect
            },
            'speed_down': {
                'color': PURPLE,
                'probability': 0.1,
                'score': 2,
                'effect': self.speed_down_effect
            },
            'invincible': {
                'color': ORANGE,
                'probability': 0.05,
                'score': 5,
                'effect': self.invincible_effect
            },
            'reverse': {
                'color': (255, 165, 0),
                'probability': 0.05,
                'score': 3,
                'effect': self.reverse_effect
            },
            'bonus': {
                'color': (255, 215, 0),
                'probability': 0.05,
                'score': 10,
                'effect': self.bonus_effect
            }
        }
        self.current_type = 'normal'
        self.color = self.food_types['normal']['color']
        self.randomize_position()

    def randomize_position(self):
        size_in_grid = int(self.current_size // GRID_SIZE)
        max_x = GRID_WIDTH - size_in_grid
        max_y = GRID_HEIGHT - size_in_grid
        
        self.position = (random.randint(0, max_x), random.randint(0, max_y))
        
        rand = random.random()
        cumulative_prob = 0
        for food_type, properties in self.food_types.items():
            cumulative_prob += properties['probability']
            if rand <= cumulative_prob:
                self.current_type = food_type
                self.color = properties['color']
                break
        
        if self.current_type == 'big_red':
            self.current_size = random.choice(list(self.size_range.values()))
        else:
            self.current_size = self.size_range['small']

    def render(self):
        size = int(self.current_size)
        pygame.draw.rect(self.screen, self.color,
                        (self.position[0] * GRID_SIZE, 
                         self.position[1] * GRID_SIZE,
                         size, size))
        
        if self.current_type != 'normal':
            if pygame.time.get_ticks() % 1000 < 500:
                pygame.draw.rect(self.screen, WHITE,
                               (self.position[0] * GRID_SIZE, 
                                self.position[1] * GRID_SIZE,
                                size, size), 2)

    def reverse_effect(self, game):
        game.snake.positions.reverse()
        game.snake.direction = (-game.snake.direction[0], -game.snake.direction[1])
        return self.food_types[self.current_type]['score']

    def bonus_effect(self, game):
        return self.food_types[self.current_type]['score']

    def normal_effect(self, game):
        game.snake.length += 1
        return self.food_types[self.current_type]['score']

    def speed_up_effect(self, game):
        game.game_speed = min(20, game.game_speed + 2)
        game.snake.length += 1
        return self.food_types[self.current_type]['score']

    def speed_down_effect(self, game):
        game.game_speed = max(5, game.game_speed - 2)
        game.snake.length += 1
        return self.food_types[self.current_type]['score']

    def invincible_effect(self, game):
        game.snake.invincible = True
        game.snake.invincible_time = pygame.time.get_ticks()
        game.snake.length += 1
        return self.food_types[self.current_type]['score']

    def big_red_effect(self, game):
        # 根据食物大小增加蛇的长度
        size_multiplier = self.current_size / GRID_SIZE
        length_increase = int(size_multiplier * 3)  # 基础增长3格
        game.snake.length += length_increase
        return self.food_types[self.current_type]['score'] * int(size_multiplier)

def main():
    # 初始化Pygame
    pygame.init()
    pygame.font.init()
    
    # 创游戏窗口
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption('贪吃蛇游戏')
    
    # 初始化字体
    game_font = get_font()  # 使用中文字体
    
    # 创建游戏实例
    game = Game(screen, game_font)
    clock = pygame.time.Clock()
    
    # 游戏主循环
    running = True
    while running:
        running = game.handle_events()
        game.update()
        game.render()
        clock.tick(game.game_speed)  # 使用游戏速度控制帧率

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()