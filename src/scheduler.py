import csv
import os
from pcb import PCB

class Scheduler:
    """
    Escalonador de Processos baseado em Múltiplas Filas com Feedback (MLFQ).
    Gerencia as filas de Alta Prioridade, Baixa Prioridade e a fila de VO (I/O).
    """
    def __init__(self):
        self.queue_high = []    # Fila 1: Alta Prioridade
        self.queue_low = []     # Fila 2: Baixa Prioridade
        self.queue_io = []      # Fila 3: Fila de VO (Waiting)
        self.running_process = None
        self.quantum = 2        
        self.current_quantum = 0 
        self.clock = 0          
        self.log_messages = []  

    def log(self, message: str):
        msg = f"Tempo [{self.clock:03d}]: {message}"
        print(msg)
        self.log_messages.append(msg)

    def load_processes_from_csv(self, filepath: str):
        if not os.path.exists(filepath):
            self.log(f"ERRO: Arquivo de entrada {filepath} não encontrado.")
            return
        with open(filepath, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                pcb = PCB(int(row['PID']), int(row['PPID']), int(row['TIME_REMAINING']), int(row['IO_TYPE']))
                self.queue_high.append(pcb)
                self.log(f"Processo carregado e inserido na Fila Alta: {pcb}")

    def manage_io_queue(self):
        if not self.queue_io: return
        for pcb in list(self.queue_io):
            pcb.io_wait_time -= 1
            if pcb.io_wait_time <= 0:
                self.queue_io.remove(pcb)
                pcb.status = "READY"
                pcb.priority = "HIGH"  # Retorno de I/O dá bônus de prioridade
                self.queue_high.append(pcb)
                self.log(f"PID {pcb.pid} concluiu seu I/O e retornou para a Fila Alta.")

    def context_switch(self):
        if self.running_process is not None: return
        if self.queue_high:
            self.running_process = self.queue_high.pop(0)
        elif self.queue_low:
            self.running_process = self.queue_low.pop(0)
        else:
            return
        self.running_process.status = "RUNNING"
        self.current_quantum = 0
        self.log(f"Troca de contexto: CPU concedida ao PID {self.running_process.pid} (Fila: {self.running_process.priority})")

    def execute_cpu(self):
        if self.running_process is None:
            self.log("CPU ociosa, nenhum processo pronto para execução.")
            return
        self.running_process.time_remaining -= 1
        self.current_quantum += 1
        self.log(f"Executando PID {self.running_process.pid} | Restante: {self.running_process.time_remaining} | Quantum: {self.current_quantum}/{self.quantum}")

        if self.running_process.time_remaining <= 0:
            self.running_process.status = "TERMINATED"
            self.log(f"Processo PID {self.running_process.pid} finalizou sua execução.")
            self.running_process = None
            return

        if self.running_process.io_type > 0 and self.current_quantum == 1:
            self.running_process.status = "WAITING"
            self.running_process.io_wait_time = 3 if self.running_process.io_type == 1 else 5
            self.queue_io.append(self.running_process)
            self.log(f"PID {self.running_process.pid} solicitou I/O (Tipo: {self.running_process.io_type}) e foi para Fila VO.")
            self.running_process = None
            return

        if self.current_quantum >= self.quantum:
            self.running_process.status = "READY"
            if self.running_process.priority == "HIGH":
                self.running_process.priority = "LOW"
                self.log(f"Estouro de Quantum! PID {self.running_process.pid} foi REBAIXADO para a Fila Baixa.")
            else:
                self.log(f"Estouro de Quantum! PID {self.running_process.pid} voltou para o fim da Fila Baixa.")
            self.queue_low.append(self.running_process)
            self.running_process = None

    def run(self):
        self.log("--- INICIANDO SIMULAÇÃO ---")
        while self.queue_high or self.queue_low or self.queue_io or self.running_process:
            self.clock += 1
            self.manage_io_queue()
            self.context_switch()
            self.execute_cpu()
        self.log("--- SIMULAÇÃO CONCLUÍDA ---")
        self.save_log("output/execution_log.txt")

    def save_log(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            for line in self.log_messages:
                f.write(line + "\n")
        print(f"\n[Sucesso] Log salvo em: {filepath}")
    
