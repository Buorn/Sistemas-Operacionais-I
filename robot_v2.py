import time
import random
import os  # NOVO: necessário para gravar os arquivos de log
import sys  # NOVO: para capturar entrada de teclado do jogador
import termios  # NOVO: para leitura não bloqueante do teclado
import tty  # NOVO: usado com termios
import threading  # NOVO: para rodar o input do jogador em paralelo
import shared_v2

# TO DO: criar função que será o target do processo. Essa função vai utilizar a clasze Robot
"""
Classe básica para representar um robô no jogo.
Cada robô tem:
    - ID
    - força (1-10)
    - energia (10-100)
    - velocidade (1-5)
    - posição
    - status (1 = vivo, 0 = morto)
    - arquivo de log
    - threads de tomada de decisão (movimento, coleta, duelo) e housekeeping
"""
class Robot:
    def __init__(self, id, grid, grid_mutex):
        self.id = id
        self.strength = random.randint(1, 10)
        self.energy = 100
        self.speed = random.randint(1, 5)
        self.position = self.get_initial_position()
        self.status = 1
        self.log_file = f"log_{self.id}.txt"
        self.sense_act_thread = threading.Thread(target=self.sense_act, args=(grid,))
        self.housekeeping_thread = threading.Thread(target=self.housekeeping, args=(grid,))

    """
    Método auxiliar para obter a posição inicial do robô.
    Garante que a posição inicial não seja uma barreira ou ocupada por outro robô.
    """
    def get_initial_position(self, grid, grid_mutex):
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            
            if grid[x][y] == b' ':
                return (x, y)

    """
    Método auxiliar para registrar ações do robô em arquivo.
    Registra a mensagem com o horário atual.
    """
    def log(robot, message):
    with open(robot.log_file, "a") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {message}\n")  # grava mensagem com horário

    """
    Método de movimento: escolhe um passo aleatório e move o robô na grade.
    """
    def move(self):
        # Escolhe um passo e uma direção aleatórias
        step = random.randint(1,self.speed)
        direction = random.choice()
        
        while step[0] > 0 or step[1] > 0:
            new_x = self.position[0] + step[0]
            new_y = self.position[1] + step[1]

            # Verifica se a nova posição está dentro dos limites da grade
            if 0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT:
                # Verifica se a nova posição não é uma barreira
                if grid[new_y * GRID_WIDTH + new_x] != b'#':
                    # Move o robô para a nova posição
                    self.position = (new_x, new_y)
                    grid[self.position[1] * GRID_WIDTH + self.position[0]] = b' '

            
            
    """
    Método de duelo: realiza uma batalha entre dois robôs.
    """
    def battle(self, other_robot):
        self.log(f"{self.id} iniciou batalha com {other_robot.id}.\n")
        other_robot.log(f"{self.id} desafiou {other_robot.id} para uma batalha.\n")

        # Calcula o poder de ataque de cada robô
        power_self = 2 * self.strength + self.energy
        power_other = 2 * other_robot.strength + other_robot.energy

        if power_self > power_other:
            # Se robô que chamou o método vencer, muda o status do outro robô para "morto"
            self.log(f"{self.id} venceu a batalha contra {other_robot.id}")
            other_robot.log(f"{other_robot.id} perdeu a batalha contra {self.id}")
            other_robot.status = 0

        elif power_self < power_other:
            # Se robô que chamou o método perder, muda o próprio status para "morto"
            self.log(f"{self.id} perdeu a batalha contra {other_robot.id}")
            other_robot.log(f"{other_robot.id} venceu a batalha contra {self.id}")
            self.status = 0

        else:
            # Em caso de empate, ambos os robôs mudam o status para "morto"
            self.status = 0
            self.log(f"{self.id} e {other_robot.id} empataram na batalha. Ambos foram destruídos.\n")
            other_robot.status = 0
            other_robot.log(f"{other_robot.id} e {self.id} empataram na batalha. Ambos foram destruídos.\n")
    
    """
    Método de recarga: recarrega a energia do robô.
    Se a energia ultrapassar 100, é ajustada para 100.
    """
    def recharge(self, amount):
        self.energy += amount
        if self.energy > 100:
            self.energy = 100
        self.log(f"{self.id} recarregou sua energia. Energia atual: {self.energy}\n")
    
    def get_position(self):
        return self.position
    
    def set_position(self, x, y):
        self.position = (x, y)
        self.log(f"{self.id} se moveu para a posição {self.position}")
        self.log(f"Robô {self.id} iniciado com energia máxima")
        pos = self.get_position()
        if pos is None:
            self.log("Erro: posição inicial não encontrada. Encerrando.")
            return
        self.sense_act_thread.start()
        self.housekeeping_thread.start()
        self.log(f"Robô {self.id} iniciado com energia máxima")

    def sense_act(self, grid)

    def housekeeping(self, grid)

"""
Classe derivada de Robot para representar um robô controlado por um jogador.
Além das funcionalidades básicas de um robô, ela inclui a capacidade de receber entradas do teclado para controlar o robô.
"""
class PlayerRobot(Robot):
    def __init__(self, id):
        super().__init__()
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