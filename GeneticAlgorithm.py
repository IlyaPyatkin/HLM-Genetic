import tkinter as tk
from math import exp, pow, log, e

from Room import RoomMap, RoomsGraph
from Visualiser import Application
from config import *


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
        graph = RoomsGraph(gene)
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
        graph = RoomsGraph(rooms_gene)
        fitness = 0
        for key in graph.AdjMatrix:
            connected_rooms_types = [gene[i].room_type for i in graph.AdjMatrix[key]]
            room_area = rooms_area[key]
            room_connections = len(graph.AdjMatrix[key])
            room_type = gene[key].room_type
            if room_type == "Corridor":
                if "Bathroom" in connected_rooms_types:
                    fitness += 10
                if "Kitchen" in connected_rooms_types:
                    fitness += 10
                fitness += 500 * room_connections

            if room_type == "Hall":
                if "Storage" in connected_rooms_types:
                    fitness += 10
                if "Bathroom" in connected_rooms_types:
                    fitness += 10
                if "Kitchen" in connected_rooms_types:
                    fitness += 10
                if room_area > 20:
                    fitness += 1000

            if room_type == "Kitchen":
                if "Storage" in connected_rooms_types:
                    fitness += 10
                if "Bathroom" in connected_rooms_types:
                    fitness += 10
                if 15 < room_area < 30:
                    fitness += 1000

            if room_type == "Bathroom":
                if room_area < 15:
                    fitness += 1000
                if room_connections == 1:
                    fitness += 1000
            if room_type == "Storage":
                if room_area < 10:
                    fitness += 1000
        return fitness

    @staticmethod
    def enemy_fitness(gene):
        enemy_types_weights = {
            "fat": 100,
            "dog": 40,
            "dodger": 80,
            "melee_static": 10,
            "melee_patrol": 15,
            "melee_random": 15,
            "uzi_static": 30,
            "uzi_patrol": 35,
            "uzi_random": 35,
            "9mm_static": 20,
            "9mm_patrol": 25,
            "9mm_random": 25,
            "shotgun_static": 30,
            "shotgun_patrol": 35,
            "shotgun_random": 35
        }
        fitness = 0

        for chromosome in gene:
            room_difficulty = len(chromosome.enemies) * len(chromosome.enemies)
            for enemy in chromosome.enemies:
                room_difficulty += enemy_types_weights[enemy[1]]

            room_set_difficulty = difficulty * (len(chromosome.room_tiles) / average_room_area) * log(
                chromosome.index + 4, 4)
            fitness -= abs(room_set_difficulty - room_difficulty)
        return fitness
