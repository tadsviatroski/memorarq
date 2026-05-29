# Memorarq

Sistema automatizado para extração de texto de documentos (OCR) focado em acervos e arquivos. O projeto integra pipelines de visão computacional para pré-processamento de imagens e modelos de linguagem (BERT) para correção contextual pós-OCR.

## Pré-requisitos

- **Sistema Operacional:** Windows (devido à automação de binários via script `.bat`).
- **Python:** Versão 3.8 ou superior (necessário estar no `PATH` do sistema).

## Instalação e Execução

O processo de setup da infraestrutura é integralmente automatizado pelo script de inicialização. Na raiz do projeto, execute:

> `start.bat`

### Etapas executadas pelo script na primeira inicialização:
1. Criação de um ambiente virtual isolado (`venv`).
2. Instalação das dependências do backend listadas em `requirements.txt`.
3. Download e extração automatizada dos binários do **Tesseract-OCR** e **Poppler** (alocados na pasta local `bin/`).
4. Download dos pacotes de modelo de linguagem do Tesseract (`por.traineddata`).
5. Inicialização do servidor ASGI (Uvicorn) expondo a API na porta `8000`.

A interface do cliente (frontend) será instanciada no navegador padrão no endereço `http://127.0.0.1:8000`.

## Arquitetura e Funcionalidades

- **Pré-processamento de Imagem:** Aplicação de filtros com OpenCV (Denoising via método `fastNlMeansDenoising`, e Binarização utilizando o limiar de Otsu) para otimizar a estrutura da imagem para o Tesseract.
- **Processamento Híbrido de Documentos:** Suporte nativo à leitura text-layer de PDFs via `pdfplumber` e renderização via `pdf2image`/Poppler com OCR fallback para documentos escaneados.
- **Correção Contextual (NLP):** Integração com modelo BERT (HuggingFace) auxiliado por análise de distância de Levenshtein (PySpellChecker) para inferência estrutural de erros do OCR em português.
- **Interface de Usuário:** Editor em modelo *split-view* desenvolvido em HTML5, CSS3 e Vanilla JS.
- **Gerenciamento e Exportação:** Manipulação de documentos armazenados, com capacidade de download de artefatos processados em `.txt` ou `.pdf` gerados nativamente pelo ReportLab.

## Stack Tecnológica

- **Backend Framework:** Python, FastAPI, Uvicorn.
- **Visão Computacional e OCR:** OpenCV, NumPy, Pillow, PyTesseract, Poppler.
- **NLP e Machine Learning:** PyTorch, HuggingFace Transformers, PySpellChecker.
- **Frontend:** HTML, CSS, JavaScript (sem frameworks externos).
