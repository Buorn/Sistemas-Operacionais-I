import ctypes
import random
from multiprocessing import Array, Value, Lock

# Dimensões do tabuleiro
GRID_WIDTH = 40
GRID_HEIGHT = 20

# Energia máxima que um robô pode ter
MAX_ENERGY = 100

# Número total de robôs na arena
NUM_ROBOTS = 4

# Número de baterias a serem colocadas no grid
NUM_BATTERIES = 5

# Número de barreiras fixas a serem colocadas no grid
NUM_BARRIERS = 30

# Identificacao dos robos
ROBOT_IDS = ['A','B','C','D']


# Conversão de coordenadas (x, y) para índice linear
def xy_to_index(x, y):
    return y * GRID_WIDTH + x

# Estrutura do robô na memória compartilhada
class Robot(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_char),
        ("forca", ctypes.c_int),
        ("energia", ctypes.c_int),
        ("velocidade", ctypes.c_int),
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("vivo", ctypes.c_int)
    ]

# Criação da memória compartilhada e locks
def create_shared_segment():
    grid = Array(ctypes.c_char, GRID_WIDTH * GRID_HEIGHT)  # Segmento do tabuleiro

    # Inicializa o grid como vazio (' ')
    for i in range(GRID_WIDTH * GRID_HEIGHT):
        grid[i] = b' '[0]

    # Vetor de robôs
    robots = Array(Robot, NUM_ROBOTS)

    # Flags auxiliares
    flags = {
        'init_done': Value(ctypes.c_bool, False),
        'game_over': Value(ctypes.c_bool, False),
        'winner_id': Value(ctypes.c_char, b' ')
    }

    # Locks
    locks = {
        'init_mutex': Lock(),
        'grid_mutex': Lock(),
        'robots_mutex': Lock(),
        'battery_mutexes': [Lock() for _ in range(GRID_WIDTH * GRID_HEIGHT)]
    }

    return grid, robots, flags, locks

# Inicializa robôs, barreiras e baterias
def initialize_grid(grid, robots, flags):
    # Coloca barreiras
    for _ in range(NUM_BARRIERS):
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            idx = xy_to_index(x, y)
            if grid[idx] == b' '[0]:
                grid[idx] = b'#'[0]
                break

    # Coloca baterias
    for _ in range(NUM_BATTERIES):
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            idx = xy_to_index(x, y)
            if grid[idx] == b' '[0]:
                grid[idx] = b'&'[0]
                break

    # Inicializa os robôs
    letras = [chr(65 + i).encode() for i in range(NUM_ROBOTS)]
    for i in range(NUM_ROBOTS):
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            idx = xy_to_index(x, y)
            if grid[idx] == b' '[0]:
                grid[idx] = letras[i][0]
                break

        robots[i].id = letras[i][0]
        robots[i].forca = random.randint(1, 10)
        robots[i].energia = random.randint(10, MAX_ENERGY)
        robots[i].velocidade = 1000	#random.randint(1, 5)
        robots[i].x = x
        robots[i].y = y
        robots[i].vivo = 1

    flags['init_done'].value = True
