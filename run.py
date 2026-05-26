import subprocess
import sys
import time

def main():
    print("--- Iniciando o Memorarq ---")
    
    # Caminho direto para o Python dentro do ambiente virtual do backend
    backend_cmd = r"venv\Scripts\python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000"
    
    # Comando do frontend
    frontend_cmd = "npm start"
    
    print("-> Subindo Backend (FastAPI)...")
    backend_process = subprocess.Popen(backend_cmd, cwd="backend", shell=True)
    
    print("-> Subindo Frontend (Express)...")
    frontend_process = subprocess.Popen(frontend_cmd, cwd="frontend", shell=True)
    
    try:
        # Mantém o script principal rodando para segurar os subprocessos
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Quando pressionar Ctrl+C, encerra ambos os servidores de forma limpa
        print("\n--- Encerrando o Memorarq ---")
        backend_process.terminate()
        frontend_process.terminate()
        print("Processos encerrados com sucesso.")

if __name__ == "__main__":
    main()