import random
import tkinter as tk
from functools import reduce
from math import exp, pow, log, e
from queue import Queue
from abc import ABC, abstractmethod

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
        width = (self.height_step + self.width_step) / 8
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

    def points_center(self, points):
        center = reduce(lambda p1, p2: Point(p1.x + p2.x, p1.y + p2.y), points)
        x = (center.x / len(points) + 0.5) * self.width_step + self.OFFSET
        y = (center.y / len(points) + 0.5) * self.height_step + self.OFFSET
        return x, y

    def draw_graph(self, room_map, gene):
        graph = Graph(gene)
        rooms_tiles = room_map.get_rooms_tiles()
        rooms_centers = {room: self.points_center(rooms_tiles[room]) for room in rooms_tiles}
        for center in rooms_centers.values():
            x = center[0]
            y = center[1]
            size = 3
            self.w.create_oval(x - size, y - size, x + size, y + size, fill="black")
        for from_room in graph.AdjMatrix:
            p1 = rooms_centers[from_room]
            for to_room in graph.AdjMatrix[from_room]:
                p2 = rooms_centers[to_room]
                self.w.create_line(p1[0], p1[1], p2[0], p2[1], width=1)

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


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return "(%d:%d)" % (self.x, self.y)


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


class GeneticAlgorithm:
    def __init__(self, mutator, breeder, fitness, initial, _rng):
        self.mutator = mutator
        self.breeder = breeder
        self.fitness = fitness
        self.initial = initial
        self._rng = _rng
        self._population = None

    def compute(self, steps):
        self._population = [(x, self.fitness(x)) for x in self.initial]

        if self.fitness == Fitness.mixed_room_fitness:
            app = Application(master=tk.Tk())

        for i in range(steps):
            self.sort_by_fitness()

            if debug_output:
                print("%02d/%d" % (i, steps), end=" ")
                print(["{0:0.2f}".format(x[1]) for x in self._population])

            if self.fitness == Fitness.mixed_room_fitness:
                app.draw(self._population[0][0])
                app.update()

            self.step()
        if self.fitness == Fitness.mixed_room_fitness:
            app.master.destroy()
        self.sort_by_fitness()
        return self._population[0][0]

    def sort_by_fitness(self):
        self._population = sorted(self._population, key=lambda x: (-x[1]))

    def step(self):
        for i in range(2, len(self._population)):
            new_gene = self.breeder(self._rng, self._population[0][0], self._population[1][0])
            mutated_gene = self.mutator(self._rng, new_gene)
            self._population[i] = (mutated_gene, self.fitness(mutated_gene))

    # Randomly mixes two genes
    @staticmethod
    def uniform_crossover(_rng, gene1, gene2):
        if len(gene1) < len(gene2):
            gene1, gene2 = gene2, gene1
        gene = []
        for i in range(len(gene2)):
            gene.append(_rng.choice([gene1[i], gene2[i]]))
        for i in range(len(gene2), len(gene1)):
            if _rng.choice([True, False]):
                gene.append(gene1[i])
        return gene

    # Splits two genes at some point and then connects two parts of both into one gene
    @staticmethod
    def one_point_crossover(_rng, gene1, gene2):
        if len(gene1) < len(gene2):
            gene1, gene2 = gene2, gene1
        split_point = _rng.randrange(len(gene2) + 1)
        gene = gene2[:split_point] + gene1[split_point:]
        return gene


class RoomChromosome:
    def __init__(self, index, rect, position, connected):
        self.index = index
        self.rect = rect
        self.position = position
        self.connected = connected

    @staticmethod
    def generate(_rng, index, gene_length):
        x = _rng.randrange(1, map_width - min_room_size - 2)
        y = _rng.randrange(1, map_height - min_room_size - 2)
        width = _rng.randrange(min_room_size, min(map_width - x, max_room_size + 1))
        height = _rng.randrange(min_room_size, min(map_height - y, max_room_size + 1))
        rect = Rect(x, y, width, height)
        position = _rng.choice(["Over", "Under"])
        connected = _rng.choices([True, False], k=gene_length)
        return RoomChromosome(index, rect, position, connected)

    @staticmethod
    def generate_gene(_rng, gene_length):
        return [RoomChromosome.generate(_rng, i, gene_length) for i in range(gene_length)]

    # Replaces random chromosome in a gene
    @staticmethod
    def mutate(_rng, gene):
        index = _rng.randrange(len(gene))
        gene[index] = RoomChromosome.generate(_rng, index, len(gene))
        return gene


