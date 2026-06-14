#src/controller/player_controller.py
import pygame
from src.core.state_machine import GameState

class PlayerController:
    def __init__(self, actor, game_map, state_machine, event_bus):
        self.actor = actor
        self.map = game_map
        self.state = state_machine
        self.bus = event_bus
        
        # ✅ 网格跳跃专属状态
        self.is_moving = False        # 是否正在播放移动动画
        self.target_x = actor.grid_x  # 目标格子的 X 坐标
        self.target_y = actor.grid_y  # 目标格子的 Y 坐标
        self.move_speed = 0.15        # 移动速度：每帧移动的“格子比例”。0.15 意味着大约 0.16秒 走完一格(60fps下)

    def handle_input(self, events):
        if self.state.current != GameState.EXPLORE:
            return

        for event in events:
            if event.type == pygame.KEYDOWN:
                # 交互键 Z 随时可用
                if event.key == pygame.K_z:
                    self.bus.emit("player_interact", (self.actor.grid_x, self.actor.grid_y))
                    continue

                # ✅ 核心拦截：如果正在移动动画中，屏蔽所有方向键输入
                if self.is_moving:
                    continue

                # 计算假设的目标坐标
                target_x, target_y = self.actor.grid_x, self.actor.grid_y
                if event.key in (pygame.K_UP, pygame.K_w): target_y -= 1
                elif event.key in (pygame.K_DOWN, pygame.K_s): target_y += 1
                elif event.key in (pygame.K_LEFT, pygame.K_a): target_x -= 1
                elif event.key in (pygame.K_RIGHT, pygame.K_d): target_x += 1

                # 如果目标坐标发生了改变，且目标格子是“可通行”的
                if (target_x != self.actor.grid_x or target_y != self.actor.grid_y):
                    if self.map.is_walkable(target_x, target_y):
                        self.target_x = target_x
                        self.target_y = target_y
                        self.is_moving = True  # 🔒 锁定状态，开始移动动画

    def update(self):
        if self.state.current != GameState.EXPLORE:
            return
            
        # 如果没有在移动，什么都不做
        if not self.is_moving:
            return

        # ✅ 平滑插值：让浮点坐标逐渐靠近目标坐标
        # X轴移动
        if self.actor._fx != self.target_x:
            diff = self.target_x - self.actor._fx
            step = self.move_speed if diff > 0 else -self.move_speed
            # 如果剩余距离小于一步，直接对齐到目标点
            if abs(diff) <= abs(step):
                self.actor._fx = self.target_x
            else:
                self.actor._fx += step
        
        # Y轴移动
        if self.actor._fy != self.target_y:
            diff = self.target_y - self.actor._fy
            step = self.move_speed if diff > 0 else -self.move_speed
            if abs(diff) <= abs(step):
                self.actor._fy = self.target_y
            else:
                self.actor._fy += step

        # ✅ 动画完成：当浮点坐标完全等于目标坐标时，解锁状态
        if self.actor._fx == self.target_x and self.actor._fy == self.target_y:
            self.is_moving = False
            # 同步逻辑网格坐标
            self.actor.x = self.actor.grid_x
            self.actor.y = self.actor.grid_y

    def _try_move(self, target_x, target_y):
        if self.map.is_walkable(target_x, target_y):
            self.target_x = target_x
            self.target_y = target_y
            self.is_moving = True
            
            # 🌟 动态计算耗时公式
            # 基础耗时 10 分钟。玩家每有 1 点“敏捷”或“移速等级”，减少 1 分钟。
            # 最低耗时不能少于 2 分钟（防止瞬间移动）
            base_cost = 10 
            speed_bonus = self.actor.speed_level # 假设 Actor 有这个属性
            
            actual_cost = max(2, base_cost - speed_bonus) 
            
            # 调用统一的时间推进器
            self.time_sys.advance(actual_cost) 