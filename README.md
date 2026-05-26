# Memorarq

O **Memorarq** é uma ferramenta de gestão de documentos focado na extração de texto (OCR) utilizando Visão Computacional, com correção ortográfica contextualizada alimentada por Inteligência Artificial (Modelo BERTimbau).

## 🚀 Funcionalidades

- **Upload e Leitura**: Suporte para Imagens e PDFs.
- **OCR Avançado**: Pipeline de Visão Computacional (OpenCV) para limpar as imagens antes da extração pelo Tesseract-OCR.
- **Edição de Texto Integrada**: Interface fluída que permite editar textos paralelamente à visualização do documento original.
- **Correção com IA**: Revisão ortográfica contextual baseada em redes neurais (BERT).
- **Exportação**: Geração de arquivos `.txt` e `.pdf` formatados on-the-fly.

---

## 💻 Pré-requisitos (Ferramentas do Sistema)

Considerando uma máquina com sistema operacional **Windows** rodando o projeto pela primeira vez, você precisará das ferramentas abaixo devidamente instaladas e configuradas:

1. **Node.js e NPM**: Para rodar o servidor frontend. Baixe aqui.
2. **Python 3.9+**: Para rodar a API do backend. Certifique-se de marcar a opção *"Add Python to PATH"* durante a instalação. Baixe aqui.
3. **Tesseract-OCR**: Motor de extração de texto.
   - Baixe o instalador para Windows (ex: UB-Mannheim).
   - Instale-o (geralmente em `C:\Program Files\Tesseract-OCR\`).
   - **Importante:** Adicione o caminho do Tesseract às Variáveis de Ambiente (`PATH`) do Windows. Adicionalmente, você precisará do pacote de idioma Português (`por.traineddata`).
4. **Poppler**: Ferramenta necessária para a conversão de PDFs em imagens.
   - Baixe a versão para Windows aqui (Release v25.01.0 ou compatível).
   - Extraia e renomeie/mova a pasta exatamente para: `C:\Program Files\poppler-25.12.0` (Conforme configurado na constante `POPPLER_PATH` do sistema). Caso instale em outro local, atualize a variável no arquivo `backend/services/ocr_service.py`.

---

## ⚙️ Instalação e Configuração

Abra um terminal (PowerShell ou Git Bash) e siga o passo a passo:

### 1. Clonar o Repositório
```bash
git clone https://github.com/SEU_USUARIO/memorarq.git
cd memorarq
```

### 2. Configurar o Frontend
Navegue até a pasta do frontend e instale os pacotes do Node:
```bash
cd frontend
npm install
cd ..
```

### 3. Configurar o Backend
O projeto utiliza um script central (`run.py`) que espera encontrar o ambiente virtual (venv) **obrigatoriamente** nomeado como `venv` dentro da pasta `backend`.

```bash
cd backend
# Criar ambiente virtual
python -m venv venv

# Ativar o ambiente virtual
# No Windows:
.\venv\Scripts\activate

# Instalar as dependências do Python necessárias
pip install fastapi uvicorn python-multipart torch transformers pyspellchecker Levenshtein pytesseract pdfplumber pdf2image Pillow opencv-python numpy reportlab

cd ..
```

*Atenção: A primeira vez que a ferramenta de IA (Correção com BERT) for utilizada, o sistema precisará baixar o modelo `neuralmind/bert-base-portuguese-cased` através da internet (aprox. 400MB).*

---

## ▶️ Como Executar o Sistema

Com tudo configurado, você não precisará abrir dois terminais manuais. O script raiz `run.py` se encarrega de subir o Frontend e o Backend simultaneamente.

1. No terminal, vá para a raiz do projeto (pasta `memorarq`).
2. Rode o comando:
   ```bash
   python run.py
   ```
3. Você verá os logs de inicialização. Acesse o sistema pelo seu navegador no endereço:
   👉 **http://localhost:3000**

Para encerrar os servidores com segurança, pressione `Ctrl + C` no terminal onde o script está rodando.

---

## 📂 Estrutura do Projeto

```text
memorarq/
│
├── backend/                   # API em Python (FastAPI)
│   ├── app.py                 # Rotas da API e lógica de download/salvamento
│   ├── storage/uploads/       # (Gerado automaticamente) Onde os arquivos ficam salvos
│   ├── services/
│   │   ├── bert_correction.py # Serviço da IA (HuggingFace Transformers)
│   │   ├── ocr_service.py     # Lógica de extração de texto (Tesseract + Pdfplumber)
│   │   └── preprocessing.py   # Filtros de imagem via OpenCV
│   └── venv/                  # Ambiente virtual do Python
│
├── frontend/                  # Interface Web (Express)
│   ├── server.js              # Servidor Node simples
│   ├── package.json           # Dependências de Node
│   └── public/
│       ├── index.html         # Estrutura visual
│       ├── style.css          # Estilização (Tema VSCode)
│       └── script.js          # Lógica de interface
│
├── .gitignore                 # Filtros do git
└── run.py                     # Script orquestrador de execução
```
