import os
from scheduler import Scheduler

def main():
    input_file = os.path.join("input", "processes.csv")
    escalonador = Scheduler()
    escalonador.load_processes_from_csv(input_file)
    escalonador.run()

if __name__ == "__main__":
    main()
