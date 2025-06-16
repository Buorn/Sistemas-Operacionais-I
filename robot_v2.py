import multiprocessing
import threading
import ctypes
import random
import time
import sys
import termios
import tty
import os

# Definição das constantes
# Dimensões do tabuleiro
GRID_WIDTH = 40
GRID_HEIGHT = 20

# Energia máxima que um robô pode ter e valor da bateria
MAX_ENERGY = 100
BATTERY_VALUE = 20

# Número total de robôs na arena
NUM_ROBOTS = 4

# Número de baterias a serem colocadas no grid
NUM_BATTERIES = 5

# Número de barreiras fixas a serem colocadas no grid
NUM_BARRIERS = 30

# Número de casas visíveis para o robô
VISIBILITY = 10

# Função para encontrar célula vazia no grid. Utilizada na inicialização dos robôs
def find_empty_cell(grid):
    while True:
        #print("find_empty_cell WHILE 1")
        #time.sleep(0.3)
        x = random.randint(0, GRID_HEIGHT - 1)
        y = random.randint(0, GRID_WIDTH - 1)

        #print("find_empty_cell WHILE 2")
        # Verifica se a célula está vazia
        if grid[x][y] == b' ':
            print("find_empty_cell IF")
            time.sleep(1)
            return (x, y)

# Memória compartilhada para as flags
class Flags(ctypes.Structure):
    _fields_ = [
        ("init_done", ctypes.c_bool),
        ("game_over", ctypes.c_int),
        ("winner", ctypes.c_char),
    ]

""""
Estrutura de dados para representar um robô no jogo.
Utiliza ctypes para garantir a manipulação de dados entre processos.
Cada robô tem:
    - ID
    - força (1-10)
    - energia (10-100)
    - velocidade (1-5)
    - posição (x, y)
    - status (True = vivo, False = morto)
    - arquivo de log para registrar ações
"""
class RobotStruct(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_char),
        ("strength", ctypes.c_int),
        ("energy", ctypes.c_int),
        ("speed", ctypes.c_int),
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("status", ctypes.c_bool),
    ]

