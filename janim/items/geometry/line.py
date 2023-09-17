from __future__ import annotations
from typing import Iterable, Optional
from janim.typing import Self

from janim.constants import *
from janim.items.item import Item
from janim.items.vitem import VItem, DashedVItem
from janim.items.geometry.arc import Arc
from janim.utils.space_ops import (
    get_norm, normalize,
    rotate_vector, angle_of_vector
)
from janim.utils.simple_functions import clip, fdiv

DEFAULT_DASH_LENGTH = 0.05

class Line(VItem):
    '''
    线段

    传入 `start`, `end` 为线段起点终点
    
    - `buff`: 线段两端的空余量，默认为 0
    - `path_arc`: 表示线段的弯曲角度
    '''
    def __init__(
        self,
        start: np.ndarray = LEFT,
        end: np.ndarray = RIGHT,
        buff: float = 0,
        path_arc: float = 0,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.start = start
        self.end = end
        self.buff = buff
        self.path_arc = path_arc

        self.set_points_by_ends(start, end, buff, path_arc)
    
    def set_points_by_ends(
        self,
        start: np.ndarray,
        end: np.ndarray,
        buff: float = 0,
        path_arc: float = 0
    ) -> Self:
        vect = end - start
        dist = get_norm(vect)
        if np.isclose(dist, 0):
            self.set_points_as_corners([start, end])
            return self
        if path_arc:
            neg = path_arc < 0
            if neg:
                path_arc = -path_arc
                start, end = end, start
            radius = (dist / 2) / np.sin(path_arc / 2)
            alpha = (PI - path_arc) / 2
            center = start + radius * normalize(rotate_vector(end - start, alpha))

            raw_arc_points = Arc.create_quadratic_bezier_points(
                angle=path_arc - 2 * buff / radius,
                start_angle=angle_of_vector(start - center) + buff / radius,
            )
            if neg:
                raw_arc_points = raw_arc_points[::-1]
            self.set_points(center + radius * raw_arc_points)
        else:
            if buff > 0 and dist > 0:
                start = start + vect * (buff / dist)
                end = end - vect * (buff / dist)
            self.set_points_as_corners([start, end])
        return self

    def set_path_arc(self, new_value: float) -> Self:
        self.path_arc = new_value
        self.set_points_by_ends(self.start, self.end, self.buff, self.path_arc)
        return self

    def set_start_and_end_attrs(self, start: np.ndarray, end: np.ndarray) -> None:
        # If either start or end are Items, this
        # gives their centers
        rough_start = self.pointify(start)
        rough_end = self.pointify(end)
        vect = normalize(rough_end - rough_start)
        # Now that we know the direction between them,
        # we can find the appropriate boundary point from
        # start and end, if they're items
        self.start = self.pointify(start, vect)
        self.end = self.pointify(end, -vect)

    def pointify(
        self,
        item_or_point: Item | np.ndarray,
        direction: np.ndarray | None = None
    ) -> np.ndarray:
        """
        Take an argument passed into Line (or subclass) and turn
        it into a 3d point.
        """
        if isinstance(item_or_point, Item):
            item = item_or_point
            if direction is None:
                return item.get_center()
            else:
                return item.get_continuous_bbox_point(direction)
        else:
            point = item_or_point
            result = np.zeros(3)
            result[:len(point)] = point
            return result

    def put_start_and_end_on(self, start: np.ndarray, end: np.ndarray) -> Self:
        '''将直线的首尾放在 `start`, `end` 上'''
        curr_start, curr_end = self.get_start_and_end()
        if np.isclose(curr_start, curr_end).all():
            # Handle null lines more gracefully
            self.set_points_by_ends(start, end, buff=0, path_arc=self.path_arc)
            return self
        return super().put_start_and_end_on(start, end)

    def get_vector(self) -> np.ndarray:
        '''获取直线的方向向量'''
        return self.get_end() - self.get_start()

    def get_unit_vector(self) -> np.ndarray:
        '''获取直线方向上的单位向量'''
        return normalize(self.get_vector())

    def get_angle(self) -> float:
        '''获取直线倾斜角'''
        return angle_of_vector(self.get_vector())

    def get_projection(self, point: np.ndarray) -> np.ndarray:
        '''返回点在直线上的投影'''
        unit_vect = self.get_unit_vector()
        start = self.get_start()
        return start + np.dot(point - start, unit_vect) * unit_vect

    def get_slope(self) -> float:
        '''获取直线斜率'''
        return np.tan(self.get_angle())

    def set_angle(self, angle: float, about_point: np.ndarray | None = None) -> Self:
        '''设置直线倾斜角为 `angle`'''
        if about_point is None:
            about_point = self.get_start()
        self.rotate(
            angle - self.get_angle(),
            about_point=about_point,
        )
        return self
    
    def get_length(self) -> float:
        return get_norm(self.get_vector())

    def set_length(self, length: float, **kwargs) -> Self:
        '''缩放到 `length` 长度'''
        self.scale(length / self.get_length(), False, **kwargs)
        return self

class DashedLine(Line):
    '''
    虚线

    - 使用了 `DahsedVItem` 进行创建
    - `dash_length`: 每段虚线的长度，默认为 0.05
    '''
    def __init__(
        self,
        *args,
        dash_length: float = DEFAULT_DASH_LENGTH,
        dash_spacing: float = None,
        positive_space_ratio: float = 0.5,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.dash_length = dash_length
        self.dash_spacing = dash_spacing

        num_dashes = self.calculate_num_dashes(positive_space_ratio)
        dashes = DashedVItem(
            self,
            num_dashes=num_dashes,
            positive_space_ratio=positive_space_ratio
        )
        self.clear_points()
        self.add(*dashes)

    def calculate_num_dashes(self, positive_space_ratio: float) -> int:
        try:
            full_length = self.dash_length / positive_space_ratio
            return int(np.ceil(self.get_length() / full_length))
        except ZeroDivisionError:
            return 1

    def calculate_positive_space_ratio(self) -> float:
        return fdiv(
            self.dash_length,
            self.dash_length + self.dash_spacing,
        )

    def get_start(self) -> np.ndarray:
        if len(self.items) > 0:
            return self.items[0].get_start()
        else:
            return super().get_start()

    def get_end(self) -> np.ndarray:
        if len(self.items) > 0:
            return self.items[-1].get_end()
        else:
            return super().get_end()

    def get_first_handle(self) -> np.ndarray:
        return self.items[0].get_points()[1]

    def get_last_handle(self) -> np.ndarray:
        return self.items[-1].get_points()[-2]

class TangentLine(Line):
    '''
    切线

    - 传入 `vitem` 表示需要做切线，`alpha` 表示切点在 `vitem` 上的比例
    - `length`: 切线长度
    - `d_alpha`: 精细程度，越小越精细（默认 1e-6）
    '''
    def __init__(
        self,
        vitem: VItem,
        alpha: float,
        length: float = 1,
        d_alpha: float = 1e-6,
        **kwargs
    ) -> None:
        a1 = clip(alpha - d_alpha, 0, 1)
        a2 = clip(alpha + d_alpha, 0, 1)
        super().__init__(vitem.pfp(a1), vitem.pfp(a2), **kwargs)
        self.scale(length / self.get_length())

class Elbow(VItem):
    '''
    折线（一般用作直角符号）

    - width 表示宽度
    - angle 表示角度
    '''
    def __init__(
        self,
        width: float = 0.2,
        angle: float = 0,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.set_points_as_corners([UP, UP + RIGHT, RIGHT])
        self.set_width(width, about_point=ORIGIN)
        self.rotate(angle, about_point=ORIGIN)

# TODO: [L] CubicBezier

