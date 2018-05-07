from Geometry import Point


class FurnitureGenerator:
    # angle of rotation, and vector of direction
    angles = {
        "right": {"direction": (-1, 0), "angle": 0, "direction2": (0, 1)},
        "up": {"direction": (0, 1), "angle": 90, "direction2": (1, 0)},
        "left": {"direction": (1, 0), "angle": 180, "direction2": (0, -1)},
        "down": {"direction": (0, -1), "angle": 270, "direction2": (-1, 0)},
    }

    # ((object ID, sprite ID), rotated, size, variations)
    objects = {
        "Kitchen": [
            ((3449, 2012), 0, 1, 2),
            ((147, 72), 0, 1, 2),
            ((125, 71), 0, 1, 4),
            ((3455, 2018), 1, 0, 2)
        ],
        "Bathroom": [
            ((247, 134), 1, 1, 2),
            ((1356, 836), 0, 2, 2),
            ((148, 73), 1, 1, 2)
        ],
        "Storage": [
            ((402, 244), 0, 1, 2),
            ((1867, 1096), 0, 1, 6),
            ((190, 109), 0, 1, 1)
        ],
        "Hall": [
            ((221, 114), 0, 3, 1),
            ((3303, 1901), 1, 2, 1),
            ((2075, 1210), 0, 3, 2),
            ((2111, 1233), 0, 0, 2),
            ((3195, 1838), 1, 3, 1)
        ]
    }

    @staticmethod
    def is_door_tile(hotline_map, tile):
        for i in range(tile[0] - 1, tile[0] + 2):
            for j in range(tile[1] - 1, tile[1] + 2):
                for key, val in hotline_map[i][j].items():
                    if val[0] == 'Door' or val[0] == 'Transition':
                        return True
        return False

    # get wall tiles, but not near door
    # ind - show dimension of borders. 0 - vertical, 1 - horizontal
    # angles - shows 'direction' of wall
    @staticmethod
    def get_borders(hotline_map, arr, coord_index, directions):
        # sort by one of the dimensions
        arr = sorted(arr, key=lambda tile: tile[coord_index])
        # init array of borders
        borders = []
        prev = arr[0]
        if not FurnitureGenerator.is_door_tile(hotline_map, prev):
            borders += [(prev, directions[0])]
        for tile in arr:
            if prev[coord_index] != tile[coord_index]:
                if not FurnitureGenerator.is_door_tile(hotline_map, prev):
                    borders += [(prev, directions[1])]
                if not FurnitureGenerator.is_door_tile(hotline_map, tile):
                    borders += [(tile, directions[0])]
            prev = tile
        if not FurnitureGenerator.is_door_tile(hotline_map, prev):
            borders += [(prev, directions[1])]
        return borders

    @staticmethod
    def get_center_tiles(room_tiles):
        result = []
        for tile in room_tiles:
            center = True
            for x in range(-3, 3):
                for y in range(-3, 3):
                    if (tile[0] + x, tile[1] + y) not in room_tiles:
                        center = False
                        break
                if not center:
                    break
            if center:
                result += [tile]
        return result

    @staticmethod
    def split_walls_corners(a, b):
        a_set = set([x[0] for x in a])
        b_set = set([x[0] for x in b])
        corners = a_set & b_set
        corner_tiles = [x for x in a if x[0] in corners] + [x for x in b if x[0] in corners]
        a_no = [x for x in a if x[0] not in corners]
        b_no = [x for x in b if x[0] not in corners]
        return a_no, b_no, corner_tiles

    @staticmethod
    def place_objects(rng, hotline_map, rooms_types, rooms_tiles, path):
        occupied_tiles = []
        with open(path, "w") as f:
            for room, tiles in rooms_tiles.items():
                if rooms_types[room] == "Corridor":
                    continue
                tiles_tuples = [(tile.x, tile.y) for tile in tiles]

                center_tiles = FurnitureGenerator.get_center_tiles(tiles_tuples)
                borders_x = FurnitureGenerator.get_borders(hotline_map, tiles_tuples, 0, ("right", "left"))
                borders_y = FurnitureGenerator.get_borders(hotline_map, tiles_tuples, 1, ("up", "down"))
                walls_x, walls_y, corners = FurnitureGenerator.split_walls_corners(borders_x, borders_y)
                borders = walls_x + walls_y

                occupied_tiles += FurnitureGenerator.place_objects2(f, rng, borders, center_tiles,
                                                                    FurnitureGenerator.objects[rooms_types[room]])

                # if center_tiles and rng.randrange(10) < 6:
                #     occupied_tiles += FurnitureGenerator.place_billiard(rng, center_tiles, f)
                # if corners and rng.randrange(10) < 4:
                #     occupied_tiles += FurnitureGenerator.place_tv_spot(rng, walls + corners, f, tiles_tuples)
                # if walls and rng.randrange(10) < 8:
                #     occupied_tiles += FurnitureGenerator.place_bookshelf(rng, walls, f)

        return occupied_tiles

    @staticmethod
    def place_objects2(f, rng, borders, center_tiles, objects):
        occupied_tiles = []
        extra_occupied = []
        for obj in objects:
            borders = [border for border in borders if
                       border[0] not in occupied_tiles and border[0] not in extra_occupied]
            obj_type, obj_rotated, obj_size, obj_variations = obj
            if obj_size == 0:
                if center_tiles:
                    x, y = rng.choice(center_tiles)
                    FurnitureGenerator.write(f, x, y, obj_type, 90 * rng.randrange(2), rng.randrange(obj_variations))
                    occupied_tiles.append((x, y))
                    for i in range(3):
                        for j in range(3):
                            occupied_tiles.append((x + i - 1, y + j - 1))
            else:
                if borders:
                    border = rng.choice(borders)
                    borders.remove(border)
                    (x, y), angle = border
                    x_dir, y_dir = FurnitureGenerator.angles[angle]['direction']
                    x_dir2, y_dir2 = FurnitureGenerator.angles[angle]['direction2']
                    multiplier = 1
                    if obj_size > 1:
                        extra_tile_1 = (x + x_dir, y + y_dir)
                        extra_tile_2 = (x - x_dir, y - y_dir)
                        if extra_tile_1 in occupied_tiles or extra_tile_2 in occupied_tiles:
                            continue
                        if extra_tile_1 in extra_occupied or extra_tile_2 in extra_occupied:
                            continue
                        occupied_tiles.append(extra_tile_1)
                        occupied_tiles.append(extra_tile_2)
                        extra_occupied.append((x + x_dir2 + x_dir * multiplier, y + y_dir2 + y_dir * multiplier))
                        extra_occupied.append((x + x_dir2 - x_dir * multiplier, y + y_dir2 - y_dir * multiplier))
                        multiplier = 2
                    extra_occupied.append((x + x_dir2, y + y_dir2))
                    extra_occupied.append((x + x_dir2 + x_dir * multiplier, y + y_dir2 + y_dir * multiplier))
                    extra_occupied.append((x + x_dir2 - x_dir * multiplier, y + y_dir2 - y_dir * multiplier))
                    occupied_tiles += [(x, y)]
                    FurnitureGenerator.write(f, x, y, obj_type,
                                             FurnitureGenerator.angles[angle]['angle'] - 90 * obj_rotated,
                                             rng.randrange(obj_variations))
        return [Point(tile[0], tile[1]) for tile in occupied_tiles]

    @staticmethod
    def place_bookshelf(rng, all_borders, f):
        border = rng.choice(all_borders)
        x, y = border[0]
        angle = border[1]
        x_dir, y_dir = FurnitureGenerator.angles[angle]['direction']
        bookshelf_types = [(3303, 1901), (171, 98)]
        FurnitureGenerator.write(f, x, y, rng.choice(bookshelf_types),
                                 FurnitureGenerator.angles[angle]['angle'] - 90)

        new_occupations = []
        new_occupations += [Point(x, y)]
        new_occupations += [Point(x + y_dir, y + x_dir)]
        new_occupations += [Point(x - y_dir, y - x_dir)]
        return new_occupations

    @staticmethod
    def place_tv_spot(rng, all_borders, f, tiles_tuples):
        border = rng.choice(all_borders)
        x, y = border[0]
        angle = border[1]
        x_dir, y_dir = FurnitureGenerator.angles[angle]['direction']
        armchair_types = [(178, 104), (1355, 835), (3450, 2013)]
        if (x + x_dir * 2, y + y_dir * 2) not in tiles_tuples or (x + x_dir * 3, y + y_dir * 3) not in tiles_tuples:
            return []
        FurnitureGenerator.write(f, x, y, (191, 110),
                                 FurnitureGenerator.angles[angle]['angle'])
        FurnitureGenerator.write(f, x + x_dir, y + y_dir, rng.choice(armchair_types),
                                 FurnitureGenerator.angles[angle]['angle'] + 90)

        new_occupations = []
        new_occupations += [Point(x, y)]
        new_occupations += [Point(x + x_dir, y + y_dir)]
        return new_occupations

    @staticmethod
    def place_billiard(rng, center_tiles, f):
        x, y = rng.choice(center_tiles)
        is_rotated = rng.randrange(2)
        FurnitureGenerator.write(f, x, y, (1861, 1092), 90 * is_rotated)

        new_occupations = []
        new_occupations += [Point(x, y)]
        if is_rotated:
            new_occupations += [Point(x, y + 1)]
            new_occupations += [Point(x, y - 1)]
        else:
            new_occupations += [Point(x - 1, y)]
            new_occupations += [Point(x + 1, y)]

        return new_occupations

    @staticmethod
    def write(f, x, y, object_type, rotation=0, variant=0):
        print(11, file=f)
        print(32 * x + 20, file=f)
        print(32 * y + 20, file=f)
        print(object_type[0], file=f)
        print(rotation, file=f)
        print(object_type[1], file=f)
        print(variant, file=f)
