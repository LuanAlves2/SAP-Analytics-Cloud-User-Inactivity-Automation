"""
Wrapper para rodar main.py como servico Windows via NSSM.
Executa toda sexta-feira as 10:00.
"""
import os
import subprocess
import sys
import time
from datetime import datetime

import schedule

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = sys.executable
MAIN_SCRIPT = os.path.join(SCRIPT_DIR, "main.py")
DIA_SEMANA = "friday"
HORARIO = "10:00"
TIMEOUT_SEGUNDOS = 1800  # 30 minutos


def agora():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def executar_main():
    print(f"[{agora()}] Iniciando execucao do main.py...", flush=True)
    # Forca UTF-8 no processo filho: sem isso, qualquer caractere fora do cp1252
    # impresso pelo main.py derruba a execucao quando a saida vai para um pipe.
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    try:
        resultado = subprocess.run(
            [PYTHON_EXE, MAIN_SCRIPT],
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=TIMEOUT_SEGUNDOS,
        )
        print(resultado.stdout, flush=True)
        if resultado.stderr:
            print(f"[STDERR] {resultado.stderr}", flush=True)
        status = "OK" if resultado.returncode == 0 else "COM FALHAS"
        print(f"[{agora()}] Execucao finalizada {status} (codigo: {resultado.returncode})", flush=True)
    except subprocess.TimeoutExpired:
        print(f"[{agora()}] [ERRO] Timeout: execucao excedeu {TIMEOUT_SEGUNDOS // 60} minutos", flush=True)
    except Exception as e:
        print(f"[{agora()}] [ERRO] {type(e).__name__}: {e}", flush=True)


getattr(schedule.every(), DIA_SEMANA).at(HORARIO).do(executar_main)

print(f"Servico SAC iniciado em {agora()}", flush=True)
print(f"Agendado para: toda {DIA_SEMANA} as {HORARIO}", flush=True)
print(f"Python: {PYTHON_EXE}", flush=True)
print(f"Script: {MAIN_SCRIPT}", flush=True)
print(f"Proxima execucao: {schedule.next_run()}", flush=True)

if "--agora" in sys.argv:
    # Util para testar o servico sem esperar o agendamento
    executar_main()

while True:
    schedule.run_pending()
    time.sleep(60)
