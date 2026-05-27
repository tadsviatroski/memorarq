import os
import urllib.request
import zipfile
import subprocess
import shutil
import ssl

# Descobre a raiz do projeto (uma pasta acima da 'backend')
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BIN_DIR = os.path.join(BASE_DIR, 'bin')

# URLs de download - Tesseract redirecionado para o Internet Archive para burlar firewall
POPPLER_URL = "https://github.com/oschwartz10612/poppler-windows/releases/download/v24.02.0-0/Release-24.02.0-0.zip"
TESSERACT_URL = "https://web.archive.org/web/20231005183842id_/https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe"
TESSDATA_POR_URL = "https://raw.githubusercontent.com/tesseract-ocr/tessdata/main/por.traineddata"

def download_file(url, dest):
    print(f" -> Baixando {url.split('/')[-1]} (Isso pode levar alguns minutos)...")
    
    # Ignora bloqueios de certificado SSL e força perfil de navegador
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0'}
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response, open(dest, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
    except Exception as e:
        print(f"\n[ERRO FATAL] Ocorreu um problema de rede: {e}")
        print(f"Não foi possível baixar automaticamente. Por favor, acesse o link abaixo no seu navegador:\n{url}")
        print(f"Salve o arquivo dentro da pasta 'bin' do projeto.")
        import sys
        sys.exit(1)

def setup_poppler():
    poppler_dir = os.path.join(BIN_DIR, 'poppler')
    if os.path.exists(os.path.join(poppler_dir, 'Library', 'bin', 'pdftoppm.exe')):
        return

    print("\n[SETUP] Poppler ausente. Iniciando instalacao automatica...")
    os.makedirs(BIN_DIR, exist_ok=True)
    zip_path = os.path.join(BIN_DIR, 'poppler.zip')
    
    download_file(POPPLER_URL, zip_path)
    
    print(" -> Extraindo Poppler...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(BIN_DIR)
    
    extracted_folder = os.path.join(BIN_DIR, 'poppler-24.02.0-0')
    if os.path.exists(extracted_folder):
        if os.path.exists(poppler_dir):
            shutil.rmtree(poppler_dir) 
        os.rename(extracted_folder, poppler_dir)
        
    os.remove(zip_path)
    print(" -> Poppler instalado com sucesso.")

def setup_tesseract():
    tesseract_dir = os.path.join(BIN_DIR, 'Tesseract-OCR')
    if not os.path.exists(os.path.join(tesseract_dir, 'tesseract.exe')):
        print("\n[SETUP] Tesseract ausente. Iniciando instalacao automatica portatil...")
        os.makedirs(BIN_DIR, exist_ok=True)
        installer_path = os.path.join(BIN_DIR, 'tesseract_installer.exe')
        
        download_file(TESSERACT_URL, installer_path)
        
        print(" -> Instalando Tesseract silenciosamente na pasta bin...")
        subprocess.run([installer_path, '/S', f'/D={tesseract_dir}'], check=True)
        os.remove(installer_path)
        print(" -> Tesseract instalado.")
        
    tessdata_dir = os.path.join(tesseract_dir, 'tessdata')
    por_data_path = os.path.join(tessdata_dir, 'por.traineddata')
    
    if not os.path.exists(por_data_path):
        print("\n[SETUP] Pacote de idioma Portugues ausente. Baixando...")
        os.makedirs(tessdata_dir, exist_ok=True)
        download_file(TESSDATA_POR_URL, por_data_path)
        print(" -> Idioma instalado com sucesso.")

if __name__ == "__main__":
    setup_poppler()
    setup_tesseract()