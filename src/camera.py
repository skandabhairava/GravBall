
class CameraSystem:
    def __init__(self, coords: tuple[float, float], scale: float, width_height: tuple[float, float]) -> None:
        self.CAM_CENTER_ON = [-coords[0], coords[1]]
        self.SCALE = scale
        self.set_scale = scale
        self.width = width_height[0]
        self.height = width_height[1]

        self._zoom_out_: int = 0
        # 0 -> nothing
        # 1 -> zoom_out
        # 2 -> zoom_in

    def follow(self, coords: tuple[float, float], dt: float) -> None:
        # smooth interpolation towards x, y

        if self._zoom_out_ == 1:
            coords = (0, 0)

        self.CAM_CENTER_ON[0] += (-coords[0] - self.CAM_CENTER_ON[0]) * 2 * self.SCALE * (dt * 3)
        self.CAM_CENTER_ON[1] += (coords[1] - self.CAM_CENTER_ON[1]) * 2 * self.SCALE * (dt * 3)

    def zoom_out(self):
        self.set_scale = self.SCALE
        self._zoom_out_ = 1

    def zoom_in(self):
        self._zoom_out_ = 2

    def zoom(self, delta):
        
        if self._zoom_out_ == 0:
            return
        
        if self._zoom_out_ == 1:
            if self.SCALE - delta <= 0.08:
                self.SCALE = 0.08
            else:
                self.SCALE -= delta

        if self._zoom_out_ == 2:
            if self.SCALE + delta >= self.set_scale:
                self._zoom_out_ = 0
                self.SCALE = self.SCALE
            else:
                self.SCALE += delta

    def calc_pos_x(self, pos_x: float) -> float:
        return (self.CAM_CENTER_ON[0] + pos_x) * self.SCALE + self.width//2

    def calc_pos_y(self, pos_y: float) -> float:
        return (self.CAM_CENTER_ON[1] - pos_y) * self.SCALE + self.height//2
    
    def set_width_height(self, width_height: tuple[float, float]) -> None:
        self.width, self.height = width_height

    def increase_scale(self):

        if self._zoom_out_ != 0:
            return

        if self.SCALE >= 1:
            self.SCALE += 1
        elif self.SCALE < 1:
            self.SCALE += 0.1

        self.SCALE = round(self.SCALE, 1)

        if self.SCALE > 10: self.SCALE = 10

    def decrease_scale(self):

        if self._zoom_out_ != 0:
            return
        
        if self.SCALE > 1:
            self.SCALE -= 1
        elif self.SCALE > 0.1:
            self.SCALE -= 0.1
        elif self.SCALE <= 0.1:
            self.SCALE = 0.1

        self.SCALE = round(self.SCALE, 1)

    def reset(self, coords: tuple[float, float]):
        self._zoom_out_ = 0
        self.SCALE = 1
        self.CAM_CENTER_ON = [-coords[0], coords[1]]