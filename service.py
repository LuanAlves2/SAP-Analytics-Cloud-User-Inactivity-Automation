"""
Wrapper para rodar main.py como servico Windows via NSSM.
Executa toda sexta-feira as 10:00.
"""
import schedule
import time
import subprocess
import sys
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = sys.executable
MAIN_SCRIPT = os.path.join(SCRIPT_DIR, "main.py")


def executar_main():
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"[{agora}] Iniciando execucao do main.py...")
    try:
        resultado = subprocess.run(
            [PYTHON_EXE, MAIN_SCRIPT],
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutos de timeout
        )
        print(resultado.stdout)
        if resultado.stderr:
            print(f"[STDERR] {resultado.stderr}")
        print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] Execucao finalizada (codigo: {resultado.returncode})")
    except subprocess.TimeoutExpired:
        print(f"[ERRO] Timeout: execucao excedeu 30 minutos")
    except Exception as e:
        print(f"[ERRO] {e}")


# Agenda para toda sexta-feira as 10:00
schedule.every().friday.at("10:00").do(executar_main)

print(f"Servico SAC iniciado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
print(f"Agendado para: toda sexta-feira as 10:00")
print(f"Script: {MAIN_SCRIPT}")
print(f"Proxima execucao: {schedule.next_run()}")

while True:
    schedule.run_pending()
    time.sleep(60)
