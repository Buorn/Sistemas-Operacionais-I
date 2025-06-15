import multiprocessing as mp
from ctypes import c_char, c_bool
import time
import random
from constants import GRID_WIDTH, GRID_HEIGHT, NUM_ROBOTS, NUM_BARRIERS, NUM_BATTERIES
from robot import robot_process
from viewer import viewer_process

def inicializa_grid(grid, grid_mutex):
    with grid_mutex:
        # Limpa o grid e preenche com espaços vazio ' '
        for i in range(GRID_WIDTH * GRID_HEIGHT):
            grid[i] = b' '

        # Cria a borda do GRID usando o caractere '#'
        for x in range(GRID_WIDTH):
            grid[0 * GRID_WIDTH + x] = b'#'
            grid[(GRID_HEIGHT - 1) * GRID_WIDTH + x] = b'#'
        for y in range(GRID_HEIGHT):
            grid[y * GRID_WIDTH + 0] = b'#'
            grid[y * GRID_WIDTH + (GRID_WIDTH - 1)] = b'#'

        # Posiciona as barreiras de forma aleatória
        for _ in range(NUM_BARRIERS):
            while True:
                x = random.randint(1, GRID_WIDTH - 2)
                y = random.randint(1, GRID_HEIGHT - 2)
                idx = y * GRID_WIDTH + x
                if grid[idx] == b' ':
                    grid[idx] = b'#'
                    break

        # Posiciona as baterias de forma aleatória
        for _ in range(NUM_BATTERIES):
            while True:
                x = random.randint(1, GRID_WIDTH - 2)
                y = random.randint(1, GRID_HEIGHT - 2)
                idx = y * GRID_WIDTH + x
                if grid[idx] == b' ':
                    grid[idx] = b'&'
                    break

        # Posiciona robôs com IDs 'A', 'B', 'C', 'D'
        rob_ids = [b'A', b'B', b'C', b'D']
        for rid in rob_ids:
            while True:
                x = random.randint(1, GRID_WIDTH - 2)
                y = random.randint(1, GRID_HEIGHT - 2)
                idx = y * GRID_WIDTH + x
                if grid[idx] == b' ':
                    grid[idx] = rid
                    break

def cria_flags(manager):
    flags = manager.dict()
    flags['game_over'] = False
    return flags

def main():
    grid = mp.Array(c_char, GRID_WIDTH * GRID_HEIGHT)
    grid_mutex = mp.Lock()

    manager = mp.Manager()
    flags = cria_flags(manager)

    inicializa_grid(grid, grid_mutex)

    robos = []
    for i in range(NUM_ROBOTS):
        # A chamada do processo continua a mesma
        p = mp.Process(target=robot_process, args=(grid, grid_mutex, flags, i))
        p.start()
        robos.append(p)

    viewer = mp.Process(target=viewer_process, args=(grid, flags))
    viewer.start()

    for p in robos:
        p.join()

    flags['game_over'] = True
    viewer.join()

    print("Jogo finalizado.")

if __name__ == "__main__":
    main()
