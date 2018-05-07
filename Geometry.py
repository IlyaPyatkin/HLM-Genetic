from functools import reduce


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @staticmethod
    def points_center(points):
        center = reduce(lambda p1, p2: Point(p1.x + p2.x, p1.y + p2.y), points)
        x = (center.x / len(points) + 0.5)
        y = (center.y / len(points) + 0.5)
        return Point(x, y)

    def square_distance(self, point):
        return abs(self.x - point.x) + abs(self.y - point.y)

    def __repr__(self):
        return "(%d:%d)" % (self.x, self.y)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class Rect:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.w = width
        self.h = height

    def crosses(self, rect):
        return (
            (rect.x < self.x and self.x + self.w < rect.x + rect.w and
             self.y <= rect.y and rect.y + rect.h <= self.y + self.h) or
            (rect.x <= self.x and self.x + self.w <= rect.x + rect.w and
             self.y < rect.y and rect.y + rect.h < self.y + self.h)
        )
