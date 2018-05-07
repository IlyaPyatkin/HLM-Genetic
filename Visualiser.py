import tkinter as tk

from Room import RoomsGraph, RoomMap
from config import *


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        self.WIDTH = 680
        self.HEIGHT = 480
        self._mapWidth = 34
        self._mapHeight = 24
        self.OFFSET = 2
        self.width_step = (self.WIDTH - self.OFFSET) / self._mapWidth
        self.height_step = (self.HEIGHT - self.OFFSET) / self._mapHeight

        self.w = tk.Canvas(master, width=self.WIDTH, height=self.HEIGHT)
        self.w.pack()

    def draw_wall(self, x, y, horizontal, color):
        width = int(self.height_step + self.width_step) // 8
        offset = width / 64
        if horizontal:
            p1 = (x, y)
            p2 = (x + 1, y)
        else:
            p1 = (x + offset, y - offset)
            p2 = (x + offset, y + 1 - offset)
        self.draw_line(p1, p2, width, fill=color)

    def draw_rooms(self, room_map):
        placed = room_map.rooms
        placed_under = reversed(list(filter(lambda x: x.position == "Under", placed)))
        placed_over = list(filter(lambda x: x.position == "Over", placed))
        colors = ["brown", "green", "grey", "violet", "cyan", "purple", "gold", "coral", "navy", "pink"]
        for rc in placed_under:
            self.draw_rect(rc.rect, colors[rc.index % 10])
        for rc in placed_over:
            self.draw_rect(rc.rect, colors[rc.index % 10])

    def draw_indexes(self, room_map):
        for x in range(map_width):
            for y in range(map_height):
                tile = room_map.map_[x][y]
                if tile != -1:
                    self.draw_index(x, y, tile)
        point_lists = [room_map.get_holes(),
                       room_map.get_narrow_corridors(),
                       room_map.get_tiny_corridors()]
        for j in range(len(point_lists)):
            for point in point_lists[j]:
                self.draw_index(point.x, point.y, '*' + str(j), "red")

    def draw_graph(self, room_map, gene):
        graph = RoomsGraph(gene)
        rooms_centers = room_map.get_rooms_centers()
        for room, center in rooms_centers.items():
            rooms_centers[room].x = center.x * self.width_step + self.OFFSET
            rooms_centers[room].y = center.y * self.height_step + self.OFFSET
        for room, center in rooms_centers.items():
            x = center.x
            y = center.y
            size = 3
            # self.w.create_oval(x - size, y - size, x + size, y + size, fill="black")
            self.w.create_text((x, y), text=room, font=("Purisa", 25))
        for from_room in graph.AdjMatrix:
            p1 = rooms_centers[from_room]
            for to_room in graph.AdjMatrix[from_room]:
                p2 = rooms_centers[to_room]
                self.w.create_line(p1.x, p1.y, p2.x, p2.y, width=2)

    def draw(self, gene):
        self.w.delete("all")
        room_map = RoomMap(gene)
        self.draw_rooms(room_map)
        self.draw_grid()
        # self.draw_indexes(room_map)
        self.draw_graph(room_map, gene)

    def draw_index(self, x, y, index, fill="black"):
        self.w.create_text(self.normalize((x, y)), text=index, fill=fill)

    def draw_grid(self):
        for i in range(self._mapWidth * 2):
            self.draw_line((i, 0), (i, self._mapHeight), rotation=1, fill="gray15")
        for i in range(self._mapHeight * 2):
            self.draw_line((0, i), (self._mapWidth, i), rotation=2, fill="gray15")

    def draw_line(self, from_, to, width=1, fill="black", rotation=1):
        self.w.create_line([self.normalize(from_, width, rotation),
                            self.normalize(to, width, rotation)],
                           tag='grid_line', width=width, fill=fill)

    def draw_rect(self, rect, color):
        self.w.create_rectangle(
            rect.x * self.width_step + self.OFFSET,
            rect.y * self.height_step + self.OFFSET,
            (rect.x + rect.w) * self.width_step + self.OFFSET,
            (rect.y + rect.h) * self.height_step + self.OFFSET,
            fill=color)

    def normalize(self, coords, width=0, rotation=0):
        if not rotation:
            x_offset = self.width_step / 2
            y_offset = self.height_step / 2
        else:
            x_offset = width / 2 * (rotation == 2)
            y_offset = width / 2 * (rotation == 1)
        return (coords[0] * self.width_step + self.OFFSET + x_offset,
                coords[1] * self.height_step + self.OFFSET + y_offset)
