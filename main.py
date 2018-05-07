import random

from Chromosomes import *
from FurnitureGenerator import *
from GeneticAlgorithm import *
from Serializer import *
from config import *

if __name__ == '__main__':
    # Make sure that the output dir exists
    if not os.path.isdir(hl2_path):
        print("Could not find the HL2 levels folder at:")
        print(hl2_path)
        exit(1)
    if not os.path.isdir(level_path):
        os.makedirs(level_path)

    # Generate the seed
    if random_seed:
        seed = random.randrange(100000000)
    print("Seed:", seed)
    rng = random.Random(seed)

    # Run the GA to generate rooms
    room_ga = GeneticAlgorithm(
        breeder=GeneticAlgorithm.uniform_crossover,
        mutator=RoomChromosome.mutate,
        initial=[RoomChromosome.generate_gene(rng, gene_length) for _ in range(population_size)],
        fitness=Fitness.mixed_room_fitness,
        _rng=rng
    )
    rooms_dominant = room_ga.compute(iterations)

    # Run the GA to generate room types
    room_type_ga = GeneticAlgorithm(
        breeder=GeneticAlgorithm.uniform_crossover,
        mutator=RoomTypeChromosome.mutate,
        initial=[RoomTypeChromosome.generate_gene(rng, rooms_dominant) for _ in range(population_size)],
        fitness=Fitness.room_type_fitness,
        _rng=rng
    )
    room_types_dominant = room_type_ga.compute(iterations)

    # Transform the room layout to a HLM map
    hotline_map, start_tile = HotlineSerializer.to_map(rooms_dominant, Point(20, 25), rng)
    TileSerializer.serialize(room_types_dominant, tiles_path, rng)

    room_map = RoomMap(rooms_dominant)
    rooms_tiles = room_map.get_rooms_tiles()
    narrow_corridors = room_map.get_narrow_corridors()
    start_room = next(room for room, tiles in rooms_tiles.items() if start_tile in tiles)

    # Generate furniture
    available_rooms_tiles = {room: [tile for tile in tiles if tile not in narrow_corridors] for room, tiles in
                             rooms_tiles.items()}
    rooms_types = {chromosome.room.index: chromosome.room_type for chromosome in room_types_dominant}
    occupied_tiles = FurnitureGenerator.place_objects(rng, hotline_map, rooms_types, available_rooms_tiles,
                                                      objects_path)

    rooms_centers = {room: Point.points_center(tiles) for room, tiles in rooms_tiles.items()}
    distance_map = RoomsGraph(rooms_dominant).get_distance_map(start_room, rooms_centers)
    rooms_by_distance = sorted(distance_map, key=distance_map.get)

    # Run the GA to generate enemies
    enemies_ga = GeneticAlgorithm(
        breeder=GeneticAlgorithm.uniform_crossover,
        mutator=EnemyChromosome.mutate,
        initial=[EnemyChromosome.generate_gene(rng, rooms_tiles, rooms_by_distance, occupied_tiles) for _ in
                 range(population_size)],
        fitness=Fitness.enemy_fitness,
        _rng=rng
    )
    enemies_dominant = enemies_ga.compute(iterations)

    # Save the result
    WallSerializer.serialize(hotline_map, walls_path)
    enemies = EnemySerializer.serialize(enemies_dominant, objects_path)

    # Draw the final output
    app = Application(master=tk.Tk())
    app.draw(rooms_dominant)
    colors = {"Door": "black", "Standard": "bisque3", "RedBrick": "red4", "Transition": "green"}
    for x in range(map_width):
        for y in range(map_height):
            if "HorizontalWall" in hotline_map[x][y]:
                if hotline_map[x][y]["HorizontalWall"][0] != "Transition":
                    app.draw_wall(x, y, 1, colors[hotline_map[x][y]["HorizontalWall"][0]])
            if "VerticalWall" in hotline_map[x][y]:
                if hotline_map[x][y]["VerticalWall"][0] != "Transition":
                    app.draw_wall(x, y, 0, colors[hotline_map[x][y]["VerticalWall"][0]])
    for t in occupied_tiles:
        app.draw_index(t.x, t.y, "T")
    for e in enemies:
        app.draw_index(e.x, e.y, "E")

    app.mainloop()
