#src/entities/actor.py
class Actor:
    # ✅ 确保这里接收 speed 参数，并设置默认值为 4.0
    def __init__(self, x: int, y: int, speed: float = 4.0, move_ap_cost: int = 500):
        self.x = x  # 逻辑网格坐标
        self.y = y
        self.speed = speed  # ✅ 确保这里把 speed 赋值给 self.speed
        self.move_ap_cost = move_ap_cost #移动一格所消耗的行动点 (AP)
        # 渲染用的浮点坐标，保证平滑移动
        self._fx = float(x)
        self._fy = float(y)

    @property
    def grid_x(self) -> int:
        return int(round(self._fx))

    @property
    def grid_y(self) -> int:
        return int(round(self._fy))

    def set_position(self, x: int, y: int):
        self.x = x
        self.y = y
        self._fx = float(x)
        self._fy = float(y)