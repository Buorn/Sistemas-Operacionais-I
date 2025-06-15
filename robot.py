import time
import random
import os
from constants import GRID_WIDTH, GRID_HEIGHT, MAX_ENERGY, ROBOT_IDS

# --- FUNÇÕES AUXILIARES ---

def log(robot_char, message):
    filename = f"log_{robot_char}.txt"
    with open(filename, "a") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {message}\n")

def calculate_distance_sq(pos1, pos2):
    return (pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2

def get_pos(grid, grid_mutex, rob_id_byte):
    with grid_mutex:
        for i in range(GRID_WIDTH * GRID_HEIGHT):
            if grid[i] == rob_id_byte:
                x = i % GRID_WIDTH
                y = i // GRID_WIDTH
                return (x, y)
    return None

def move_robot(grid, grid_mutex, rob_id_byte, old_pos, new_pos):
    with grid_mutex:
        old_idx = old_pos[1] * GRID_WIDTH + old_pos[0]
        new_idx = new_pos[1] * GRID_WIDTH + new_pos[0]

        item_no_destino = grid[new_idx]

        if item_no_destino == b' ' or item_no_destino == b'&':
            grid[old_idx] = b' '
            grid[new_idx] = rob_id_byte
            return True, item_no_destino
    return False, None

# --- LÓGICA DE BATALHA ---

def iniciar_batalha(atacante_id, defensor_id, flags):
    try:
        poder_atacante = (2 * flags[f'forca_{atacante_id}']) + flags[f'energia_{atacante_id}']
        poder_defensor = (2 * flags[f'forca_{defensor_id}']) + flags[f'energia_{defensor_id}']
    except KeyError:
        log(atacante_id, "ERRO: Falha ao ler status de batalha do oponente.")
        return None

    log(atacante_id, f"BATALHA! Poder {poder_atacante} vs {defensor_id} (Poder {poder_defensor})")
    log(defensor_id, f"SOB ATAQUE! {atacante_id} (Poder {poder_atacante}) vs Poder {poder_defensor}")

    if poder_atacante > poder_defensor:
        flags[f'energia_{defensor_id}'] = 0
        log(atacante_id, f"VITÓRIA contra {defensor_id}!")
        log(defensor_id, "DERROTA!")
        return defensor_id
    elif poder_defensor > poder_atacante:
        flags[f'energia_{atacante_id}'] = 0
        log(defensor_id, f"VITÓRIA contra {atacante_id}!")
        log(atacante_id, "DERROTA!")
        return atacante_id
    else:
        flags[f'energia_{atacante_id}'] = 0
        flags[f'energia_{defensor_id}'] = 0
        log(atacante_id, f"EMPATE com {defensor_id}! Ambos destruídos.")
        log(defensor_id, f"EMPATE com {atacante_id}! Ambos destruídos.")
        return (atacante_id, defensor_id)

# --- PROCESSO PRINCIPAL DO ROBÔ ---

def robot_process(grid, grid_mutex, flags, robot_id_index):
    robot_char = ROBOT_IDS[robot_id_index]
    rob_id_byte = robot_char.encode()

    flags[f'energia_{robot_char}'] = MAX_ENERGY
    flags[f'forca_{robot_char}'] = random.randint(5, 15)

    log(robot_char, f"Robô IA '{robot_char}' iniciado. Força: {flags[f'forca_{robot_char}']}")

    while flags.get(f'energia_{robot_char}', 0) > 0 and not flags['game_over']:
        current_pos = get_pos(grid, grid_mutex, rob_id_byte)
        if current_pos is None:
            break

        alvos = []
        with grid_mutex:
            for i in range(GRID_WIDTH * GRID_HEIGHT):
                conteudo = grid[i]
                id_alvo_str = conteudo.decode(errors='ignore')
                if conteudo == b'&':
                    pos_alvo = (i % GRID_WIDTH, i // GRID_WIDTH)
                    alvos.append({'pos': pos_alvo, 'tipo': 'bateria', 'id': None})
                elif id_alvo_str in ROBOT_IDS and conteudo != rob_id_byte and flags.get(f'energia_{id_alvo_str}', 0) > 0:
                    pos_alvo = (i % GRID_WIDTH, i // GRID_WIDTH)
                    alvos.append({'pos': pos_alvo, 'tipo': 'robo', 'id': id_alvo_str})

        acao_realizada = False
        if alvos:
            alvo_mais_proximo = min(alvos, key=lambda a: calculate_distance_sq(current_pos, a['pos']))
            dist_sq = calculate_distance_sq(current_pos, alvo_mais_proximo['pos'])

            if alvo_mais_proximo['tipo'] == 'robo' and dist_sq == 1:
                log(robot_char, f"Inimigo {alvo_mais_proximo['id']} adjacente. INICIANDO BATALHA!")
                perdedor = iniciar_batalha(robot_char, alvo_mais_proximo['id'], flags)

                if perdedor:
                    perdedores = perdedor if isinstance(perdedor, tuple) else (perdedor,)

                    # --- CORREÇÃO DO DEADLOCK AQUI ---
                    with grid_mutex: # Adquire o lock apenas uma vez
                        for p_id in perdedores:
                            # Busca pelo perdedor diretamente, sem chamar get_pos()
                            id_a_remover = p_id.encode()
                            for i in range(GRID_WIDTH * GRID_HEIGHT):
                                if grid[i] == id_a_remover:
                                    grid[i] = b' ' # Remove o robô do grid
                                    break

                acao_realizada = True

            if not acao_realizada:
                posicao_a_mover = None
                destino_final = alvo_mais_proximo['pos']

                if destino_final != current_pos:
                    x, y = current_pos
                    dx = destino_final[0] - x
                    dy = destino_final[1] - y

                    passos_preferenciais = []
                    if abs(dx) > abs(dy):
                        if dx != 0: passos_preferenciais.append((x + (1 if dx > 0 else -1), y))
                        if dy != 0: passos_preferenciais.append((x, y + (1 if dy > 0 else -1)))
                    else:
                        if dy != 0: passos_preferenciais.append((x, y + (1 if dy > 0 else -1)))
                        if dx != 0: passos_preferenciais.append((x + (1 if dx > 0 else -1), y))

                    with grid_mutex:
                        for passo in passos_preferenciais:
                            if 0 <= passo[0] < GRID_WIDTH and 0 <= passo[1] < GRID_HEIGHT:
                                conteudo = grid[passo[1] * GRID_WIDTH + passo[0]]
                                if conteudo == b' ' or conteudo == b'&':
                                    posicao_a_mover = passo
                                    break

                if posicao_a_mover:
                    movido, item_coletado = move_robot(grid, grid_mutex, rob_id_byte, current_pos, posicao_a_mover)
                    if movido:
                        energia_atual = flags.get(f'energia_{robot_char}', 0)
                        flags[f'energia_{robot_char}'] = energia_atual - 1
                        log_msg = f"Movido para {posicao_a_mover}. Energia: {flags.get(f'energia_{robot_char}')}"
                        if item_coletado == b'&':
                            nova_energia = min(MAX_ENERGY, flags[f'energia_{robot_char}'] + 20)
                            flags[f'energia_{robot_char}'] = nova_energia
                            log_msg += f". BATERIA COLETADA! Nova energia: {nova_energia}"
                        log(robot_char, log_msg)

        time.sleep(0.3)

    log(robot_char, "Processo encerrado.")

    robos_vivos = 0
    for r_id in ROBOT_IDS:
        if flags.get(f'energia_{r_id}', 0) > 0:
            robos_vivos += 1

    if robos_vivos <= 1:
        flags['game_over'] = True
        log(robot_char, f"Fim de jogo detectado ({robos_vivos} robôs restantes).")