class RoomTypeChromosome:
    def __init__(self, room, room_type):
        self.room = room
        self.room_type = room_type

    @staticmethod
    def generate(_rng, room):
        types = ["Kitchen", "Bathroom", "Closet", "Hall", "Corridor"]
        room_type = _rng.choice(types)
        return RoomTypeChromosome(room, room_type)

    @staticmethod
    def generate_gene(_rng, gene):
        return [RoomTypeChromosome.generate(_rng, room) for room in gene]

    @staticmethod
    def mutate(_rng, gene):
        index = _rng.randrange(len(gene))
        gene[index] = RoomTypeChromosome.generate(_rng, gene[index].room)
        return gene


class EnemyChromosome:
    def __init__(self, room, room_tiles, enemies):
        self.room = room
        self.room_tiles = room_tiles
        self.enemies = enemies

    @staticmethod
    def generate(_rng, room, room_tiles):
        tiles = _rng.sample(room_tiles, rng.randrange(min(6, len(room_tiles))))
        enemies = [(tile, _rng.randrange(8)) for tile in tiles]
        return EnemyChromosome(room, room_tiles, enemies)

    @staticmethod
    def generate_gene(_rng, gene):
        rooms_tiles = RoomMap(gene).get_rooms_tiles()
        return [EnemyChromosome.generate(_rng, gene[room], rooms_tiles[room]) for room in rooms_tiles]

    @staticmethod
    def mutate(_rng, gene):
        index = _rng.randrange(len(gene))
        gene[index] = EnemyChromosome.generate(_rng, gene[index], gene[index].room_tiles)
        return gene


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


class Graph:
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

    def get_distance_map(self, start):
        distance = {v: -1 for v in self.AdjMatrix}
        distance[start] = 0
        queue = Queue()
        queue.put(start)
        while queue.qsize() != 0:
            v = queue.get()
            for i in self.AdjMatrix[v]:
                if distance[i] == -1:
                    distance[i] = distance[v] + 1
                    queue.put(i)
        return distance

    def get_diameter(self):
        diameter = 0
        for v in self.AdjMatrix:
            max_distance = max(self.get_distance_map(v).values())
            diameter = max(max_distance, diameter)
        return diameter


class Fitness:
    @staticmethod
    def mixed_room_fitness(gene):
        room_map = RoomMap(gene)
        rooms = room_map.get_room_number()
        if rooms == 1:
            return -1000
        narrow_corridors = len(room_map.get_narrow_corridors())
        tiny_rooms = len(room_map.get_tiny_corridors())
        building_area = room_map.get_building_area()
        holes = len(room_map.get_holes())
        graph = Graph(gene)
        if not graph.connected():
            return -1000
        avg_degree = graph.average_degree()
        diameter = graph.get_diameter()
        exp_diameter = exp(-(diameter - 3.0) * (diameter - 3.0))
        exp_degree = exp(-(avg_degree - 2.0) * (avg_degree - 2.0))

        # return (exp_degree * rooms * log(diameter)) / (log(e + narrow_corridors) * pow(10.0, tiny_rooms))
        return ((exp_degree * rooms * exp_diameter) /
                (log(e + narrow_corridors) * pow(10.0, tiny_rooms)) +
                building_area / 25.0 - 100 * holes)


    @staticmethod
    def room_type_fitness(gene):
        rooms_gene = [rtc.room for rtc in gene]
        rooms_area = RoomMap(rooms_gene).get_rooms_area()
        graph = Graph(rooms_gene)
        fitness = 1.0
        for key in graph.AdjMatrix:
            if gene[key].room_type == "Corridor":
                connected_rooms_types = [gene[i].room_type for i in graph.AdjMatrix[key]]
                if "Bathroom" in connected_rooms_types:
                    fitness += 10
                if "Kitchen" in connected_rooms_types:
                    fitness += 10
                fitness += 100 * len(graph.AdjMatrix[key])

            if gene[key].room_type == "Hall":
                connected_rooms_types = [gene[i].room_type for i in graph.AdjMatrix[key]]
                if "Closet" in connected_rooms_types:
                    fitness += 10
                if "Bathroom" in connected_rooms_types:
                    fitness += 10
                if "Kitchen" in connected_rooms_types:
                    fitness += 10
                if rooms_area[key] > 20:
                    fitness += 1000

            if gene[key].room_type == "Kitchen":
                connected_rooms_types = [gene[i].room_type for i in graph.AdjMatrix[key]]
                if "Closet" in connected_rooms_types:
                    fitness += 10
                if "Bathroom" in connected_rooms_types:
                    fitness += 10
                if 15 < rooms_area[key] < 30:
                    fitness += 1000

            if gene[key].room_type == "Bathroom":
                if rooms_area[key] < 15:
                    fitness += 1000
                if len(graph.AdjMatrix[key]) == 1:
                    fitness += 1000
            if gene[key].room_type == "Closet":
                if rooms_area[key] < 10:
                    fitness += 1000
        return fitness

    @staticmethod
    def enemy_fitness(gene):
        return 10


