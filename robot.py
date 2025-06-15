import time
import random
import os
import sys
import termios
import tty
import threading
from constants import GRID_WIDTH, GRID_HEIGHT, MAX_ENERGY, ROBOT_IDS

# --- FUNÇÕES AUXILIARES PARA A IA ---

def calculate_distance_sq(pos1, pos2):
    """Calcula o quadrado da distância euclidiana entre dois pontos."""
    return (pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2

# --- FUNÇÕES ORIGINAIS DO PROJETO (com modificações necessárias) ---

def log(robot_char, message):
    """Registra uma mensagem de log para o robô."""
    filename = f"log_{robot_char}.txt"
    with open(filename, "a") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {message}\n")

def get_key():
    """Captura uma tecla pressionada sem precisar de ENTER."""
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
    """
    Move o robô de old_pos para new_pos no grid.
    Retorna uma tupla: (sucesso_movimento, item_coletado)
    Permite mover para espaços vazios ou baterias.
    """
    with grid_mutex:
        old_idx = old_pos[1] * GRID_WIDTH + old_pos[0]
        new_idx = new_pos[1] * GRID_WIDTH + new_pos[0]

        # Verifica se o destino é válido (dentro dos limites)
        if not (0 <= new_pos[0] < GRID_WIDTH and 0 <= new_pos[1] < GRID_HEIGHT):
            return False, None

        item_no_destino = grid[new_idx]

        # O robô pode mover-se para um espaço vazio ou para uma bateria.
        if item_no_destino == b' ' or item_no_destino == b'&':
            grid[old_idx] = b' '      # Limpa a posição antiga
            grid[new_idx] = rob_id_byte # Coloca o robô na nova posição
            return True, item_no_destino # Retorna sucesso e o que havia no local
        else:
            # Não pode mover-se para barreiras ou outros robôs
            return False, item_no_destino

# --- LÓGICA DO PROCESSO DO ROBÔ AUTÔNOMO (COM IA) ---

def robot_process(grid, grid_mutex, flags, robot_id_index):
    """Processo principal para um robô autônomo com IA."""
    rob_id_byte = ROBOT_IDS[robot_id_index].encode()
    robot_char = ROBOT_IDS[robot_id_index]
    energia = MAX_ENERGY

    log(robot_char, f"Robô IA '{robot_char}' iniciado com energia máxima.")

    pos_inicial = get_pos(grid, grid_mutex, rob_id_byte)
    if pos_inicial is None:
        log(robot_char, "ERRO: Posição inicial não encontrada. Encerrando.")
        return

    while energia > 0 and not flags['game_over']:
        current_pos = get_pos(grid, grid_mutex, rob_id_byte)
        if current_pos is None:
            log(robot_char, "Robô não está mais no grid. Encerrando.")
            break

        # 1. IDENTIFICAR TODOS OS ALVOS (OUTROS ROBÔS E BATERIAS)
        alvos = []
        with grid_mutex:
            for i in range(GRID_WIDTH * GRID_HEIGHT):
                conteudo_celula = grid[i]
                if conteudo_celula == b'&':
                    x_alvo, y_alvo = i % GRID_WIDTH, i // GRID_WIDTH
                    alvos.append(((x_alvo, y_alvo), 'bateria'))
                elif conteudo_celula in [r.encode() for r in ROBOT_IDS] and conteudo_celula != rob_id_byte:
                    x_alvo, y_alvo = i % GRID_WIDTH, i // GRID_WIDTH
                    alvos.append(((x_alvo, y_alvo), 'robo'))

        # 2. ENCONTRAR O ALVO MAIS PRÓXIMO
        alvo_final_pos = None
        alvo_final_tipo = None
        distancia_minima_sq = float('inf')

        if alvos:
            for pos_alvo, tipo_alvo in alvos:
                dist = calculate_distance_sq(current_pos, pos_alvo)
                if dist < distancia_minima_sq:
                    distancia_minima_sq = dist
                    alvo_final_pos = pos_alvo
                    alvo_final_tipo = tipo_alvo

        # (Mantenha todo o código anterior da função robot_process)

        # 3. DETERMINAR A POSIÇÃO DE DESTINO E O PRÓXIMO PASSO
        posicao_a_mover = None
        if alvo_final_pos:
            log(robot_char, f"Alvo mais próximo: {alvo_final_tipo} em {alvo_final_pos}.")

            destino_para_movimento = alvo_final_pos
            # Se o alvo for um robô, o destino deve ser uma célula vazia adjacente a ele.
            if alvo_final_tipo == 'robo':
                ex, ey = alvo_final_pos
                celulas_adjacentes_vazias = []
                with grid_mutex:
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        ax, ay = ex + dx, ey + dy
                        if 0 <= ax < GRID_WIDTH and 0 <= ay < GRID_HEIGHT and grid[ay * GRID_WIDTH + ax] in [b' ', b'&']: # Permite mover para adjacente se for bateria também
                            celulas_adjacentes_vazias.append((ax, ay))

                if celulas_adjacentes_vazias:
                    # Escolhe a célula adjacente mais próxima do robô atual
                    destino_para_movimento = min(celulas_adjacentes_vazias, key=lambda c: calculate_distance_sq(current_pos, c))
                    log(robot_char, f"Movendo para {destino_para_movimento} para se aproximar do robô em {alvo_final_pos}.")
                else:
                    log(robot_char, f"Robô alvo em {alvo_final_pos} está cercado. Forçando movimento aleatório.")
                    destino_para_movimento = None # Força movimento aleatório

            # Se houver um destino, calcula o próximo passo
            if destino_para_movimento and destino_para_movimento != current_pos:
                x, y = current_pos
                dx = destino_para_movimento[0] - x
                dy = destino_para_movimento[1] - y

                passos_preferenciais = []
                # Prioriza o eixo com a maior distância
                if abs(dx) > abs(dy):
                    if dx != 0: passos_preferenciais.append((x + (1 if dx > 0 else -1), y))
                    if dy != 0: passos_preferenciais.append((x, y + (1 if dy > 0 else -1)))
                else:
                    if dy != 0: passos_preferenciais.append((x, y + (1 if dy > 0 else -1)))
                    if dx != 0: passos_preferenciais.append((x + (1 if dx > 0 else -1), y))

                # Adiciona os outros movimentos possíveis como alternativas
                for move in [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]:
                    if move not in passos_preferenciais:
                        passos_preferenciais.append(move)

                # *** CORREÇÃO PRINCIPAL AQUI ***
                # Tenta o passo preferencial, mas SÓ se ele for válido (vazio ou bateria)
                with grid_mutex:
                    for passo in passos_preferenciais:
                        if 0 <= passo[0] < GRID_WIDTH and 0 <= passo[1] < GRID_HEIGHT:
                            idx = passo[1] * GRID_WIDTH + passo[0]
                            conteudo = grid[idx]
                            if conteudo == b' ' or conteudo == b'&':
                                posicao_a_mover = passo # Encontrou um passo válido
                                break # Para de procurar

        # Se não há alvos ou o caminho inteligente está bloqueado, move-se aleatoriamente
        if not posicao_a_mover:
            log(robot_char, "Nenhum alvo ou caminho claro. Movendo aleatoriamente.")
            x, y = current_pos
            movimentos_possiveis = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
            random.shuffle(movimentos_possiveis)
            with grid_mutex:
                for move in movimentos_possiveis:
                    if 0 <= move[0] < GRID_WIDTH and 0 <= move[1] < GRID_HEIGHT:
                        conteudo = grid[move[1] * GRID_WIDTH + move[0]]
                        if conteudo == b' ' or conteudo == b'&':
                            posicao_a_mover = move
                            break

# (O restante do código, a partir de # 4. EXECUTAR O MOVIMENTO, pode continuar o mesmo)
        # 4. EXECUTAR O MOVIMENTO
        if posicao_a_mover and posicao_a_mover != current_pos:
            movido, item_coletado = move_robot(grid, grid_mutex, rob_id_byte, current_pos, posicao_a_mover)
            if movido:
                energia -= 1
                log_msg = f"Movido de {current_pos} para {posicao_a_mover}. Energia: {energia}"
                if item_coletado == b'&':
                    energia = min(MAX_ENERGY, energia + 20)
                    log_msg += f". BATERIA COLETADA! Nova energia: {energia}"
                log(robot_char, log_msg)
            else:
                log(robot_char, f"Falha ao tentar mover para {posicao_a_mover} (bloqueado).")
        else:
            log(robot_char, "Nenhum movimento realizado neste turno.")

        time.sleep(0.2)

    # Lógica de finalização do robô
    with grid_mutex:
        pos_final = get_pos(grid, grid_mutex, rob_id_byte)
        if pos_final:
            grid[pos_final[1] * GRID_WIDTH + pos_final[0]] = b' '
    log(robot_char, f"Robô removido do grid (Energia: {energia} / Fim de Jogo: {flags['game_over']}).")

    # Verifica se o jogo acabou
    with grid_mutex:
        vivos = sum(1 for i in range(GRID_WIDTH * GRID_HEIGHT) if grid[i] in [r.encode() for r in ROBOT_IDS])
    if vivos <= 1:
        flags['game_over'] = True
        log(robot_char, f"Fim de jogo detectado ({vivos} robôs restantes).")


# --- PROCESSO DO ROBÔ CONTROLADO PELO JOGADOR (ORIGINAL, SEM ALTERAÇÕES) ---

def player_robot_process(grid, grid_mutex, flags, robot_id_index):
    rob_id_byte = ROBOT_IDS[robot_id_index].encode()
    robot_char = ROBOT_IDS[robot_id_index]
    energia = MAX_ENERGY

    log(robot_char, "Robô jogador iniciado com energia máxima")
    print(f"\n🎮 Robô jogador '{robot_char}' pronto! Use W A S D para se mover. Q para sair.\n")

    pos = get_pos(grid, grid_mutex, rob_id_byte)
    if pos is None:
        log(robot_char, "Erro: posição inicial não encontrada. Encerrando.")
        return

    # Thread que escuta comandos do teclado do jogador
    def input_loop():
        nonlocal pos, energia
        while energia > 0 and not flags['game_over']:
            key = get_key().lower()
            if key == 'q':
                print("Saindo...")
                flags['game_over'] = True
                break

            dx, dy = 0, 0
            if key == 'w': dy = -1
            elif key == 's': dy = 1
            elif key == 'a': dx = -1
            elif key == 'd': dx = 1
            else:
                continue

            new_x = pos[0] + dx
            new_y = pos[1] + dy

            if 0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT:
                new_pos = (new_x, new_y)
                # O robô do jogador também usa a função de movimento modificada
                moved, item_hit = move_robot(grid, grid_mutex, rob_id_byte, pos, new_pos)
                if moved:
                    pos = new_pos
                    energia -= 1
                    log_msg = f"Movido para {pos}, Energia: {energia}"
                    if item_hit == b'&':
                        energia = min(MAX_ENERGY, energia + 20)
                        log_msg += f" (Bateria Coletada! Nova Energia: {energia})"
                    print(log_msg)
                    log(robot_char, log_msg)
                else:
                    print("Movimento bloqueado!")
                    log(robot_char, f"Movimento bloqueado em {new_pos}")
            else:
                print("Fora dos limites!")

    t = threading.Thread(target=input_loop)
    t.start()
    t.join()

    with grid_mutex:
        idx = pos[1] * GRID_WIDTH + pos[0]
        grid[idx] = b' '
    log(robot_char, "Robô jogador removido do grid (morte ou saída)")
