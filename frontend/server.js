const express = require('express');
const path = require('path');
const app = express();
const PORT = 3000;

// Serve os arquivos estáticos da pasta 'public'
app.use(express.static(path.join(__dirname, 'public')));

// Rota principal
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
    console.log(`\n--- MEMORARQ FRONTEND ---`);
    console.log(`Servidor rodando em: http://localhost:${PORT}`);
    console.log(`Para parar, pressione Ctrl + C\n`);
});