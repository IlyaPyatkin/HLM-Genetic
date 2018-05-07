from Geometry import Point
from Room import RoomMap
from config import *


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
                        map_[not_corner_walls[index][0] - 1][not_corner_walls[index][1]]["VerticalWall"] = (
                            "Transition", 0)
                    else:
                        map_[not_corner_walls[index][0]][not_corner_walls[index][1]]["HorizontalWall"] = ("Door", 1)
                        map_[not_corner_walls[index][0]][not_corner_walls[index][1] - 1]["HorizontalWall"] = (
                            "Transition", 1)
                else:
                    for wall in possible_doors:
                        if wall[2] == "Vertical":
                            map_[wall[0]][wall[1]]["VerticalWall"] = ("Transition", 0)
                            map_[wall[0] - 1][wall[1]]["VerticalWall"] = ("Transition", 0)
                        if wall[2] == "Horizontal":
                            map_[wall[0]][wall[1]]["HorizontalWall"] = ("Transition", 1)
                            map_[wall[0]][wall[1] - 1]["HorizontalWall"] = ("Transition", 1)

        start_tile = HotlineSerializer.place_entrance(map_, hero_position)
        start_tile.y -= 1
        return map_, start_tile

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
        map_[min_point.x][min_point.y - 1]["HorizontalWall"] = ("Transition", 1)
        return min_point

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
            for x in range(map_width):
                for y in range(map_height):
                    if "HorizontalWall" in map_[x][y]:
                        WallSerializer.write(f, map_[x][y]["HorizontalWall"], x, y)
                    if "VerticalWall" in map_[x][y]:
                        WallSerializer.write(f, map_[x][y]["VerticalWall"], x, y)

    @staticmethod
    def write(f, wall, x, y):
        if wall[0] == "Transition":
            return
        print(WallSerializer.objectKey[wall[0]][wall[1]], file=f)
        print(32 * x, file=f)
        print(32 * y, file=f)
        print(WallSerializer.spriteKey[wall[0]][wall[1]], file=f)
        print(0, file=f)


class TileSerializer:
    floor_tiles = []
    rug_tiles = []
    kitchen_tiles = []
    bathroom_tiles = []

    for i in range(12):
        for j in range(11):
            floor_tiles.append({
                "ObjectKey": 2,
                "Column": i * 16,
                "Row": j * 16,
            })

    for i in range(10):
        for j in range(8):
            bathroom_tiles.append({
                "ObjectKey": 5,
                "Column": i * 16,
                "Row": j * 16,
            })

    for i in range(12):
        for j in range(10):
            if j == 9 and i < 6:
                continue
            rug_tiles.append({
                "ObjectKey": 6,
                "Column": i * 16,
                "Row": j * 16,
            })

    for i in range(7):
        for j in range(11):
            if j == 10 and i < 2:
                continue
            kitchen_tiles.append({
                "ObjectKey": 7,
                "Column": i * 16,
                "Row": j * 16,
            })

    room_type_tiles = {
        "Storage": floor_tiles,
        "Corridor": rug_tiles,
        "Hall": floor_tiles,
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
        print(tile["Column"], file=f)
        print(tile["Row"], file=f)
        print(x, file=f)
        print(y, file=f)
        print("1001", file=f)

    @staticmethod
    def serialize(gene, path, _rng):
        rooms_tiles = RoomMap([rtc.room for rtc in gene]).get_rooms_tiles()
        with open(path, "w") as f:
            for chromosome in gene:
                if chromosome.room.index not in rooms_tiles:
                    continue
                tile = _rng.choice(TileSerializer.room_type_tiles[chromosome.room_type])
                for point in rooms_tiles[chromosome.room.index]:
                    TileSerializer.write(f, tile, point.x, point.y)


class EnemySerializer:
    @staticmethod
    def serialize(gene, path):
        enemy_types = {
            "fat": (2194, 1289),
            "dog": (1766, 1064),
            "dodger": (3973, 2286),
            "melee_static": (211, 230),
            "melee_patrol": (204, 941),
            "melee_random": (204, 170),
            "uzi_static": (208, 186),
            "uzi_patrol": (208, 184),
            "uzi_random": (208, 183),
            "9mm_static": (201, 186),
            "9mm_patrol": (201, 184),
            "9mm_random": (201, 183),
            "shotgun_static": (206, 186),
            "shotgun_patrol": (206, 184),
            "shotgun_random": (206, 183)
        }
        enemy_tiles = []
        with open(path, "a") as f:
            # Place the fans car at the lower right corner of the map
            f.write("1583\n933\n712\n392\n0\n236\n0\n")
            for chromosome in gene:
                for enemy in chromosome.enemies:
                    enemy_tiles.append(enemy[0])
                    EnemySerializer.write(f, enemy_types[enemy[1]], enemy[0].x, enemy[0].y)
        return enemy_tiles

    @staticmethod
    def write(f, enemy_type, x, y):
        print(10, file=f)
        print(32 * x + 16, file=f)
        print(32 * y + 16, file=f)
        print(enemy_type[0], file=f)
        print(270, file=f)
        print(enemy_type[1], file=f)
        print(0, file=f)