class HotlineSerializer:
    @staticmethod
    def to_map(gene, hero_position, _rng):
        map_ = [[{} for _ in range(map_height)] for _ in range(map_width)]
        room_map = RoomMap(gene)
        for i in range(len(gene)):
            HotlineSerializer.fill_wall(room_map, i, map_)

        for i in range(len(gene)):
            for j in range(i + 1, len(gene)):
                if not gene[j].connected[i] or not gene[i].connected[j]:
                    continue
                possible_doors = HotlineSerializer.get_possible_doors(room_map, i, j)
                not_corner_walls = list(filter(lambda x: not x[3], possible_doors))
                if not_corner_walls:
                    index = _rng.randrange(len(not_corner_walls))
                    if not_corner_walls[index][2] == "Vertical":
                        map_[not_corner_walls[index][0]][not_corner_walls[index][1]]["VerticalWall"] = ("Door", 0)
                    else:
                        map_[not_corner_walls[index][0]][not_corner_walls[index][1]]["HorizontalWall"] = ("Door", 1)
                else:
                    for wall in possible_doors:
                        if wall[2] == "Horizontal":
                            map_[wall[0]][wall[1]].pop("HorizontalWall", None)
                        if wall[2] == "Vertical":
                            map_[wall[0]][wall[1]].pop("VerticalWall", None)
        HotlineSerializer.place_entrance(map_, hero_position)
        return map_

    @staticmethod
    def place_entrance(map_, hero_position):
        min_distance = 10000
        min_point = Point(-1, -1)
        for x in range(map_width):
            for y in range(map_height):
                if "HorizontalWall" in map_[x][y] and \
                                "VerticalWall" not in map_[x][y - 1] and \
                                "VerticalWall" not in map_[x + 1][y - 1]:
                    distance = abs(x - hero_position.x) + abs(y - hero_position.y)
                    if distance < min_distance:
                        min_distance = distance
                        min_point = Point(x, y)
        map_[min_point.x][min_point.y]["HorizontalWall"] = ("Door", 1)

    @staticmethod
    def fill_wall(room_map, i, map_):
        for x in range(map_width):
            for y in range(map_height):
                if room_map.map_[x][y] == i:
                    if x == 0 or room_map.map_[x - 1][y] != i:
                        map_[x][y]["VerticalWall"] = ("Standard", 0)
                    if y == 0 or room_map.map_[x][y - 1] != i:
                        map_[x][y]["HorizontalWall"] = ("Standard", 1)
                    if x == 0 or room_map.map_[x - 1][y] == -1:
                        map_[x][y]["VerticalWall"] = ("RedBrick", 0)
                    if y == 0 or room_map.map_[x][y - 1] == -1:
                        map_[x][y]["HorizontalWall"] = ("RedBrick", 1)
                if y + 1 < map_height and room_map.map_[x][y] == i and room_map.map_[x][y + 1] == -1:
                    map_[x][y + 1]["HorizontalWall"] = ("RedBrick", 1)
                if x + 1 < map_width and room_map.map_[x][y] == i and room_map.map_[x + 1][y] == -1:
                    map_[x + 1][y]["VerticalWall"] = ("RedBrick", 0)

    @staticmethod
    def get_possible_doors(room_map, room1, room2):
        result = []
        for x in range(map_width):
            for y in range(map_height):
                if x > 0 and room_map.map_[x][y] == room1 and room_map.map_[x - 1][y] == room2:
                    is_corner = HotlineSerializer.is_vertical_corner(room_map, x, y, x - 1, y)
                    result.append((x, y, "Vertical", is_corner))
                if x + 1 < map_width and room_map.map_[x][y] == room1 and room_map.map_[x + 1][y] == room2:
                    is_corner = HotlineSerializer.is_vertical_corner(room_map, x, y, x + 1, y)
                    result.append((x + 1, y, "Vertical", is_corner))
                if y > 0 and room_map.map_[x][y] == room1 and room_map.map_[x][y - 1] == room2:
                    is_corner = HotlineSerializer.is_horizontal_corner(room_map, x, y, x, y - 1)
                    result.append((x, y, "Horizontal", is_corner))
                if y + 1 < map_height and room_map.map_[x][y] == room1 and room_map.map_[x][y + 1] == room2:
                    is_corner = HotlineSerializer.is_horizontal_corner(room_map, x, y, x, y + 1)
                    result.append((x, y + 1, "Horizontal", is_corner))
        return result

    @staticmethod
    def is_horizontal_corner(room_map, xtop, ytop, xbot, ybot):
        if xtop == 0 or room_map.map_[xtop][ytop] != room_map.map_[xtop - 1][ytop]:
            return True
        if xtop == map_width - 1 or room_map.map_[xtop][ytop] != room_map.map_[xtop + 1][ytop]:
            return True
        if xbot == 0 or room_map.map_[xbot][ybot] != room_map.map_[xbot - 1][ybot]:
            return True
        if xbot == map_width - 1 or room_map.map_[xbot][ybot] != room_map.map_[xbot + 1][ybot]:
            return True
        return False

    @staticmethod
    def is_vertical_corner(room_map, xtop, ytop, xbot, ybot):
        if ytop == 0 or room_map.map_[xtop][ytop] != room_map.map_[xtop][ytop - 1]:
            return True
        if ytop == map_height - 1 or room_map.map_[xtop][ytop] != room_map.map_[xtop][ytop + 1]:
            return True
        if ybot == 0 or room_map.map_[xbot][ybot] != room_map.map_[xbot][ybot - 1]:
            return True
        if ybot == map_height - 1 or room_map.map_[xbot][ybot] != room_map.map_[xbot][ybot + 1]:
            return True
        return False


