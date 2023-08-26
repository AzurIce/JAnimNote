from __future__ import annotations

import numpy as np

from janim.constants import *
from janim.animation.animation import Animation
from janim.animation.transform import Transform

from janim.items.item import Item
from janim.items.geometry.arrow import Arrow


class GrowFromPoint(Transform):
    '''
    从指定的位置放大显现
    '''
    def __init__(self, item: Item, point: np.ndarray, **kwargs):
        self.point = point
        super().__init__(item, item, **kwargs)

    def begin(self) -> None:
        self.item_copy = self.item.copy().scale(0).move_to(self.point)
        super().begin()

class GrowFromCenter(GrowFromPoint):
    '''从物件的中心放大显现'''
    def __init__(self, item: Item, **kwargs):
        point = item.get_center()
        super().__init__(item, point, **kwargs)

class GrowFromEdge(GrowFromPoint):
    '''从物件的指定边角放大显现'''
    def __init__(self, item: Item, edge: np.ndarray, **kwargs):
        point = item.get_bbox_point(edge)
        super().__init__(item, point, **kwargs)


class GrowArrow(Animation):
    '''显示箭头的显现过程，从开头到结尾画出，并自动调整箭头标志位置'''
    def __init__(self, arrow: Arrow, **kwargs):
        self.arrow = arrow
        super().__init__(**kwargs)

    def begin(self) -> None:
        self.make_visible(self.arrow)
        self.arrow_copy = self.arrow.copy()
    
    def interpolate(self, alpha) -> None:
        self.arrow.pointwise_become_partial(self.arrow_copy, 0, alpha)
        self.arrow.place_tip()

    def finish(self) -> None:
        self.interpolate(1)


class SpinInFromNothing(GrowFromCenter):
    '''从物件的中心旋转半圈放大显现'''
    def __init__(self, item: Item, path_arc=PI, **kwargs):
        super().__init__(item, path_arc=path_arc, **kwargs)
