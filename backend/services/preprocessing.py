import cv2
import numpy as np
from PIL import Image

def preprocess_image(pil_image):
    """
    Pipeline de limpeza de imagem para maximizar acurácia do Tesseract.
    Converte PIL Image -> OpenCV -> Filtros -> PIL Image.
    """
    # 1. Converter PIL para formato OpenCV (Array Numpy)
    open_cv_image = np.array(pil_image) 
    
    # Se a imagem tiver cor (RGB), converte para BGR (padrão OpenCV)
    if len(open_cv_image.shape) == 3:
        open_cv_image = open_cv_image[:, :, ::-1].copy()

    # 2. Escala de Cinza (Remove informação de cor que atrapalha o OCR)
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)

    # 3. Remoção de Ruído (Denoising)
    # Remove "sujeira" digital ou manchas de scan
    no_noise = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

    # 4. Binarização (Thresholding) - O PASSO MAIS IMPORTANTE
    # Transforma tudo que não é texto em branco absoluto e o texto em preto absoluto.
    # Usamos o método de Otsu, que calcula o limiar ideal automaticamente.
    _, binary = cv2.threshold(no_noise, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 5. Dilatação (Opcional, mas útil para fontes muito finas)
    # Engrossa levemente as letras para o Tesseract pegar melhor
    # kernel = np.ones((1, 1), np.uint8)
    # binary = cv2.dilate(binary, kernel, iterations=1)

    # 6. Converter de volta para PIL para o Tesseract usar
    return Image.fromarray(binary)