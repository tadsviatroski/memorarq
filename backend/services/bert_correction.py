import torch
from transformers import BertTokenizer, BertForMaskedLM
from spellchecker import SpellChecker
from Levenshtein import distance as levenshtein_distance
import re
import os

class BertCorrector:
    def __init__(self):
        print("--- INICIALIZANDO IA (BERT CUSTOMIZADO) ---")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Dispositivo de Inferência: {self.device.upper()}")
        
        # 1. CAMINHO PARA O SEU MODELO COM FINE-TUNING
        # Quando concluir o treino, basta salvar os arquivos na pasta bin/meu_bert_finetuned
        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        local_model_path = os.path.join(BASE_DIR, 'bin', 'meu_bert_finetuned')
        
        # Fallback: Se o modelo local ainda não existir, usa o base para você continuar testando
        if os.path.exists(local_model_path):
            print("Carregando modelo local com Fine-Tuning...")
            model_name = local_model_path
        else:
            print("Modelo local não encontrado. Usando BERTimbau Large padrão...")
            model_name = 'neuralmind/bert-large-portuguese-cased'
        
        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.model = BertForMaskedLM.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()
        
        # 2. CARREGAMENTO DO SPELLCHECKER
        self.spell = SpellChecker(language='pt')
        self._load_dynamic_vocabulary(BASE_DIR)

    def _load_dynamic_vocabulary(self, base_dir):
        """
        Carrega um arquivo .txt com o vocabulário extraído do seu dataset de fine-tuning.
        Isso impede que o corretor gaste processamento mascarando siglas válidas.
        """
        vocab_path = os.path.join(base_dir, 'bin', 'vocab_acervo.txt')
        if os.path.exists(vocab_path):
            with open(vocab_path, 'r', encoding='utf-8') as f:
                custom_words = [line.strip().lower() for line in f if line.strip()]
            self.spell.word_frequency.load_words(custom_words)
            print(f"Vocabulário do Acervo carregado: {len(custom_words)} termos adicionados.")

    def correct_text(self, text: str) -> tuple[str, list]:
        if not text: return "", []
        print(f"\n--- INICIANDO CORREÇÃO DE TEXTO ({len(text)} caracteres) ---")

        paragraphs = text.split('\n')
        corrected_paragraphs = []
        correction_logs = [] # <-- NOVA LISTA DE LOGS

        for p in paragraphs:
            if not p.strip():
                corrected_paragraphs.append(p)
                continue
            
            # Agora recebe os logs da frase também
            corrected_p, count, logs = self._correct_sentence(p)
            corrected_paragraphs.append(corrected_p)
            correction_logs.extend(logs) # Junta todos os logs

        print(f"--- FIM DA CORREÇÃO: {len(correction_logs)} alterações identificadas ---\n")
        return "\n".join(corrected_paragraphs), correction_logs

    def _correct_sentence(self, sentence: str):
        tokens = re.findall(r"[\w']+|[.,!?; ]", sentence)
        corrections_count = 0
        unknown_indices = []
        sentence_logs = [] # <-- LOGS DESTA FRASE
        
        for i, token in enumerate(tokens):
            clean_word = token.strip()
            if clean_word.isalpha() and len(clean_word) > 2:
                if clean_word.lower() not in self.spell:
                    unknown_indices.append(i)
        
        if not unknown_indices:
            return sentence, 0, []

        for idx in unknown_indices:
            bad_word = tokens[idx]
            temp_sentence = "".join(tokens[:idx] + [self.tokenizer.mask_token] + tokens[idx+1:])
            prediction = self._predict_mask(temp_sentence)
            
            if prediction:
                if prediction.startswith('##') or (len(prediction) <= 2 and len(bad_word) > 4):
                    # Registra a recusa (opcional para debug, ou pode omitir)
                    sentence_logs.append({"original": bad_word, "sugestao": prediction, "status": "RECUSADO", "motivo": "Sub-token"})
                    continue

                dist = levenshtein_distance(bad_word.lower(), prediction.lower())
                
                if dist <= 3: 
                    if bad_word.isupper(): prediction = prediction.upper()
                    elif bad_word[0].isupper(): prediction = prediction.capitalize()
                    
                    tokens[idx] = prediction
                    corrections_count += 1
                    
                    # Registra a correção feita com sucesso
                    sentence_logs.append({
                        "original": bad_word, 
                        "sugestao": prediction, 
                        "status": "ACEITO"
                    })
                else:
                    sentence_logs.append({
                        "original": bad_word, 
                        "sugestao": prediction, 
                        "status": "RECUSADO",
                        "motivo": "Baixa similaridade"
                    })
            
        return "".join(tokens), corrections_count, sentence_logs

    def _predict_mask(self, masked_sentence):
        try:
            # 4. PREVENÇÃO DE CRASH DE MEMÓRIA (Limite de 512 tokens do BERT)
            inputs = self.tokenizer(
                masked_sentence, 
                return_tensors="pt", 
                truncation=True, 
                max_length=512
            ).to(self.device)
            
            mask_positions = (inputs.input_ids == self.tokenizer.mask_token_id)[0].nonzero(as_tuple=True)[0]
            
            if len(mask_positions) == 0: 
                return None

            mask_token_index = mask_positions[0]

            with torch.no_grad():
                outputs = self.model(**inputs)
            
            mask_token_logits = outputs.logits[0, mask_token_index, :]
            top_token = torch.topk(mask_token_logits, 1, dim=0).indices.item()
            
            return self.tokenizer.decode([top_token]).strip()
            
        except Exception as e:
            print(f"Erro na predição: {e}")
            return None

bert_corrector = BertCorrector()