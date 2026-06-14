#src/entities/game_map.py
import json
import random
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

@dataclass
class Entity:
    id: str
    name: str
    x: int
    y: int
    type: str
    interact_text: str
    is_active: bool = True

class GameMap:
    def __init__(self, map_path: str):
        with open(map_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.width = data["width"]
        self.height = data["height"]
        self.terrain = data["terrain"]
        
        # 【性能优化】建立坐标到实体列表的映射，实现 O(1) 查找
        self.entity_grid: Dict[Tuple[int, int], List[Entity]] = {}
        for e_data in data["entities"]:
            entity = Entity(**e_data)
            pos = (entity.x, entity.y)
            self.entity_grid.setdefault(pos, []).append(entity)
            
        # 【第三层：事件层】O(1) 查找
        self.triggers: Dict[Tuple[int, int], str] = {
            tuple(t["pos"]): t["event_id"] for t in data["triggers"]
        }

        # ：初始化每个格子的环境数据 (灵气、资源、特殊地点)
        self.tile_data: Dict[Tuple[int, int], dict] = {}
        resources_pool = ["灵草", "铁矿", "百年人参", None, None, None] # None 概率更高，代表普通空地
        
        for y in range(self.height):
            for x in range(self.width):
                # 只有可通行的格子才有环境数据
                if self.is_walkable(x, y):
                    self.tile_data[(x, y)] = {
                        "lingqi": random.randint(5, 100),          # 随机灵气 5~100
                        "resource_type": random.choice(resources_pool), # 随机资源
                        "ground_items": [],                        # 地上的物品 (初始为空，可通过事件生成)
                        "has_special": random.random() < 0.05      # 5% 概率有特殊地点
                    }
                else:
                    # 墙壁或障碍物不需要环境数据
                    self.tile_data[(x, y)] = {"lingqi": 0, "resource_type": None, "ground_items": [], "has_special": False}


    def is_walkable(self, x: int, y: int) -> bool:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.terrain[y][x] == 0  # 0 为可通行
        return False

    def get_entities_at(self, x: int, y: int) -> List[Entity]:
        """O(1) 复杂度获取指定坐标上的激活实体"""
        return [e for e in self.entity_grid.get((x, y), []) if e.is_active]

    def remove_entity(self, entity_id: str):
        for pos, entities in self.entity_grid.items():
            for e in entities:
                if e.id == entity_id:
                    e.is_active = False
                    return

    def check_trigger(self, x: int, y: int) -> Optional[str]:
        return self.triggers.get((x, y))

    def interact_at(self, x: int, y: int, event_bus):
        """处理交互请求：只负责抛出事件，不处理具体业务逻辑 (彻底解耦)"""
        targets = self.get_entities_at(x, y)
        if targets:
            for target in targets:
                event_bus.emit("entity_interacted", target)
                if target.type == "item":
                    self.remove_entity(target.id)
            return True
        
        event_id = self.check_trigger(x, y)
        if event_id:
            event_bus.emit("trigger_activated", event_id)
            return True
            
        return False