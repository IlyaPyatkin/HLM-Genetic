from Geometry import Rect
from config import *


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
        types = ["Kitchen", "Bathroom", "Storage", "Hall", "Corridor"]
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
    def __init__(self, index, room_tiles, enemies):
        self.index = index
        self.room_tiles = room_tiles
        self.enemies = enemies

    @staticmethod
    def generate(_rng, index, room_tiles):
        enemy_types = ["fat", "dog", "dodger", "melee_static",
                       "melee_patrol", "melee_random", "uzi_static", "uzi_patrol",
                       "uzi_random", "9mm_static", "9mm_patrol", "9mm_random",
                       "shotgun_static", "shotgun_patrol", "shotgun_random"]
        tiles = _rng.sample(room_tiles, _rng.randrange(min(12, len(room_tiles))))
        enemies = [(tile, _rng.choice(enemy_types)) for tile in tiles]
        return EnemyChromosome(index, room_tiles, enemies)

    @staticmethod
    def generate_gene(_rng, rooms_tiles, rooms_by_distance, occ_tiles):
        for room in rooms_tiles:
            rooms_tiles[room] = [tile for tile in rooms_tiles[room] if tile not in occ_tiles]
        return [EnemyChromosome.generate(_rng, rooms_by_distance.index(room),
                                         rooms_tiles[room]) for room in rooms_tiles]

    @staticmethod
    def mutate(_rng, gene):
        index = _rng.randrange(len(gene))
        gene[index] = EnemyChromosome.generate(_rng, gene[index].index, gene[index].room_tiles)
        return gene