class TileSerializer:
    floor_tiles = []
    rug_tiles = []
    kitchen_tiles = []
    bathroom_tiles = []

    # i can be 0
    for i in range(3, 12):
        for j in range(6, 12):
            floor_tiles.append({
                "ObjectKey": 2,
                "Column": j * 16,
                "Row": i * 16,
                "Z": 1001
            })

    for i in range(10):
        for j in range(10):
            rug_tiles.append({
                "ObjectKey": 6,
                "Column": j * 16,
                "Row": i * 16,
                "Z": 1001
            })

    for i in range(8):
        for j in range(7):
            if 4 <= j <= 5:
                continue
            kitchen_tiles.append({
                "ObjectKey": 7,
                "Column": j * 16,
                "Row": i * 16,
                "Z": 1001
            })

    for i in range(7):
        for j in range(7):
            bathroom_tiles.append({
                "ObjectKey": 5,
                "Column": j * 16,
                "Row": i * 16,
                "Z": 1001
            })

    room_type_tiles = {
        "Closet": floor_tiles,
        "Corridor": floor_tiles,
        "Hall": rug_tiles,
        "Kitchen": kitchen_tiles,
        "Bathroom": bathroom_tiles
    }

    @staticmethod
    def write(f, tile, x, y):
        TileSerializer.write_tile(f, tile, x * 32, y * 32)
        TileSerializer.write_tile(f, tile, x * 32 + 16, y * 32)
        TileSerializer.write_tile(f, tile, x * 32, y * 32 + 16)
        TileSerializer.write_tile(f, tile, x * 32 + 16, y * 32 + 16)

    @staticmethod
    def write_tile(f, tile, x, y):
        print(tile["ObjectKey"], file=f)
        print(tile["Row"], file=f)
        print(tile["Column"], file=f)
        print(x, file=f)
        print(y, file=f)
        print(tile["Z"], file=f)

    @staticmethod
    def serialize(gene, path, _rng):
        rooms_tiles = RoomMap([rtc.room for rtc in gene]).get_rooms_tiles()
        with open(path, "w") as f:
            for room in rooms_tiles:
                tile = _rng.choice(TileSerializer.kitchen_tiles)
                for point in rooms_tiles[room]:
                    TileSerializer.write(f, tile, point.x, point.y)


class WallSerializer:
    spriteKey = {"RedBrick": (100, 99),
                 "Standard": (63, 62),
                 "Door": (91, 92)}
    objectKey = {"RedBrick": (31, 32),
                 "Standard": (8, 7),
                 "Door": (25, 26)}

    @staticmethod
    def serialize(map_, path):
        with open(path, "w") as f:
            for x in range(len(map_)):
                for y in range(len(map_[0])):
                    if "HorizontalWall" in map_[x][y]:
                        WallSerializer.write(f, map_[x][y]["HorizontalWall"], x, y)
                    if "VerticalWall" in map_[x][y]:
                        WallSerializer.write(f, map_[x][y]["VerticalWall"], x, y)

    @staticmethod
    def write(f, wall, x, y):
        print(WallSerializer.objectKey[wall[0]][wall[1]], file=f)
        print(32 * x, file=f)
        print(32 * y, file=f)
        print(WallSerializer.spriteKey[wall[0]][wall[1]], file=f)
        print(0, file=f)


