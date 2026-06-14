#src/core/state_machine.py
from enum import Enum

class GameState(Enum):
    # 枚举名保持英文(符合代码规范)，但值设为中文(用于UI显示)
    EXPLORE = "探索中"
    INTERACTING = "交互中"
    COMBAT = "战斗中"

class StateMachine:
    def __init__(self, initial_state: GameState):
        self._stack = [initial_state]

    @property
    def current(self) -> GameState:
        return self._stack[-1]

    def push(self, state: GameState):
        self._stack.append(state)

    def pop(self):
        if len(self._stack) > 1:
            self._stack.pop()