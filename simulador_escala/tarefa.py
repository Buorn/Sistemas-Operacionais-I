from threading import Thread
from multiprocessing import Queue
from time import sleep
import random

class Consumidor:
  
def consumidor(q, idt):
    while True:
        val = q.get(timeout=5)
        if val is None:
            print("Encerrando consumidor...")
            break
        tarefa = val * random.randint(1, 1000)
        print(f"ID:{idt}\nValor recebido: {val}\nValor Processado: {tarefa}")
        sleep(1)

def produtor(itens, q):
    for i in range(itens):
        msg = random.randint(1, 1000)
        q.put(msg)
    q.put(None)


queue = Queue()
prod = Thread(target=produtor, args=(15, queue))
cons1 = Thread(target=consumidor, args=(queue,1))
cons2 = Thread(target=consumidor, args=(queue,2))

prod.start()
cons1.start()
cons2.start()
prod.join()
cons1.join()
cons2.join()
