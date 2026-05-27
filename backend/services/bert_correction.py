import torch
from transformers import BertTokenizer, BertForMaskedLM
from spellchecker import SpellChecker
from Levenshtein import distance as levenshtein_distance
import re

class BertCorrector:
    def __init__(self):
        print("--- INICIALIZANDO IA (BERT) ---")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Dispositivo de Inferência: {self.device.upper()}")
        
        # Carrega o modelo e o tokenizador
        self.tokenizer = BertTokenizer.from_pretrained('neuralmind/bert-large-portuguese-cased')
        self.model = BertForMaskedLM.from_pretrained('neuralmind/bert-large-portuguese-cased')
        self.model.to(self.device)
        self.model.eval()
        
        # Carrega dicionário
        self.spell = SpellChecker(language='pt')

    def correct_text(self, text: str) -> str:
        if not text: return ""
        print(f"\n--- INICIANDO CORREÇÃO DE TEXTO ({len(text)} caracteres) ---")

        paragraphs = text.split('\n')
        corrected_paragraphs = []
        
        total_corrections = 0

        for p in paragraphs:
            if not p.strip():
                corrected_paragraphs.append(p)
                continue
            
            corrected_p, count = self._correct_sentence(p)
            corrected_paragraphs.append(corrected_p)
            total_corrections += count

        print(f"--- FIM DA CORREÇÃO: {total_corrections} alterações realizadas ---\n")
        return "\n".join(corrected_paragraphs)

    def _correct_sentence(self, sentence: str):
        # Tokeniza mantendo pontuação para reconstrução
        # Regex captura palavras ou pontuação
        tokens = re.findall(r"[\w']+|[.,!?; ]", sentence)
        
        corrected_tokens = []
        corrections_count = 0
        
        # Identifica palavras desconhecidas (candidatas a erro)
        # Agora aceitamos palavras maiores que 2 letras (antes era 3)
        unknown_indices = []
        for i, token in enumerate(tokens):
            clean_word = token.strip()
            # Checa se é palavra, tamanho > 2 e não está no dicionário
            if clean_word.isalpha() and len(clean_word) > 2:
                if clean_word.lower() not in self.spell:
                    unknown_indices.append(i)
        
        if not unknown_indices:
            return sentence, 0

        # Processa as correções
        # Reconstruímos a frase token a token
        final_sentence = sentence
        
        for idx in unknown_indices:
            bad_word = tokens[idx]
            
            # Prepara máscara: "O c0mputador quebrou" -> "O [MASK] quebrou"
            # Substituimos apenas a ocorrência exata naquele contexto
            temp_sentence = "".join(tokens[:idx] + [self.tokenizer.mask_token] + tokens[idx+1:])
            
            prediction = self._predict_mask(temp_sentence)
            
            if prediction:
                # Regra de Aceite:
                # 1. Distância de edição <= 3 (Aumentei a tolerância)
                # 2. OU se a palavra prevista for muito comum e pequena (ex: 'de', 'da')
                dist = levenshtein_distance(bad_word.lower(), prediction.lower())
                
                # Debug no Terminal
                print(f"[ANÁLISE] Erro: '{bad_word}' | Sugestão: '{prediction}' (Dist: {dist})", end="")

                if dist <= 3: 
                    # Preserva Capitalização (Maiúscula/Minúscula)
                    if bad_word[0].isupper():
                        prediction = prediction.capitalize()
                    
                    tokens[idx] = prediction # Atualiza o token na lista
                    corrections_count += 1
                    print(" -> ACEITO ✅")
                else:
                    print(" -> RECUSADO ❌ (Muito diferente)")
            
        return "".join(tokens), corrections_count

    def _predict_mask(self, masked_sentence):
        try:
            inputs = self.tokenizer(masked_sentence, return_tensors="pt").to(self.device)
            mask_token_index = (inputs.input_ids == self.tokenizer.mask_token_id)[0].nonzero(as_tuple=True)[0]
            
            if len(mask_token_index) == 0: return None

            with torch.no_grad():
                outputs = self.model(**inputs)
            
            mask_token_logits = outputs.logits[0, mask_token_index, :]
            top_token = torch.topk(mask_token_logits, 1, dim=1).indices[0].item()
            return self.tokenizer.decode([top_token]).strip()
        except Exception as e:
            print(f"Erro na predição: {e}")
            return None

bert_corrector = BertCorrector()