class EnemySerializer:
    @staticmethod
    def serialize2(gene, path, _rng):
        result = []
        with open(path, "w") as f:
            f.write("1583\n933\n712\n392\n0\n236\n0\n")
            for chromosome in gene:
                for enemy in chromosome.enemies:
                    result.append(enemy[0])
                    enemy_type = _rng.choice([(208, 186), (201, 183)])
                    EnemySerializer.write(f, enemy_type, enemy[0].x, enemy[0].y)
        return result

    @staticmethod
    def serialize(gene, path, _rng):
        result = []
        with open(path, "w") as f:
            # Place the fans car at the lower right corner of the map
            f.write("1583\n933\n712\n392\n0\n236\n0\n")
            rooms_tiles = RoomMap(gene).get_rooms_tiles()
            for room_tiles in rooms_tiles.values():
                enemies = _rng.randrange(3)
                if len(room_tiles) >= 30:
                    enemies += 1
                if len(room_tiles) >= 60:
                    enemies += 1

                for i in range(enemies):
                    point = _rng.choice(room_tiles)
                    result.append(point)
                    enemy_type = _rng.choice([(208, 186), (201, 183)])
                    EnemySerializer.write(f, enemy_type, point.x, point.y)
        return result

    @staticmethod
    def write(f, enemy_type, x, y):
        print(10, file=f)
        print(32 * x + 16, file=f)
        print(32 * y + 16, file=f)
        print(enemy_type[0], file=f)
        print(0, file=f)
        print(enemy_type[1], file=f)
        print(0, file=f)


if __name__ == '__main__':
    if random_seed:
        seed = random.randrange(100000000)
    print("Seed:", seed)
    rng = random.Random(seed)

    # Run GA to generate rooms
    room_ga = GeneticAlgorithm(
        breeder=GeneticAlgorithm.one_point_crossover,
        mutator=RoomChromosome.mutate,
        initial=[RoomChromosome.generate_gene(rng, gene_length) for _ in range(population_size)],
        fitness=Fitness.mixed_room_fitness,
        _rng=rng
    )
    rooms_dominant = room_ga.compute(iterations)

    # Run GA to generate room types
    room_type_ga = GeneticAlgorithm(
        breeder=GeneticAlgorithm.uniform_crossover,
        mutator=RoomTypeChromosome.mutate,
        initial=[RoomTypeChromosome.generate_gene(rng, rooms_dominant) for _ in range(population_size)],
        fitness=Fitness.room_type_fitness,
        _rng=rng
    )
    room_types_dominant = room_type_ga.compute(int(iterations / 4))

    # Run GA to generate enemies
    enemies_ga = GeneticAlgorithm(
        breeder=GeneticAlgorithm.uniform_crossover,
        mutator=EnemyChromosome.mutate,
        initial=[EnemyChromosome.generate_gene(rng, rooms_dominant) for _ in range(population_size)],
        fitness=Fitness.enemy_fitness,
        _rng=rng
    )
    enemies_dominant = enemies_ga.compute(iterations)

    # Serialize the level and save it
    if not os.path.isdir(hl2_path):
        print("Could not find the HL2 levels folder at:")
        print(hl2_path)
        exit(1)
    if not os.path.isdir(level_path):
        os.makedirs(level_path)
    hotline_map = HotlineSerializer.to_map(rooms_dominant, Point(20, 25), rng)
    WallSerializer.serialize(hotline_map, walls_path)
    TileSerializer.serialize(room_types_dominant, tiles_path, rng)
    # enemies = EnemySerializer.serialize(rooms_dominant, objects_path, rng)
    enemies = EnemySerializer.serialize2(enemies_dominant, objects_path, rng)

    app = Application(master=tk.Tk())
    app.draw(rooms_dominant)
    colors = {"Door": "black", "Standard": "bisque3", "RedBrick": "red4"}
    for x in range(map_width):
        for y in range(map_height):
            if "HorizontalWall" in hotline_map[x][y]:
                app.draw_wall(x, y, 1, colors[hotline_map[x][y]["HorizontalWall"][0]])
            if "VerticalWall" in hotline_map[x][y]:
                app.draw_wall(x, y, 0, colors[hotline_map[x][y]["VerticalWall"][0]])
    for e in enemies:
        app.draw_index(e.x, e.y, "E")
    app.mainloop()
