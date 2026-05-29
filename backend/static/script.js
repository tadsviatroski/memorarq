// --- ELEMENTOS DO DOM (DECLARAÇÕES GLOBAIS) ---
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const uploadScreen = document.getElementById('upload-screen');
const editorScreen = document.getElementById('editor-screen');
const docPreview = document.getElementById('doc-preview');
const textEditor = document.getElementById('text-editor');
const btnBack = document.getElementById('btn-back');
const btnDownload = document.getElementById('btn-download'); // Referência crucial recuperada
const loadingOverlay = document.getElementById('loading-overlay');
const loadingText = document.getElementById('loading-text'); // Referência cacheada para evitar erros

// --- MODAL DE DOWNLOAD ---
const downloadModal = document.getElementById('download-modal');
const btnCloseModal = document.getElementById('btn-close-modal');
const btnDlTxt = document.getElementById('btn-dl-txt');
const btnDlPdf = document.getElementById('btn-dl-pdf');

// --- FERRAMENTAS DO EDITOR ---
const btnZoomIn = document.getElementById('btn-zoom-in');
const btnZoomOut = document.getElementById('btn-zoom-out');
const btnCopy = document.getElementById('btn-copy');
const btnClear = document.getElementById('btn-clear');
const btnUpper = document.getElementById('btn-uppercase');
const btnLower = document.getElementById('btn-lowercase');
const charCount = document.getElementById('char-count');
const cursorPos = document.getElementById('cursor-pos');
const btnSaveText = document.getElementById('btn-save-text');
const btnReOcr = document.getElementById('btn-re-ocr');
const btnAiFix = document.getElementById('btn-ai-fix');
const btnViewLogs = document.getElementById('btn-view-logs');

// --- SIDEBAR ---
const sidebar = document.getElementById('sidebar');
const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
const btnOpenSidebar = document.getElementById('btn-open-sidebar');

const managerScreen = document.getElementById('manager-screen');
const navUpload = document.getElementById('nav-upload');
const navManager = document.getElementById('nav-manager');
const managerFileList = document.getElementById('manager-file-list');

// --- VARIÁVEIS DE ESTADO ---
const API_URL = window.location.origin;
let currentOpenFilename = null;

// --- INICIALIZAÇÃO ---
window.addEventListener('DOMContentLoaded', () => {
});

// --- EVENTOS DE UPLOAD ---
if (fileInput) {
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) uploadFile(fileInput.files[0]);
    });
}

if (dropZone) {
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--accent-color)';
    });
    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = 'var(--border-color)';
    });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--border-color)';
        if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
    });
}

// Botão Voltar / Novo Documento
if (btnBack) {
    btnBack.addEventListener('click', () => {
        editorScreen.classList.add('hidden');
        uploadScreen.classList.remove('hidden');
        fileInput.value = ''; 
        docPreview.innerHTML = '';
        textEditor.value = '';
        currentOpenFilename = null;
    });
}

