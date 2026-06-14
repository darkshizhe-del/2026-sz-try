# src/systems/time_system.py
from enum import Enum

class TimePhase(Enum):
    MORNING = "早上"
    NOON = "中午"
    EVENING = "晚上"
    MIDNIGHT = "午夜"

class TimeSystem:
    def __init__(self, event_bus, max_ap_per_phase=500):
        self.bus = event_bus
        
        # 📅 日历系统
        self.year = 1
        self.month = 1
        self.day = 1
        
        # ⏳ 阶段与行动点系统
        self.phase = TimePhase.MORNING
        self.max_ap = max_ap_per_phase  # 每个阶段的总行动点 (例如 500)
        self.current_ap = self.max_ap   # 当前剩余行动点

    def consume_ap(self, amount: int):
        """
        核心方法：消耗行动点。
        任何行为（移动、交互、战斗）都调用此方法。
        """
        self.current_ap -= amount
        
        # 如果行动点耗尽，推进阶段
        if self.current_ap <= 0:
            self._advance_phase()

    def _advance_phase(self):
        """推进时间阶段"""
        phase_order = list(TimePhase)
        current_index = phase_order.index(self.phase)
        
        if current_index < len(phase_order) - 1:
            # 进入下一个阶段 (早 -> 中 -> 晚 -> 午夜)
            self.phase = phase_order[current_index + 1]
            self.current_ap = self.max_ap # 重置行动点
            self.bus.emit("time_phase_changed", self.phase.value)
            print(f"🕒 [时间提示] 进入了 {self.phase.value}！行动点已恢复。")
        else:
            # 午夜结束，进入新的一天
            self._advance_day()

    def _advance_day(self):
        """推进天数，处理进位"""
        self.day += 1
        self.phase = TimePhase.MORNING
        self.current_ap = self.max_ap
        
        if self.day > 31:
            self.day = 1
            self.month += 1
            if self.month > 12:
                self.month = 1
                self.year += 1
                self.bus.emit("time_year_changed", self.year)
                
        self.bus.emit("time_day_changed", (self.year, self.month, self.day))
        print(f"🌅 [时间提示] 新的一天开始了！{self.year}年{self.month}月{self.day}日")

    def get_display_string(self) -> str:
        """获取用于 UI 显示的字符串"""
        return f"{self.year}年{self.month}月{self.day}日 {self.phase.value} (AP: {self.current_ap}/{self.max_ap})"