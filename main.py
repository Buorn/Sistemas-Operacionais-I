import multiprocessing as mp								# Importa biblioteca para criar multiprocessos
from ctypes import c_char, c_bool							# Importa biblioteca para usar tipos de dadis compatíveis com C. Usado para representar caracteres no GRID. 
import time										# 
import random										# Importa biblioteca que gera valores aleatórios. Usado para posicionar elementos aleatoriamente no GRID.
from constants import GRID_WIDTH, GRID_HEIGHT, NUM_ROBOTS, NUM_BARRIERS, NUM_BATTERIES	# Importa as constantes de constants.py. 
from robot import robot_process								# Importa a função robot_process de robot.py.
from viewer import viewer_process							# Importa a função viewer_processes de viewer.py.

def inicializa_grid(grid, grid_mutex):				# inicializa o GRID.
    with grid_mutex:						# Inicia a seção crítica do código, pois as posicoes do GRID sao compartilhadas.
        # Limpa o grid e preenche com espaços vazio ' '
        for i in range(GRID_WIDTH * GRID_HEIGHT):
            grid[i] = b' '					# Estamos utilizado o vetor unidimensional grid[] para definir o tabuleiro.
	
        # Cria a borda do GRID usando o caractere '#'
        for x in range(GRID_WIDTH):
            grid[0 * GRID_WIDTH + x] = b'#'                     # Borda superior | Estamos linearizando as posições do GRID, utilizando (y * tam. coluna + x).
            grid[(GRID_HEIGHT - 1) * GRID_WIDTH + x] = b'#'     # Borda inferior | Estamos linearizando as posições do GRID, utilizando (y * tam. coluna + x).
        for y in range(GRID_HEIGHT):
            grid[y * GRID_WIDTH + 0] = b'#'                     # Borda esquerda | Estamos linearizando as posições do GRID, utilizando (y * tam. coluna + x).
            grid[y * GRID_WIDTH + (GRID_WIDTH - 1)] = b'#'      # Borda direita | Estamos linearizando as posições do GRID, utilizando (y * tam. coluna + x).

	# Posiciona as barreiras de forma aleatória usando o caractere '#'
        for _ in range(NUM_BARRIERS):
            while True:
                x = random.randint(0, GRID_WIDTH -1)
                y = random.randint(0, GRID_HEIGHT -1)
                idx = y * GRID_WIDTH + x			# Estamos linearizando as posições do GRID, utilizando (y * tam. coluna + x).
                if grid[idx] == b' ':				# Verifica se a posicao no GRID está vazia, caso positivo inclui a barreira.
                    grid[idx] = b'#'
                    break

        # Posiciona as baterias de forma aleatória usando o caractere '&'
        for _ in range(NUM_BATTERIES):
            while True:
                x = random.randint(0, GRID_WIDTH -1)
                y = random.randint(0, GRID_HEIGHT -1)
                idx = y * GRID_WIDTH + x			# Estamos linearizando as posições do GRID, utilizando (y * tam. coluna + x).
                if grid[idx] == b' ':				# Verifica se a posicao no GRID está vazia, caso positivo inclui a bateria.
                    grid[idx] = b'&'
                    break

        # Posiciona robôs com IDs 'A', 'B', 'C', 'D'
        rob_ids = [b'A', b'B', b'C', b'D']
        for rid in rob_ids:
            while True:
                x = random.randint(0, GRID_WIDTH -1)
                y = random.randint(0, GRID_HEIGHT -1)
                idx = y * GRID_WIDTH + x			# Estamos linearizando as posições do GRID, utilizando (y * tam. coluna + x).
                if grid[idx] == b' ':				# Verifica se a posicao no GRID está vazia, caso positivo inclui os robots.
                    grid[idx] = rid
                    break

def cria_flags(manager):
    # Usamos Manager para criar dicionário de flags compartilhadas
    flags = manager.dict()
    flags['game_over'] = False					#flag utilizada pra sinalizar o fim do jogo.
    return flags

def main():
    # Cria memória compartilhada para o vetor unidimensional grid[].
    grid = mp.Array(c_char, GRID_WIDTH * GRID_HEIGHT)

    # Mutex para controlar acesso a memória compartilhada grid[].
    grid_mutex = mp.Lock()

    # flags para controle entre processos das memórias compartilhadas
    manager = mp.Manager()
    flags = cria_flags(manager)

    # Inicializa o GRID (barreiras, baterias, robôs), recebendo como parâmetro o vetor grid[] e o mutex para controlar acesso ao vetor grid[].
    inicializa_grid(grid, grid_mutex)

    # Cria os o vetor de robos
    robos = []
    for i in range(NUM_ROBOTS):
        # Instancia o proceso para cada robo, passando grid, mutex, flags e id do robô para cada processo
        p = mp.Process(target=robot_process, args=(grid, grid_mutex, flags, i))
        p.start()
        robos.append(p)

    # Cria processo viewer, passando grid e flags
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