// --- LÓGICA DE UPLOAD ---
async function uploadFile(file) {
    setLoading(true, "Enviando arquivo...");
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_URL}/upload`, { method: 'POST', body: formData });
        if (!response.ok) throw new Error(`Erro: ${response.statusText}`);

        const data = await response.json();
        currentOpenFilename = data.filename;
        
        // Arquivo novo não tem log, garante que o botão inicie desativado
        if (btnViewLogs) btnViewLogs.disabled = true; 
        
        showEditorScreen(data);
    } catch (error) {
        console.error("ERRO:", error);
        alert("Erro ao processar o arquivo.");
    } finally {
        setLoading(false);
    }
}

function showEditorScreen(data) {
    uploadScreen.classList.add('hidden');
    editorScreen.classList.remove('hidden');

    const fileUrl = data.url;
    const type = data.content_type;
    
    textEditor.value = data.text || ""; 
    updateStats();

    if (type.startsWith('image/')) {
        docPreview.innerHTML = `<img src="${fileUrl}" alt="Original">`;
    } else if (type === 'application/pdf') {
        docPreview.innerHTML = `<embed src="${fileUrl}" type="application/pdf" width="100%" height="100%">`;
    } else {
        docPreview.innerHTML = `<p>Arquivo: ${data.filename}</p>`;
    }
}

// --- CONTROLE DE LOADING SEGURO ---
function setLoading(active, text = "Processando...") {
    if (!loadingOverlay) return;
    
    if (active) {
        if (loadingText) loadingText.innerText = text;
        loadingOverlay.classList.remove('hidden');
    } else {
        loadingOverlay.classList.add('hidden');
        if (loadingText) loadingText.innerText = "Processando...";
    }
}




// --- GERENCIADOR DE SISTEMA E VALIDAÇÃO ---
async function loadManagerDocuments() {
    try {
        const response = await fetch(`${API_URL}/documents`);
        const files = await response.json();
        renderManagerTable(files);
    } catch (error) { console.error("Erro ao listar:", error); }
}

function renderManagerTable(files) {
    managerFileList.innerHTML = '';
    if (files.length === 0) {
        managerFileList.innerHTML = '<tr><td colspan="2" style="text-align: center; color: #666;">Nenhum documento processado ainda.</td></tr>';
        return;
    }

    files.forEach(file => {
        const tr = document.createElement('tr');
        
        // Coluna 1: Nome
        const tdName = document.createElement('td');
        tdName.innerText = file.name;
            
        // Coluna 2: Ações Enxutas
        const tdActions = document.createElement('td');
        tdActions.className = 'action-btns';
        
        const btnOpen = document.createElement('button');
        btnOpen.className = 'btn-secondary';
        btnOpen.innerHTML = '<span class="material-symbols-outlined" style="font-size: 16px;">edit_document</span>';
        btnOpen.title = "Abrir no Editor";
        btnOpen.onclick = () => {
            openDocument(file.name);
            managerScreen.classList.add('hidden'); 
            navManager.classList.remove('active');
        };

        const btnDel = document.createElement('button');
        btnDel.className = 'btn-secondary';
        btnDel.style.color = '#d84545';
        btnDel.innerHTML = '<span class="material-symbols-outlined" style="font-size: 16px;">delete</span>';
        btnDel.title = "Excluir Original e Extrações";
        btnDel.onclick = async () => {
            await deleteDocument(file.name);
            loadManagerDocuments();
        };

        tdActions.appendChild(btnOpen);
        tdActions.appendChild(btnDel);

        tr.appendChild(tdName);
        tr.appendChild(tdActions);
        managerFileList.appendChild(tr);
    });
}

// --- VALIDAÇÃO: BUSCA LOGS SALVOS ---
async function loadAiLogsForValidation(filename) {
    setLoading(true, "Buscando histórico de correção...");
    try {
        const response = await fetch(`${API_URL}/documents/${filename}/logs`);
        if (response.ok) {
            const logs = await response.json();
            renderAiLogsModal(logs); // Reutiliza a função de desenhar os logs
        }
    } catch (e) {
        alert("Erro ao buscar logs da IA.");
    } finally {
        setLoading(false);
    }
}

// Transformei o desenho do modal em uma função separada para poder usar no Botão do Editor e no Gerenciador
function renderAiLogsModal(logsArray) {
    const aceitos = logsArray.filter(log => log.status === "ACEITO");
    aiLogContent.innerHTML = ""; 
    
    if (aceitos.length === 0) {
        aiLogContent.innerHTML = "<div class='log-empty'>Nenhum erro ortográfico detectado pelo histórico.</div>";
    } else {
        aceitos.forEach(log => {
            const div = document.createElement('div');
            div.className = "log-item log-accepted";
            div.innerHTML = `
                <span><span class="log-original">${log.original}</span> <span class="log-arrow">➔</span> <span class="sugestao">${log.sugestao}</span></span>
                <span class="material-symbols-outlined" style="font-size: 16px; color: #4ec9b0;">check_circle</span>
            `;
            aiLogContent.appendChild(div);
        });
    }
    aiLogModal.classList.remove('hidden');
}

// --- FUNÇÃO DE ABRIR DOCUMENTO ---
async function openDocument(filename) {
    setLoading(true, "Abrindo documento...");

    try {
        const response = await fetch(`${API_URL}/documents/${filename}/details`);
        if (!response.ok) throw new Error("Erro ao abrir");
        
        const data = await response.json();
        currentOpenFilename = filename; 
        showEditorScreen(data);

        // VERIFICA SE EXISTEM LOGS PARA ATIVAR O BOTÃO DA IA
        const logsResponse = await fetch(`${API_URL}/documents/${filename}/logs`);
        if (logsResponse.ok) {
            const logs = await logsResponse.json();
            if (btnViewLogs) btnViewLogs.disabled = (logs.length === 0);
        }

    } catch (error) {
        console.error(error);
        alert("Não foi possível abrir o documento.");
    } finally {
        setLoading(false);
    }
}

async function deleteDocument(filename) {
    if (!confirm(`Excluir "${filename}" permanentemente?`)) return;

    try {
        await fetch(`${API_URL}/documents/${filename}`, { method: 'DELETE' });
        loadManagerDocuments();
    } catch (error) {
        alert("Erro ao excluir.");
    }
}

// --- DOWNLOAD E MODAL ---
if (btnDownload) {
    btnDownload.addEventListener('click', () => {
        if (!textEditor.value.trim()) {
            alert("Não há texto para baixar.");
            return;
        }
        downloadModal.classList.remove('hidden');
    });
}

if (btnCloseModal) {
    btnCloseModal.addEventListener('click', () => {
        downloadModal.classList.add('hidden');
    });
}

if (downloadModal) {
    downloadModal.addEventListener('click', (e) => {
        if (e.target === downloadModal) downloadModal.classList.add('hidden');
    });
}

// Baixar TXT
if (btnDlTxt) {
    btnDlTxt.addEventListener('click', () => {
        const text = textEditor.value;
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        const safeName = currentOpenFilename ? currentOpenFilename + ".txt" : "documento.txt";
        a.download = safeName;
        a.click();
        URL.revokeObjectURL(url);
        
        downloadModal.classList.add('hidden');
    });
}

// Baixar PDF
if (btnDlPdf) {
    btnDlPdf.addEventListener('click', async () => {
        const text = textEditor.value;
        const originalBtnText = btnDlPdf.innerHTML;
        
        btnDlPdf.innerHTML = "Gerando...";
        btnDlPdf.disabled = true;

        try {
            const response = await fetch(`${API_URL}/download/pdf`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });

            if (!response.ok) throw new Error("Erro ao gerar PDF");

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            const safeName = currentOpenFilename ? currentOpenFilename + ".pdf" : "documento.pdf";
            a.download = safeName;
            a.click();
            window.URL.revokeObjectURL(url);

            downloadModal.classList.add('hidden');
        } catch (error) {
            console.error(error);
            alert("Erro ao gerar PDF.");
        } finally {
            btnDlPdf.innerHTML = originalBtnText;
            btnDlPdf.disabled = false;
        }
    });
}

// --- SIDEBAR TOGGLE ---
btnToggleSidebar.addEventListener('click', toggleSidebar);
btnOpenSidebar.addEventListener('click', toggleSidebar);

function toggleSidebar() {
    sidebar.classList.toggle('closed');
    if (sidebar.classList.contains('closed')) {
        btnOpenSidebar.classList.remove('hidden');
    } else {
        btnOpenSidebar.classList.add('hidden');
    }
}


// --- SISTEMA DE NAVEGAÇÃO DO MENU ---
navUpload.addEventListener('click', () => {
    navUpload.classList.add('active');
    navManager.classList.remove('active');
    editorScreen.classList.add('hidden');
    managerScreen.classList.add('hidden');
    uploadScreen.classList.remove('hidden');
    if(window.innerWidth < 768) toggleSidebar(); // Fecha no celular
});

navManager.addEventListener('click', () => {
    navManager.classList.add('active');
    navUpload.classList.remove('active');
    uploadScreen.classList.add('hidden');
    editorScreen.classList.add('hidden');
    managerScreen.classList.remove('hidden');
    loadManagerDocuments(); // Atualiza a tabela
    if(window.innerWidth < 768) toggleSidebar(); 
});

btnBack.addEventListener('click', () => navUpload.click()); // O botão Voltar agora chama a navegação

// --- FERRAMENTAS DO EDITOR (ZOOM, SAVE, OCR) ---
// Zoom
let currentFontSize = 14;
btnZoomIn.addEventListener('click', () => {
    if (currentFontSize < 30) { currentFontSize += 2; textEditor.style.fontSize = `${currentFontSize}px`; }
});
btnZoomOut.addEventListener('click', () => {
    if (currentFontSize > 10) { currentFontSize -= 2; textEditor.style.fontSize = `${currentFontSize}px`; }
});

// Copiar/Limpar
btnCopy.addEventListener('click', () => {
    textEditor.select();
    navigator.clipboard.writeText(textEditor.value).then(() => alert("Copiado!")).catch(console.error);
});
btnClear.addEventListener('click', () => {
    if (confirm("Apagar tudo?")) { textEditor.value = ""; updateStats(); }
});

// Transformação
function transformText(type) {
    const start = textEditor.selectionStart;
    const end = textEditor.selectionEnd;
    const text = textEditor.value;
    if (start === end) {
        textEditor.value = type === 'upper' ? text.toUpperCase() : text.toLowerCase();
    } else {
        const sel = text.substring(start, end);
        const trans = type === 'upper' ? sel.toUpperCase() : sel.toLowerCase();
        textEditor.value = text.substring(0, start) + trans + text.substring(end);
        textEditor.setSelectionRange(start, end);
    }
}
btnUpper.addEventListener('click', () => transformText('upper'));
btnLower.addEventListener('click', () => transformText('lower'));

// Stats
function updateStats() {
    const text = textEditor.value;
    charCount.innerText = `${text.length} caracteres`;
    const lines = text.substr(0, textEditor.selectionEnd).split('\n');
    cursorPos.innerText = `Ln ${lines.length}, Col ${lines[lines.length - 1].length + 1}`;
}
textEditor.addEventListener('input', updateStats);
textEditor.addEventListener('keyup', updateStats);
textEditor.addEventListener('click', updateStats);

// Salvar e Re-OCR
btnSaveText.addEventListener('click', async () => {
    if (!currentOpenFilename) return;
    btnSaveText.innerHTML = '<span class="material-symbols-outlined spin">sync</span>';
    try {
        await fetch(`${API_URL}/documents/${currentOpenFilename}/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: textEditor.value })
        });
        const footer = document.querySelector('.editor-footer');
        const orig = footer.style.backgroundColor;
        footer.style.backgroundColor = '#4ec9b0';
        setTimeout(() => footer.style.backgroundColor = orig, 500);
    } catch(e) { alert("Erro ao salvar."); }
    finally { btnSaveText.innerHTML = '<span class="material-symbols-outlined" style="color: #4ec9b0;">save</span>'; }
});

