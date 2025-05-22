import multiprocessing as mp
from ctypes import c_char, c_bool
import time
import random
from constants import GRID_WIDTH, GRID_HEIGHT, NUM_ROBOTS, NUM_BARRIERS, NUM_BATTERIES	# Importa as constantes de constants.py
from robot import robot_process								
from viewer import viewer_process							

def inicializa_grid(grid, grid_mutex):
    with grid_mutex:
        # Limpa o grid com espaços
        for i in range(GRID_WIDTH * GRID_HEIGHT):
            grid[i] = b' '
	
        # Adiciona barreiras nas bordas do grid
        for x in range(GRID_WIDTH):
            grid[0 * GRID_WIDTH + x] = b'#'                        # Borda superior
            grid[(GRID_HEIGHT - 1) * GRID_WIDTH + x] = b'#'       # Borda inferior
        for y in range(GRID_HEIGHT):
            grid[y * GRID_WIDTH + 0] = b'#'                        # Borda esquerda
            grid[y * GRID_WIDTH + (GRID_WIDTH - 1)] = b'#'        # Borda direita

	# Posiciona barreiras '#'
        for _ in range(NUM_BARRIERS):
            while True:
                x = random.randint(0, GRID_WIDTH -1)
                y = random.randint(0, GRID_HEIGHT -1)
                idx = y * GRID_WIDTH + x
                if grid[idx] == b' ':
                    grid[idx] = b'#'
                    break

        # Posiciona baterias '&'
        for _ in range(NUM_BATTERIES):
            while True:
                x = random.randint(0, GRID_WIDTH -1)
                y = random.randint(0, GRID_HEIGHT -1)
                idx = y * GRID_WIDTH + x
                if grid[idx] == b' ':
                    grid[idx] = b'&'
                    break

        # Posiciona robôs com IDs 'A', 'B', 'C', 'D'
        rob_ids = [b'A', b'B', b'C', b'D']
        for rid in rob_ids:
            while True:
                x = random.randint(0, GRID_WIDTH -1)
                y = random.randint(0, GRID_HEIGHT -1)
                idx = y * GRID_WIDTH + x
                if grid[idx] == b' ':
                    grid[idx] = rid
                    break

def cria_flags(manager):
    # Usamos Manager para criar dicionário de flags compartilhadas
    flags = manager.dict()
    flags['game_over'] = False
    return flags

def main():
    mp.set_start_method('spawn')  # Compatibilidade multiplataforma

    # Cria memória compartilhada para o grid
    grid = mp.Array(c_char, GRID_WIDTH * GRID_HEIGHT)

    # Mutex para controlar acesso ao grid
    grid_mutex = mp.Lock()

    # Manager para flags compartilhadas
    manager = mp.Manager()
    flags = cria_flags(manager)

    # Inicializa o grid (barreiras, baterias, robôs)
    inicializa_grid(grid, grid_mutex)

    # Cria lista para processos de robôs
    robos = []
    for i in range(NUM_ROBOTS):
        # Passa grid, mutex, flags e id do robô para cada processo
        p = mp.Process(target=robot_process, args=(grid, grid_mutex, flags, i))
        p.start()
        robos.append(p)

    # Cria processo viewer
    viewer = mp.Process(target=viewer_process, args=(grid, flags))
    viewer.start()

    # Espera os robôs terminarem
    for p in robos:
        p.join()

    # Depois que robôs terminam, sinaliza fim pro viewer
    flags['game_over'] = True

    # Espera o viewer terminar
    viewer.join()

    print("Jogo finalizado.")

if __name__ == "__main__":
    main()

