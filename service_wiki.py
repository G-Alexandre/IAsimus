# service_wiki.py
import os
import sys
import time
import threading
import subprocess
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

import win32event
import win32service
import win32serviceutil
import servicemanager

import schedule

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "log")
os.makedirs(LOG_DIR, exist_ok=True)

RUN_LOG = os.path.join(LOG_DIR, "service_run.log")
LOCK_FILE = os.path.join(LOG_DIR, ".update.lock")

def setup_logger():
    logger = logging.getLogger("WikiUpdateService")
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(RUN_LOG, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    handler.setFormatter(fmt)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

LOGGER = setup_logger()

def acquire_lock():
    if os.path.exists(LOCK_FILE):
        return False
    with open(LOCK_FILE, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))
    return True

def release_lock():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except Exception:
        pass

def run_pipeline():
    """
    Roda o pipeline (textos -> fotos -> unificado) via run_wiki_update.py
    Protegido por lock para evitar execuções simultâneas.
    """
    if not acquire_lock():
        LOGGER.info("Outra execução ainda está em andamento. Abortando este disparo.")
        return

    LOGGER.info("=== Disparo do pipeline iniciado ===")
    try:
        # Use o mesmo Python do sistema/venv:
        cmd = [sys.executable, os.path.join(BASE_DIR, "run_wiki_update.py")]
        proc = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)
        if proc.stdout:
            LOGGER.info(proc.stdout.strip())
        if proc.stderr:
            LOGGER.warning(proc.stderr.strip())
        if proc.returncode != 0:
            LOGGER.error(f"Pipeline finalizou com código {proc.returncode}")
        else:
            LOGGER.info("Pipeline concluído com sucesso.")
    except Exception as e:
        LOGGER.exception(f"Erro ao rodar pipeline: {e}")
    finally:
        release_lock()

class WikiUpdateService(win32serviceutil.ServiceFramework):
    _svc_name_ = "WikiUpdateServicePy"
    _svc_display_name_ = "Wiki Update Service (Python)"
    _svc_description_ = "Serviço que executa a atualização da wiki às 08:30 (seg–sex)."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.is_running = False
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("WikiUpdateServicePy: iniciando")
        LOGGER.info("Serviço iniciado.")

        # Agenda: seg–sex às 08:30
        schedule.clear()

        def job_guarded():
            # roda só se hoje é seg–sex
            if datetime.now().weekday() < 5:  # 0=seg, 4=sex
                run_pipeline()
            else:
                LOGGER.info("Dia não útil (sab/dom). Nenhuma ação.")

        schedule.every().monday.at("08:30").do(job_guarded)
        schedule.every().tuesday.at("08:30").do(job_guarded)
        schedule.every().wednesday.at("08:30").do(job_guarded)
        schedule.every().thursday.at("08:30").do(job_guarded)
        schedule.every().friday.at("08:30").do(job_guarded)

        # Loop principal do serviço
        while self.is_running:
            schedule.run_pending()
            # Espera pequena para não consumir CPU; também permite resposta rápida ao stop
            rc = win32event.WaitForSingleObject(self.stop_event, 1000)  # 1 segundo
            if rc == win32event.WAIT_OBJECT_0:
                break

        LOGGER.info("Serviço parando.")
        servicemanager.LogInfoMsg("WikiUpdateServicePy: parando")

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(WikiUpdateService)