btnReOcr.addEventListener('click', async () => {
    if (!currentOpenFilename || !confirm("Refazer OCR apagará edições. Continuar?")) return;
    setLoading(true, "Re-extraindo...");
    try {
        const r = await fetch(`${API_URL}/documents/${currentOpenFilename}/ocr`, { method: 'POST' });
        if(r.ok) {
            const d = await r.json();
            textEditor.value = d.text;
            updateStats();
        }
    } catch(e) { alert("Erro OCR."); }
    finally { setLoading(false); }
});

// Atalho Ctrl+S
document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (!editorScreen.classList.contains('hidden')) btnSaveText.click();
    }
});

// --- ELEMENTOS DO MODAL DE LOG ---
const aiLogModal = document.getElementById('ai-log-modal');
const aiLogContent = document.getElementById('ai-log-content');
const btnCloseAiLog = document.getElementById('btn-close-ai-log');

if (btnCloseAiLog) {
    btnCloseAiLog.addEventListener('click', () => aiLogModal.classList.add('hidden'));
}

// --- Correção BERTimbau (Refatorada) ---
if (btnAiFix) {
    btnAiFix.addEventListener('click', async () => {
        if (!currentOpenFilename) return;

        if (!confirm("A IA tentará corrigir erros ortográficos baseada no contexto. Isso alterará o texto atual. Continuar?")) return;

        setLoading(true, "A IA está lendo e corrigindo...");

        try {
            const response = await fetch(`${API_URL}/documents/${currentOpenFilename}/ai-fix`, {
                method: 'POST'
            });

            if (response.ok) {
                const data = await response.json();
                
                // 1. Atualiza o texto no editor
                textEditor.value = data.text;
                updateStats();

                if (btnViewLogs) btnViewLogs.disabled = false;
                
                // 2. Monta e exibe o modal chamando a função centralizada
                renderAiLogsModal(data.logs);

            } else {
                alert("Erro ao processar com IA.");
            }
        } catch (error) {
            console.error(error);
            alert("Erro de conexão com a IA.");
        } finally {
            setLoading(false);
        }
    });
}

// --- ABRIR HISTÓRICO DE CORREÇÕES (NOVO BOTÃO) ---
if (btnViewLogs) {
    btnViewLogs.addEventListener('click', () => {
        if (currentOpenFilename && !btnViewLogs.disabled) {
            loadAiLogsForValidation(currentOpenFilename);
        }
    });
}