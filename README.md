
# 🧠 Arena dos Robôs – Batalha Autônoma em ASCII

Um jogo de batalha entre robôs autônomos, implementado em Python puro com **processos**, **memória compartilhada** e visualização **ASCII** em tempo real. Cada robô é um processo separado que toma decisões aleatórias de movimentação em um grid cheio de obstáculos, baterias e outros robôs.

## 📌 Visão Geral

Neste projeto, uma arena 2D é representada como um tabuleiro ASCII. Robôs com identificadores únicos (`A`, `B`, `C`, `D`) se movimentam pela arena até esgotarem sua energia ou serem eliminados. O último robô sobrevivente é declarado vencedor.

## 🎮 Componentes

- **`main.py`** – Inicializa a arena, spawna os processos dos robôs e o viewer.
- **`robot.py`** – Define a lógica de movimentação e energia de cada robô.
- **`viewer.py`** – Exibe a arena atualizada em tempo real no terminal.
- **`shared.py`** – Estruturas auxiliares para grid e memória compartilhada.
- **`constants.py`** – Define os parâmetros da arena, como dimensões e número de elementos.

## 🧠 Arquitetura

- Cada **robô** é um processo independente criado com `multiprocessing`.
- O **grid** é armazenado em memória compartilhada e acessado de forma concorrente com locks.
- O **viewer** roda em um processo separado, lendo continuamente o estado do grid para exibir a arena.
- As barreiras (`#`), baterias (`&`) e espaços livres (` `) são posicionados aleatoriamente no início.
- A **energia** dos robôs diminui a cada movimento. Eles morrem ao ficar sem energia.
- O jogo termina quando **só sobra um robô vivo**.

## 📂 Estrutura do Projeto

```
.
├── constants.py        # Constantes da arena
├── main.py             # Ponto de entrada da aplicação
├── robot.py            # Lógica dos robôs
├── shared.py           # Estruturas auxiliares (não usada diretamente no main atual)
├── viewer.py           # Exibição da arena em tempo real
└── README.md
```

## ▶️ Como Executar

Requisitos:
- Python 3.8+

Execute o jogo com:

```bash
python3 main.py
```

Você verá a arena atualizada no terminal a cada 0.1s com o estado atual dos robôs, obstáculos e baterias.

A versão robot_v2.py não está completamente finalizada, mas pode ser executada com:
```bash
python3 robot_v2.py
```

## ❓ Legenda

- `A`, `B`, `C`, `D` – Robôs ativos
- `#` – Barreira fixa
- `&` – Bateria (não interage no comportamento atual, mas prevista para extensões)
- `' '` – Espaço livre

## 🔧 Possíveis Extensões

- Duelos entre robôs (combate direto)
- Coleta de baterias para recuperar energia
- Robôs com IA mais sofisticada
- Logging em arquivo com histórico de turnos
- Interface gráfica (com `curses` ou GUI)

## 📜 Licença

Este projeto é educacional e pode ser usado livremente para fins acadêmicos.
