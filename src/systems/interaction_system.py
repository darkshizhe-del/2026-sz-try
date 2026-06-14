#src/systems/interaction_system.py
import pygame
from src.core.state_machine import GameState

class InteractionSystem:
    def __init__(self, state_machine, event_bus):
        self.state = state_machine
        self.bus = event_bus
        self.current_dialog = None
        self.dialog_timer = 0

        # 注册事件监听
        self.bus.on("player_interact", self._on_player_interact)
        self.bus.on("entity_interacted", self._on_entity_interacted)
        self.bus.on("trigger_activated", self._on_trigger_activated)

    def _on_player_interact(self, pos):
        x, y = pos
        # 这里需要访问 map，为了解耦，我们在 main.py 初始化时将 map 传进来，或者通过事件传递
        # 简化版：我们在 main 中直接让 interaction_system 持有 map 引用
        pass 

    def handle_interaction(self, game_map, x, y):
        """由外部(如 main 或 controller)触发，或者通过更复杂的事件传递 map"""
        game_map.interact_at(x, y, self.bus)

    def _on_entity_interacted(self, entity):
        print(f"💬 [{entity.name}]: {entity.interact_text}")
        if entity.type == "item":
            print("  🎒 [系统] 物品已收入背包。")
        elif entity.type == "enemy":
            print("  ⚔️ [系统] 准备进入战斗状态...")
            self.state.push(GameState.COMBAT)
            return
            
        # 模拟交互延迟后恢复状态
        self.current_dialog = entity.interact_text
        self.dialog_timer = pygame.time.get_ticks() + 1500
        self.state.push(GameState.INTERACTING)

    def _on_trigger_activated(self, event_id):
        print(f"  🎬 [剧情触发]: 执行隐形事件 {event_id}")
        self.state.push(GameState.INTERACTING)
        self.dialog_timer = pygame.time.get_ticks() + 2000

    def update(self):
        """在 Game Loop 中调用，处理状态恢复"""
        if self.state.current == GameState.INTERACTING:
            if pygame.time.get_ticks() > self.dialog_timer:
                self.state.pop()
                self.current_dialog = None