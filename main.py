# main.py
import sys
import os
import pygame

# ==========================================
# 🛠️ 智能路径处理 (彻底解决 FileNotFoundError)
# ==========================================
# 1. 获取 main.py 当前所在的绝对路径
main_file_dir = os.path.dirname(os.path.abspath(__file__))

# 2. 智能判断项目根目录 (兼容 main.py 放在根目录 或 src 目录)
if os.path.basename(main_file_dir) == 'src':
    # 如果 main.py 在 src 里，根目录就是它的上一级
    PROJECT_ROOT = os.path.dirname(main_file_dir)
else:
    # 如果 main.py 直接在根目录，根目录就是它自己
    PROJECT_ROOT = main_file_dir

# 3. 将项目根目录加入系统路径，确保 from src.xxx import yyy 永远不报错
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 4. 导入模块 (现在绝对安全)
from src.core.event_bus import EventBus
from src.core.state_machine import StateMachine, GameState
from src.entities.actor import Actor
from src.entities.game_map import GameMap
from src.controllers.player_controller import PlayerController
from src.systems.interaction_system import InteractionSystem
from src.systems.time_system import TimeSystem


# ==========================================
# 🎮 初始化 Pygame
# ==========================================
pygame.init()
SCREEN_W, SCREEN_H = 640, 480
TILE_SIZE = 48
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("我的RPG游戏 - 核心原型")
clock = pygame.time.Clock()

# ==========================================
# 🔤 字体加载 (智能修复中文方块问题)
# ==========================================
# 使用 PROJECT_ROOT 确保无论在哪运行都能找到字体
font_names = ["simhei.ttf", "msyh.ttc", "msyh.ttf", "simsunb.ttf"]
font = None

# 1. 在项目根目录找
for f_name in font_names:
    f_path = os.path.join(PROJECT_ROOT, f_name)
    if os.path.exists(f_path):
        font = pygame.font.Font(f_path, 18)
        print(f"✅ 成功加载项目字体: {f_path}")
        break

# 2. 去 Windows 系统字体目录找
if font is None:
    win_fonts_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
    for f_name in font_names:
        f_path = os.path.join(win_fonts_dir, f_name)
        if os.path.exists(f_path):
            font = pygame.font.Font(f_path, 18)
            print(f"✅ 成功加载系统字体: {f_path}")
            break

# 3. 终极保底
if font is None:
    font = pygame.font.Font(None, 18)
    print("❌ 严重警告：找不到任何中文字体！中文将显示为方块！")

# ==========================================
# 🧩 初始化核心模块
# ==========================================
bus = EventBus()
state_machine = StateMachine(GameState.EXPLORE)
# ✅ 初始化 AP 驱动的时间系统，每阶段 500 点
time_sys = TimeSystem(bus, max_ap_per_phase=500) 
# ✅ 使用 PROJECT_ROOT 拼接地图路径，绝对不会再报错！
map_path = os.path.join(PROJECT_ROOT, "data", "map_01.json")
game_map = GameMap(map_path)
# ✅ 传入 move_ap_cost=10，表示初期走一格消耗 500 点 AP
player = Actor(x=1, y=1, speed=4.0, move_ap_cost=500) 
# 注意：这里去掉了 time_sys，因为交互系统目前保持简单，不需要它 
interaction_sys = InteractionSystem(state_machine, bus) 

player_ctrl = PlayerController(player, game_map, state_machine, bus)


# 初始化控制器与系统
player_ctrl = PlayerController(player, game_map, state_machine, bus)
interaction_sys = InteractionSystem(state_machine, bus)

# 修补 InteractionSystem 对 map 的依赖
original_on_interact = interaction_sys._on_player_interact
def patched_on_interact(pos):
    x, y = pos
    game_map.interact_at(x, y, bus)
interaction_sys._on_player_interact = patched_on_interact

# ==========================================
# 🔁 游戏主循环
# ==========================================
game_tick = 0
running = True
# 记录玩家初始的网格坐标，用于对比是否发生了移动
last_grid_x = player.grid_x
last_grid_y = player.grid_y

while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False

    # 🔄 [更新阶段]
    player_ctrl.handle_input(events)
    player_ctrl.update()
    interaction_sys.update()
    
    # 只有当玩家完全停在格子中心，且坐标真正改变时，才扣除 AP
    if state_machine.current == GameState.EXPLORE: 
        if player._fx == player.x and player._fy == player.y:
            if player.x != last_grid_x or player.y != last_grid_y: 
                
                # 1. 扣除移动所需的行动点
                time_sys.consume_ap(player.move_ap_cost)
                
                # 2. 更新记录，防止同一格重复扣费
                last_grid_x = player.x
                last_grid_y = player.y

    # 🎨 [渲染阶段]
    screen.fill((30, 30, 40)) 
    
    # 1. 渲染地图
    for y in range(game_map.height):
        for x in range(game_map.width):
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            color = (60, 100, 60) if game_map.is_walkable(x, y) else (80, 80, 90)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (40, 40, 50), rect, 1) 
            
            if game_map.check_trigger(x, y):
                s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                s.fill((255, 255, 0, 50))
                screen.blit(s, rect.topleft)

    # 2. 渲染实体
    for pos, entities in game_map.entity_grid.items():
        for e in entities:
            if not e.is_active: continue
            rect = pygame.Rect(e.x * TILE_SIZE + 8, e.y * TILE_SIZE + 8, TILE_SIZE - 16, TILE_SIZE - 16)
            if e.type == "npc": color = (100, 150, 255)
            elif e.type == "item": color = (100, 255, 100)
            elif e.type == "enemy": color = (255, 100, 100)
            pygame.draw.rect(screen, color, rect)
            
            label = font.render(e.name, True, (255, 255, 255))
            screen.blit(label, (rect.x, rect.y - 15))

    # 3. 渲染玩家
    p_rect = pygame.Rect(int(player._fx) * TILE_SIZE + 12, int(player._fy) * TILE_SIZE + 12, TILE_SIZE - 24, TILE_SIZE - 24)
    pygame.draw.rect(screen, (255, 200, 0), p_rect) 
    pygame.draw.rect(screen, (255, 255, 255), p_rect, 2)

    # 4. 渲染 UI (状态与对话)，使用 TimeSystem 提供的格式化字符串
    time_display = time_sys.get_display_string()
    state_text = f"状态: {state_machine.current.value} | {time_display}"
    screen.blit(font.render(state_text, True, (200, 200, 200)), (10, 10)) 
    
    if interaction_sys.current_dialog:
        dlg_rect = pygame.Rect(50, SCREEN_H - 100, SCREEN_W - 100, 80)
        pygame.draw.rect(screen, (0, 0, 0), dlg_rect)
        pygame.draw.rect(screen, (255, 255, 255), dlg_rect, 2)

        # 中文逐字换行逻辑
        text = interaction_sys.current_dialog
        lines = []
        current_line = ""
        max_width = dlg_rect.width - 20
        
        for char in text:
            test_line = current_line + char
            if font.size(test_line)[0] < max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = char
        if current_line:
            lines.append(current_line)
        
        for i, line in enumerate(lines):
            screen.blit(font.render(line.strip(), True, (255, 255, 255)), (dlg_rect.x + 10, dlg_rect.y + 10 + i * 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()