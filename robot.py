import time
import random
import os  # NOVO: necessário para gravar os arquivos de log
import sys  # NOVO: para capturar entrada de teclado do jogador
import termios  # NOVO: para leitura não bloqueante do teclado
import tty  # NOVO: usado com termios
import threading  # NOVO: para rodar o input do jogador em paralelo
from constants import GRID_WIDTH, GRID_HEIGHT, MAX_ENERGY, ROBOT_IDS

# NOVO: função auxiliar para registrar ações do robô em arquivo
def log(robot_char, message):
    filename = f"log_{robot_char}.txt"
    with open(filename, "a") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {message}\n")  # grava mensagem com horário

# NOVO: captura uma tecla pressionada sem precisar apertar ENTER
def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key

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
    rob_id_byte = ROBOT_IDS[robot_id_index].encode()  # 'A', 'B', ...
    robot_char = ROBOT_IDS[robot_id_index]  # NOVO: usado para nomear arquivos de log
    energia = MAX_ENERGY

    log(robot_char, "Robô iniciado com energia máxima")  # NOVO

    pos = get_pos(grid, grid_mutex, rob_id_byte)
    if pos is None:
        log(robot_char, "Erro: posição inicial não encontrada. Encerrando.")  # NOVO
        return

    while energia > 0 and not flags['game_over']:
        # Decide movimento aleatório N/S/L/O dentro do grid
        x, y = pos
        direcoes = []
        if x > 0:
            direcoes.append((x-1, y))
        if x < GRID_WIDTH - 1:
            direcoes.append((x+1, y))
        if y > 0:
            direcoes.append((x, y-1))
        if y < GRID_HEIGHT - 1:
            direcoes.append((x, y+1))

        new_pos = random.choice(direcoes)

        moved = move_robot(grid, grid_mutex, rob_id_byte, pos, new_pos)
        if moved:
            log(robot_char, f"Movido de {pos} para {new_pos}")  # NOVO
            pos = new_pos
            energia -= 1
            log(robot_char, f"Energia restante: {energia}")  # NOVO
        else:
            log(robot_char, f"Tentativa de mover para {new_pos} falhou (bloqueado)")  # NOVO

        time.sleep(0.2)

    with grid_mutex:
        idx = pos[1] * GRID_WIDTH + pos[0]
        grid[idx] = b' '
    log(robot_char, "Robô removido do grid (morte ou fim de jogo)")  # NOVO

    with grid_mutex:
        vivos = 0
        for i in range(GRID_WIDTH * GRID_HEIGHT):
            c = grid[i]
            if c in [r.encode() for r in ROBOT_IDS]:
                vivos += 1
    if vivos <= 1:
        flags['game_over'] = True
        log(robot_char, "Fim de jogo detectado (1 robô restante)")  # NOVO

# NOVO: Função para robô controlado pelo jogador (input manual via teclado)
def player_robot_process(grid, grid_mutex, flags, robot_id_index):
    rob_id_byte = ROBOT_IDS[robot_id_index].encode()
    robot_char = ROBOT_IDS[robot_id_index]
    energia = MAX_ENERGY

    log(robot_char, "Robô jogador iniciado com energia máxima")  # NOVO
    print(f"\n🎮 Robô jogador '{robot_char}' pronto! Use W A S D para se mover. Q para sair.\n")  # NOVO

    pos = get_pos(grid, grid_mutex, rob_id_byte)
    if pos is None:
        log(robot_char, "Erro: posição inicial não encontrada. Encerrando.")  # NOVO
        return

    # NOVO: Thread que escuta comandos do teclado do jogador
    def input_loop():
        nonlocal pos, energia
        while energia > 0 and not flags['game_over']:
            key = get_key().lower()
            if key == 'q':
                print("Saindo...")  # NOVO
                flags['game_over'] = True
                break

            dx, dy = 0, 0
            if key == 'w': dy = -1
            elif key == 's': dy = 1
            elif key == 'a': dx = -1
            elif key == 'd': dx = 1
            else:
                continue  # tecla inválida

            new_x = pos[0] + dx
            new_y = pos[1] + dy

            if 0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT:
                new_pos = (new_x, new_y)
                moved = move_robot(grid, grid_mutex, rob_id_byte, pos, new_pos)
                if moved:
                    pos = new_pos
                    energia -= 1
                    print(f"Movido para {pos}, Energia: {energia}")  # NOVO
                    log(robot_char, f"Movido para {pos}, Energia: {energia}")  # NOVO
                else:
                    print("Movimento bloqueado!")  # NOVO
                    log(robot_char, f"Movimento bloqueado em {new_pos}")  # NOVO
            else:
                print("Fora dos limites!")  # NOVO

    # NOVO: roda o loop de input em uma thread separada
    t = threading.Thread(target=input_loop)
    t.start()
    t.join()

    with grid_mutex:
        idx = pos[1] * GRID_WIDTH + pos[0]
        grid[idx] = b' '
    log(robot_char, "Robô jogador removido do grid (morte ou saída)")  # NOVO

