import time
import random
from constants import GRID_WIDTH, GRID_HEIGHT, MAX_ENERGY, ROBOT_IDS

def get_pos(grid, grid_mutex, rob_id_byte):
    """Busca a posição atual do robô no grid."""
    with grid_mutex:
        for i in range(GRID_WIDTH * GRID_HEIGHT):
            if grid[i] == rob_id_byte:
                x = i % GRID_WIDTH
                y = i // GRID_WIDTH
                return (x, y)
    return None

def move_robot(grid, grid_mutex, rob_id_byte, old_pos, new_pos):
    """Move robô de old_pos para new_pos no grid."""
    with grid_mutex:
        old_idx = old_pos[1] * GRID_WIDTH + old_pos[0]
        new_idx = new_pos[1] * GRID_WIDTH + new_pos[0]

        # Só move se destino vazio (b' ')
        if grid[new_idx] == b' ':
            grid[old_idx] = b' '
            grid[new_idx] = rob_id_byte
            return True
    return False

def robot_process(grid, grid_mutex, flags, robot_id_index):
    rob_id_byte = ROBOT_IDS[robot_id_index].encode()  		# 'A', 'B', ...
    energia = MAX_ENERGY

    pos = get_pos(grid, grid_mutex, rob_id_byte)
    if pos is None:
        # Se não achar posição, termina
        return

    while energia > 0 and not flags['game_over']:
        # Decide movimento aleatório N/S/L/O dentro do grid
        x, y = pos
        direcoes = []
        if x > 0:
            direcoes.append( (x-1,y) )
        if x < GRID_WIDTH -1:
            direcoes.append( (x+1,y) )
        if y > 0:
            direcoes.append( (x,y-1) )
        if y < GRID_HEIGHT -1:
            direcoes.append( (x,y+1) )

        new_pos = random.choice(direcoes)

        moved = move_robot(grid, grid_mutex, rob_id_byte, pos, new_pos)
        if moved:
            pos = new_pos
            energia -= 1  # movimentar consome energia

        time.sleep(0.2)

        # Aqui poderia checar duelos, baterias, etc (simplificado)

    # Robô morreu ou game over, libera sua célula
    with grid_mutex:
        idx = pos[1]*GRID_WIDTH + pos[0]
        grid[idx] = b' '

    # Checar se sobrou só 1 robô vivo (simplificação)
    # Contar robôs vivos no grid
    with grid_mutex:
        vivos = 0
        for i in range(GRID_WIDTH * GRID_HEIGHT):
            c = grid[i]
            if c in [r.encode() for r in ROBOT_IDS]:
                vivos += 1
    if vivos <= 1:
        flags['game_over'] = True