"""
Classe básica para representar um robô no jogo.
A classe inclui métodos para:
    - iniciar o robô e as threads para tomada de decisão e housekeeping
    - obter a posição inicial
    - mover o robô
    - batalhar com outro robô
    - recarregar energia
    - obter e definir posição
"""
class Robot():
    def __init__(self, id, grid, robots_array, flags, robotStruct: RobotStruct, grid_mutex, robots_mutex, flags_mutex):
        self.id = id
        self.grid = grid
        self.robots_array = robots_array
        self.flags = flags
        self.robotStruct = robotStruct
        self.grid_mutex = grid_mutex
        self.robots_mutex = robots_mutex
        self.flags_mutex = flags_mutex

    # Método para identificação de baterias e robôs no grid
    def sense(self):
        #print(f"SENSE Robô {self.robotStruct.id.decode()} - ({self.robotStruct.x},{self.robotStruct.y})")
        #time.sleep(2)
        id = self.robotStruct.id
        x_robot = self.robotStruct.x
        y_robot = self.robotStruct.y

        # Define os limites da visão do robô
        left = x_robot - VISIBILITY if x_robot - VISIBILITY > 0 else 0
        right = x_robot + VISIBILITY if x_robot + VISIBILITY < GRID_WIDTH else GRID_WIDTH
        top = y_robot - VISIBILITY if y_robot - VISIBILITY > 0 else 0
        bottom = y_robot + VISIBILITY if y_robot + VISIBILITY < GRID_HEIGHT else GRID_HEIGHT

        # Armazena baterias e robôs por perto
        btrs = []
        rbts = []

        # Percorre a visão do robô
        for row in range(top, bottom):
            for col in range(left, right):
                cell = self.grid[row * GRID_WIDTH + col]
                if cell == b'&': # Bateria
                    btrs.append((row, col))

                elif 65 <= ord(cell) <= 90 and cell != id: # Robô
                    rbts.append((row, col, cell.decode()))

        # Ordena as listas de baterias e robôs por distância
        btrs.sort(key=lambda x: (x[0] - x_robot) ** 2 + (x[1] - y_robot) ** 2)
        rbts.sort(key=lambda x: (x[0] - x_robot) ** 2 + (x[1] - y_robot) ** 2)

        print(f"Robô {self.robotStruct.id.decode()}, ({x_robot},{y_robot}) - Baterias: {btrs}, Robôs: {rbts}")
        time.sleep(1)

        return btrs, rbts

    # Método para tomada de decisão e ação do robô
    def act(self, btrs, rbts):
        id = self.robotStruct.id
        x_robot = self.robotStruct.x
        y_robot = self.robotStruct.y
        energy = self.robotStruct.energy
        speed = self.robotStruct.speed

        # Prioridade para baterias, depois para robôs. Se não houver, movimento aleatório.
        target = btrs[0] if btrs else (rbts[0] if rbts else random.choice([(0, 1), (1, 0), (0, -1), (-1, 0)]))

        # Movimento para o alvo
        dx = target[0] - x_robot
        dy = target[1] - y_robot

        # Movimento unitário
        move_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        move_y = 0 if dy == 0 else (1 if dy > 0 else -1)

        # Escolhe direção para andar para não fazer movimentos diagonais
        choice = random.choice([0, 1])

        if choice == 0: # Escolhe mover na direção de x
            new_x = x_robot + move_x
            if new_x < 0 or new_x >= GRID_WIDTH: # Verifica se o movimento está dentro dos limites do grid
                new_x = x_robot
            new_y = y_robot

        else: # Escolhe mover na direção de y
            new_x = x_robot
            new_y = y_robot + move_y
            if new_y < 0 or new_y >= GRID_HEIGHT: # Verifica se o movimento está dentro dos limites do grid
                new_y = y_robot
        
        # Faz a movimentação do robô e toma ação
        while energy > 0 and self.flags.game_over:
            #print(f"ACT Robô {self.robotStruct.id.decode()} - ({self.robotStruct.x},{self.robotStruct.y}) - Target: {target}")
            #time.sleep(1)
            #print("Loop ACT")
            #time.sleep(1)
            time.sleep(0.2 * speed)
            with self.grid_mutex:
                # Obtém o conteúdo da célula do grid da nova posição
                cell = self.grid[new_x * GRID_WIDTH + new_y]
                
                if cell == b' ': # Movimento para posição vazia
                    self.grid[x_robot * GRID_WIDTH + y_robot] = b' '
                    self.grid[new_x * GRID_WIDTH + new_y] = self.robotStruct.id

                    #print(f"Robô {self.robotStruct.id.decode()} movimentando de ({x_robot},{y_robot}) para vazia ({new_x},{new_y})")
                    #time.sleep(1)

                    # Atualiza a posição do robô
                    with self.robots_mutex:
                        self.robotStruct.x = new_x
                        self.robotStruct.y = new_y
                        self.robotStruct.energy -= 1

                    # Verifica se a energia do robô chegou a zero
                    if self.robotStruct.energy == 0:
                        self.grid[new_x * GRID_WIDTH + new_y] = b' '
                        self.robotStruct.status = False
                        with self.flags_mutex:
                            self.flags.game_over -= 1

                    return

                elif cell == b'&': # Movimento para posição com bateria
                    print(f"Robô {self.robotStruct.id.decode()} recarregando em ({new_x},{new_y})")
                    self.grid[x_robot * GRID_WIDTH + y_robot] = b' '
                    self.grid[new_x * GRID_WIDTH + new_y] = self.robotStruct.id
                    self.recharge(BATTERY_VALUE)
                    
                    return

                elif 65 <= ord(cell) <= 90:
                    # Realiza o duelo com o robô adversário
                    with self.robots_mutex:
                        print(f"Robô {self.robotStruct.id.decode()} duela com {cell.decode()}")
                        time.sleep(2)
                        self.battle(cell)

                        # Verifica se a energia do robô chegou a zero
                        if self.robotStruct.energy == 0:
                            self.status = False
                            with self.flags_mutex:
                                self.flags.game_over -= 1

                    return

                elif self.grid[new_x * GRID_WIDTH + new_y] == b'#':
                    # Movimento aleatório em caso de barreira
                    move_x, move_y = random.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])
                    new_x = x_robot + move_x
                    new_y = y_robot + move_y
                    continue

                else:
                    return

    """
    Método de duelo: realiza uma batalha entre dois robôs.
    """
    def battle(self, other_robot_id):
        # Obtém dados e calula poder do robô que chamou o método
        id_self = self.robotStruct.id
        x_self  = self.robotStruct.x
        y_self = self.robotStruct.y
        power_self = 2 * self.robotStruct.strength + self.robotStruct.energy
        
        # Obtém dados e calcula poder do robô adversário
        id_other = self.robots_array[ord(other_robot_id) - 65].id
        x_other  = self.robots_array[ord(other_robot_id) - 65].x
        y_other = self.robots_array[ord(other_robot_id) - 65].y
        power_other = 2 * self.robots_array[ord(other_robot_id) - 65].strength + self.robots_array[ord(other_robot_id) - 65].energy

        if power_self > power_other:
            # Se robô que chamou o método vencer, muda o status do outro robô para "morto"
            self.robots_array[id_other].status = False
            self.grid[x_self * GRID_WIDTH + y_self] = b' '
            self.grid[x_other * GRID_WIDTH + y_other] = self.robotStruct.id
            self.robotStruct.x = x_other
            self.robotStruct.y = y_other
            self.robotStruct.energy -= 1
            
            with self.flags_mutex:
                self.flags.game_over -= 1
                if self.flags.game_over == 0:
                    self.flags.winner = self.robotStruct.id

                return

        elif power_self < power_other:
            # Se robô que chamou o método perder, muda o próprio status para "morto"
            self.status = False
            self.grid[x_self * GRID_WIDTH + y_self] = b' '
            self.robots_array[ord(other_robot_id) - 65].energy -= 1
            
            with self.flags_mutex:
                self.flags.game_over -= 1
                if self.flags.game_over == 0:
                    self.flags.winner = self.robots_array[id_other].id

                return

        else:
            # Em caso de empate, ambos os robôs mudam o status para "morto"
            self.status = False
            self.grid[self.robotStruct.x * GRID_WIDTH + self.robotStruct.y] = b' '
            
            self.robots_array[ord(other_robot_id) - 65].status = False
            self.grid[x_other * GRID_WIDTH + y_other] = b' '
            
            with self.flags_mutex:
                self.flags.game_over -= 2
                if self.flags.game_over == 0:
                    self.flags.winner = b'-'
                    
                return
    
    """
    Método de recarga: recarrega a energia do robô.
    Se a energia ultrapassar 100, é ajustada para 100.
    """
    def recharge(self, amount):
        self.robotStruct.energy += amount if self.robotStruct.energy <= MAX_ENERGY else MAX_ENERGY

    """
    Método auxiliar para registrar ações do robô em arquivo.
    Registra a mensagem com o horário atual.
    """
    #def log(self, robot, message):
    #with open(robot.log_file, "a") as f:
        #f.write(f"[{time.strftime('%H:%M:%S')}] {message}\n")  # grava mensagem com horário



