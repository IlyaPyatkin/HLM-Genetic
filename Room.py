from queue import Queue

from Geometry import Point
from config import *


class RoomMap:
    def __init__(self, gene):
        self.map_ = [[-1 for _ in range(map_height)] for _ in range(map_width)]
        self.rooms = []
        self.add_gene(gene)

    def add_gene(self, gene):
        for chromosome in gene:
            self.add_chromosome(chromosome)

    def add_chromosome(self, chromosome):
        if self.rooms and not self.overlaps(chromosome):
            return False
        for placed in self.rooms:
            if chromosome.rect.crosses(placed.rect):
                return False
            if placed.rect.crosses(chromosome.rect):
                return False
        self.add_to_map(chromosome, chromosome.index)
        self.rooms.append(chromosome)
        return True

    def add_to_map(self, chromosome, index):
        rect = chromosome.rect
        for x in range(rect.x, rect.x + rect.w):
            for y in range(rect.y, rect.y + rect.h):
                if self.map_[x][y] == -1 or chromosome.position == "Over":
                    self.map_[x][y] = index
        return True

    def overlaps(self, chromosome):
        rect = chromosome.rect
        overlaps = False
        visible = chromosome.position == "Over"
        for x in range(rect.x, rect.x + rect.w):
            for y in range(rect.y, rect.y + rect.h):
                if self.map_[x][y] != -1:
                    # finds the chromosome that is in [x][y](has index self.map_[x][y])
                    placed = next(c for c in self.rooms if c.index == self.map_[x][y])
                    if chromosome.connected[self.map_[x][y]] and placed.connected[chromosome.index]:
                        overlaps = True
                else:
                    visible = True
        return overlaps and visible

    def get_holes(self):
        holes = []
        for x in range(map_width):
            for y in range(map_height):
                if self.is_hole(x, y):
                    holes.append(Point(x, y))
        return holes

    # checks if the point is surrounded by tiles from all sides(not necessarily adjacent)
    def is_hole(self, x, y):
        if self.map_[x][y] != -1:
            return False
        for i in range(x, 0, -1):
            if self.map_[i][y] != -1:
                break
        else:
            return False
        for i in range(x, map_width):
            if self.map_[i][y] != -1:
                break
        else:
            return False
        for i in range(y, 0, -1):
            if self.map_[x][i] != -1:
                break
        else:
            return False
        for i in range(y, map_height):
            if self.map_[x][i] != -1:
                break
        else:
            return False
        return True

    # !looks ugly, should beautify
    def get_neighbours(self, x, y):
        # no check that (x,y) are valid coords
        points = []
        if x - 1 >= 0:
            points.append(Point(x - 1, y))
        if x + 1 < map_height:
            points.append(Point(x + 1, y))
        if y - 1 >= 0:
            points.append(Point(x, y - 1))
        if y + 1 < map_width:
            points.append(Point(x, y + 1))
        return points

    def get_room_number(self):
        return len(self.rooms)
        # return len(self.get_rooms_area())

    def get_building_area(self):
        return sum(self.get_rooms_area().values())

    def get_rooms_area(self):
        room_area = self.get_rooms_tiles()
        return {key: len(room_area[key]) for key in room_area}

    def get_rooms_tiles(self):
        room_area = {}
        for x in range(map_width):
            for y in range(map_height):
                tile = self.map_[x][y]
                if tile != -1:
                    if tile in room_area:
                        room_area[tile].append(Point(x, y))
                    else:
                        room_area[tile] = [Point(x, y)]
        return room_area

    def get_rooms_centers(self):
        rooms_tiles = self.get_rooms_tiles()
        return {room: Point.points_center(rooms_tiles[room]) for room in rooms_tiles}

    def get_narrow_corridors(self):
        result = []
        for x in range(map_width):
            for y in range(map_height):
                if self.map_[x][y] == -1:
                    continue
                if self.horizontally_narrow(x, y) != self.vertically_narrow(x, y):
                    result.append(Point(x, y))
        return result

    # basically a copypaste of the code above
    # also only true once in a millenia :/
    def get_tiny_corridors(self):
        result = []
        for x in range(map_width):
            for y in range(map_height):
                if self.map_[x][y] == -1:
                    continue
                if self.horizontally_narrow(x, y) and self.vertically_narrow(x, y):
                    result.append(Point(x, y))
        return result

    def vertically_narrow(self, x, y):
        return ((x == 0 or self.map_[x][y] != self.map_[x - 1][y]) and
                (x + 1 == len(self.map_) or self.map_[x][y] != self.map_[x + 1][y]))

    def horizontally_narrow(self, x, y):
        return ((y == 0 or self.map_[x][y] != self.map_[x][y - 1]) and
                (y + 1 == len(self.map_[0]) or self.map_[x][y] != self.map_[x][y + 1]))


class RoomsGraph:
    def __init__(self, gene):
        room_map = RoomMap(gene)
        self.AdjMatrix = {room.index: [] for room in room_map.rooms}
        map_ = room_map.map_
        for x in range(map_width):
            for y in range(map_height):
                if map_[x][y] == -1:
                    continue
                neighbours = room_map.get_neighbours(x, y)
                for neighbour in neighbours:
                    neighbour_index = map_[neighbour.x][neighbour.y]
                    cur_index = map_[x][y]
                    if neighbour_index != -1 and neighbour_index != cur_index:
                        if gene[cur_index].connected[neighbour_index] and \
                                gene[neighbour_index].connected[cur_index]:
                            self.add_edge(cur_index, neighbour_index)
                            self.add_edge(neighbour_index, cur_index)

    def add_edge(self, v1, v2):
        if v1 not in self.AdjMatrix:
            self.AdjMatrix[v1] = []
        if v2 not in self.AdjMatrix[v1]:
            self.AdjMatrix[v1].append(v2)

    def connected(self):
        if not self.AdjMatrix:
            return True
        distance_map = self.get_distance_map(list(self.AdjMatrix)[0])
        for vertex in self.AdjMatrix:
            if distance_map[vertex] == -1:
                return False
        return True

    def average_degree(self):
        result = 0
        n = len(self.AdjMatrix)
        for vertex in self.AdjMatrix:
            result += len(self.AdjMatrix[vertex]) / n
        return result

    def get_distance_map(self, start, rooms_centers=None):
        distance = {v: -1 for v in self.AdjMatrix}
        distance[start] = 0
        queue = Queue()
        queue.put(start)
        while queue.qsize() != 0:
            v = queue.get()
            for i in self.AdjMatrix[v]:
                if distance[i] == -1:
                    weight = 1
                    if rooms_centers:
                        weight = rooms_centers[i].square_distance(rooms_centers[v])
                    distance[i] = distance[v] + weight
                    queue.put(i)
        return distance

    def get_diameter(self):
        diameter = 0
        for v in self.AdjMatrix:
            max_distance = max(self.get_distance_map(v).values())
            diameter = max(max_distance, diameter)
        return diameter
