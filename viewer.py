import time
from constants import GRID_WIDTH, GRID_HEIGHT		# Importa as constantes de constants.py

def char_repr(b):
    """Converte byte para caractere ASCII para exibir no terminal."""
    if b == b' ':
        return ' '
    return b.decode('utf-8')

def viewer_process(grid, flags):
    print("=== Arena dos Robôs (Viewer) ===\n")

    while not flags['game_over']:			# acesso direto, sem .value
        # Monta uma string para o grid atual
        output = []
        for y in range(GRID_HEIGHT):
            linha = ''
            for x in range(GRID_WIDTH):
                idx = y * GRID_WIDTH + x
                linha += char_repr(grid[idx])
            output.append(linha)

        # Limpa tela e imprime o grid (usando ANSI simples)
        print("\033[H\033[J", end='')			# ANSI escape para limpar tela
        print('\n'.join(output))
        print("\nCtrl+C para sair.")

        time.sleep(0.1)

    print("Viewer finalizado - jogo acabou.")