"""
Classe derivada de Robot para representar um robô controlado por um jogador.
Além das funcionalidades básicas de um robô, ela inclui a capacidade de receber entradas do teclado para controlar o robô.
"""
"""
class PlayerRobot(Robot):
    def __init__(self, id, grid, robots_array, robotStruct: RobotStruct, grid_mutex, robots_mutex, flags_mutex):
        super().__init__(id, grid, robots_array, robotStruct, grid_mutex, robots_mutex, flags_mutex)
        self.input_thread = threading.Thread(target=self.get_input)

    def get_input(self):
        while True:
            key = get_key()
            if key == 'q':  # Pressione 'q' para sair
                self.log("Jogador saiu do jogo.")
                break
            elif key in ['w', 'a', 's', 'd']:  # Movimentos básicos
                self.log(f"Jogador pressionou: {key}")
                # Aqui você pode implementar a lógica de movimento do robô
            else:
                self.log(f"Tecla desconhecida pressionada: {key}")
            time.sleep(0.1)
"""

"""
Classe para gerenciar o processo de um robô.
Inclui a lógica de inicialização e execução do robô.
"""
class RobotProcess(multiprocessing.Process):
    def __init__(self, id, grid, robots_array, flags, grid_mutex, robots_mutex, flags_mutex):
        super().__init__()
        self.id = id
        self.grid = grid
        self.robots_array = robots_array
        self.flags = flags
        self.robot = Robot(chr(id+65), grid, robots_array, flags, robots_array[id], grid_mutex, robots_mutex, flags_mutex)
        self.grid_mutex = grid_mutex
        self.robots_mutex = robots_mutex
        self.flags_mutex = flags_mutex
        self.log_file = f"log_{self.robot.id}.txt"

    """
    Método principal que inicia o robô e é utilizado como target do processo.
    Inicializa o grid, se for o primeiro a executar, e inicia as threads de tomada de decisão e housekeeping.
    """
    def run(self):
        # Inicializa o grid se for o primeiro robô a executar
        with self.flags_mutex:
            if not self.flags.init_done:
                self.initialization()
                self.flags.init_done = True
            
        # Inicia as threads de tomada de decisão e housekeeping
        sense_act_thread = threading.Thread(target=self.sense_act)
        sense_act_thread.start()
        housekeeping_thread = threading.Thread(target=self.housekeeping)
        housekeeping_thread.start()

        # Aguarda o término das threads
        sense_act_thread.join()
        housekeeping_thread.join()

    # Função para encontrar célula vazia no grid. Utilizada na inicialização dos robôs
    def find_empty_cell(self):
        while True:
            x = random.randint(0, GRID_HEIGHT - 1)
            y = random.randint(0, GRID_WIDTH - 1)

            #print("find_empty_cell WHILE 2")
            # Verifica se a célula está vazia
            if self.grid[x * GRID_WIDTH + y] == b' ':
                return (x, y)

    """
    Método de inicialização: realiza a inicialização dos segmentos de memória compartilhada.
    """
    def initialization(self):
        with self.grid_mutex:
            # Inicializa o grid com espaços vazios
            for row in range(GRID_HEIGHT):
                for col in range(GRID_WIDTH):
                    self.grid[row * GRID_WIDTH + col] = b' '
                    
            # Posiciona as barreiras
            for _ in range(NUM_BARRIERS):
                while True:
                    x = random.randint(0, GRID_HEIGHT - 1)
                    y = random.randint(0, GRID_WIDTH - 1)
                    if self.grid[x * GRID_WIDTH + y] == b' ':
                        self.grid[x * GRID_WIDTH + y] = b'#'
                        break

            # Posiciona as baterias
            for _ in range(NUM_BATTERIES):
                while True:
                    x = random.randint(0, GRID_HEIGHT - 1)
                    y = random.randint(0, GRID_WIDTH - 1)
                    if self.grid[x * GRID_WIDTH + y] == b' ':
                        self.grid[x * GRID_WIDTH + y] = b'&'
                        break

            # Posiciona os robôs
            for rbt in range(NUM_ROBOTS):
                with self.robots_mutex:
                    self.robots_array[rbt].id = chr(rbt + 65).encode()
                    self.robots_array[rbt].strength = random.randint(1, 10)
                    self.robots_array[rbt].energy = random.randint(10, 100)
                    self.robots_array[rbt].speed = random.randint(1, 5)
                    self.robots_array[rbt].x, self.robots_array[rbt].y = self.find_empty_cell()
                    self.grid[self.robots_array[rbt].x * GRID_WIDTH + self.robots_array[rbt].y] = self.robots_array[rbt].id
                    self.robots_array[rbt].status = True

    """
    Loop do robô: realiza a tomada de decisão e ação do robô.
    """
    def sense_act(self):
        while self.robot.robotStruct.status and self.flags.game_over > 0:
            btrs, rbts = self.robot.sense()
            self.robot.act(btrs, rbts)

    """
    Método de housekeeping: realiza a manutenção do robô.
    """
    def housekeeping(self):
        while self.robot.robotStruct.status and self.flags.game_over > 0:
            continue

