import os

map_width = 32
map_height = 21
min_room_size = 3
max_room_size = 10
average_room_area = (min_room_size * min_room_size + max_room_size * max_room_size) // 2
#32590456
seed = 98779837
random_seed = False
debug_output = False
gene_length = 10
population_size = 20
iterations = 100
difficulty = 60

level_folder = "a6514ac2-73e2-4c3e-b687-0ac43781cc62"
hl2_path = os.path.join('C:\\', 'Users', os.getlogin(), 'Documents', 'My Games', "HotlineMiami2")
level_path = os.path.join(hl2_path, 'Levels', 'single', level_folder)

walls_path = os.path.join(level_path, "level0.wll")
tiles_path = os.path.join(level_path, "level0.tls")
objects_path = os.path.join(level_path, "level0.obj")
