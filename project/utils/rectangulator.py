from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Rect:
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        return self.x2 - self.x1 + 1

    @property
    def height(self) -> int:
        return self.y2 - self.y1 + 1

    @property
    def area(self) -> int:
        return self.width * self.height

    def touches(self, other) -> bool:
        """
        Check if this rectangle touches another rectangle (shares at least one edge).
        """
        horizontal_touch = (self.y2 + 1 == other.y1 or other.y2 + 1 == self.y1) and (
            self.x1 <= other.x2 and self.x2 >= other.x1
        )

        vertical_touch = (self.x2 + 1 == other.x1 or other.x2 + 1 == self.x1) and (
            self.y1 <= other.y2 and self.y2 >= other.y1
        )

        return horizontal_touch or vertical_touch


class Rectangulator:
    @staticmethod
    def find_max_rectangle(array: np.ndarray) -> Rect:
        n_rows, n_cols = array.shape
        max_area = 0
        best_rectangle = None

        for x1 in range(n_rows):
            for y1 in range(n_cols):
                if array[x1, y1] == 1:
                    for x2 in range(x1, n_rows):
                        if array[x2, y1] == 0:
                            break
                        for y2 in range(y1, n_cols):
                            if np.any(array[x1 : x2 + 1, y1 : y2 + 1] == 0):
                                break
                            area = (x2 - x1 + 1) * (y2 - y1 + 1)
                            if area > max_area:
                                max_area = area
                                best_rectangle = Rect(x1, y1, x2, y2)
        return best_rectangle

    @staticmethod
    def remove_rectangle(array: np.ndarray, rect: Rect) -> None:
        array[rect.x1 : rect.x2 + 1, rect.y1 : rect.y2 + 1] = 0

    def split_into_minimum_rectangles(self, array: np.ndarray) -> list[Rect]:
        rectangles = []
        array = array.copy()

        while np.any(array):
            rectangle = self.find_max_rectangle(array)
            if rectangle is None:
                break
            rectangles.append(rectangle)
            self.remove_rectangle(array, rectangle)

        return rectangles