class ViewerProcess(multiprocessing.Process):
    def __init__(self, grid, robots_array, flags, refresh_rate=0.2):
        super().__init__()
        self.grid = grid
        self.robots_array = robots_array
        self.flags = flags
        self.refresh_rate = refresh_rate

    def run(self):
        while True:
            if self.flags.init_done:
                os.system('cls' if os.name == 'nt' else 'clear')
                print("=== Arena dos Robôs (Viewer) ===\n")
                
                for r in range(GRID_HEIGHT + 2):
                    if r == 0 or r == GRID_HEIGHT + 1:
                        print('#' * (GRID_WIDTH + 1))
                        continue
                    for c in range(GRID_WIDTH + 2):
                        if c == 0 or c == GRID_WIDTH + 1:
                            print('#', end = '')
                        else:
                            print(self.grid[(r - 1)  * GRID_WIDTH + (c - 1)].decode(), end = '')
                    print()

                print()
                for i in range(NUM_ROBOTS):
                    print(f"Robô {self.robots_array[i].id.decode()}: Energia = {self.robots_array[i].energy}, Status = {'Vivo' if self.robots_array[i].status else 'Morto'}, Posição = ({self.robots_array[i].x},{self.robots_array[i].y})")
                print("\nCtrl+C para sair.")
                time.sleep(self.refresh_rate)

def main():
    # Flags na memória compartilhada
    flags = multiprocessing.RawValue(Flags)

    flags.init_done = False
    flags.game_over = NUM_ROBOTS-1
    flags.winner=b' '

    # Grid na memória compartilhada
    gridShared = multiprocessing.RawArray(ctypes.c_char, GRID_WIDTH * GRID_HEIGHT)

    # Memória compartilhada para o array de robôs
    robots_array = multiprocessing.RawArray(RobotStruct, NUM_ROBOTS)
    robos = []

    # Criação dos mutexes
    grid_mutex = multiprocessing.Lock()
    robots_mutex = multiprocessing.Lock()
    flags_mutex = multiprocessing.Lock()

    # Cria os processos para os robôs
    for i in range(NUM_ROBOTS):
        robot_process = RobotProcess(i, gridShared, robots_array, flags, grid_mutex, robots_mutex, flags_mutex)
        robot_process.start()
        robos.append(robot_process)

    # Cria o processo viewer
    viewer = ViewerProcess(gridShared, robots_array, flags)
    viewer.start()

    # Aguarda o término dos processos dos robôs
    for r in range(len(robos)):
        robos[r].join()

    # Depois que robôs terminam, sinaliza fim pro viewer
    flags.game_over = 0

    # Espera o viewer terminar
    viewer.join()

    print("Jogo finalizado.")

if __name__ == "__main__":
    main()