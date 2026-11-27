import os
import json
import cv2
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("A variável de ambiente GEMINI_API_KEY não está configurada.")
    return genai.Client(api_key=api_key)

SYSTEM_PROMPT_TEXTO = """
Você é um especialista brasileiro em checagem de fatos (fact-checking), análise do discurso político-religioso e desinformação nas eleições presidenciais do Brasil de 2022.
Sua missão é analisar artigos, notícias ou mensagens encaminhadas voltadas ao público religioso e retornar um parecer respeitoso, educativo, imparcial e tecnicamente rigoroso.

Avalie especificamente:
1. Veracidade factual (confrontando com checagens do TSE, agências de fact-checking e fatos históricos de 2022).
2. Táticas de manipulação voltadas ao público religioso:
   - Pânico moral (ex.: boatos falsos de fechamento de igrejas, proibição de cultos/Bíblias ou perseguição religiosa iminente).
   - Descontextualização teológica ou bíblica (uso de versículos fora de contexto para validar candidatos).
   - Falsas profecias ou falas fabricadas atribuídas a pastores, padres ou líderes religiosos.
   - Montagens ou distorções de falas de candidatos sobre fé, família e valores.

Retorne EXCLUSIVAMENTE um JSON válido com a seguinte estrutura:
{
  "veredito": "VERDADEIRO" | "FALSO" | "ENGANOSO / FORA DE CONTEXTO" | "SEM COMPROVAÇÃO",
  "nivel_risco": 0,
  "resumo_executivo": "Explicação clara, respeitosa e direta em português.",
  "taticas_detectadas": ["lista de táticas identificadas ou 'Nenhuma tática de manipulação detectada'"],
  "contexto_eleicoes_2022": "Explicação histórica/factual sobre o tema no contexto das eleições de 2022 no Brasil.",
  "dica_educativa": "Orientação prática para o leitor verificar conteúdos semelhantes antes de compartilhar."
}
"""

SYSTEM_PROMPT_VIDEO = """
Você é um perito forense digital especializado na detecção de vídeos gerados por Inteligência Artificial (deepfakes, Sora, Runway, HeyGen, Veo, lip-sync sintético) e manipulações visuais em conteúdos políticos e religiosos no Brasil.

Analise os quadros extraídos deste vídeo observando:
1. Inconsistências anatômicas (mãos, dedos, dentes, orelhas, piscar de olhos antinatural).
2. Artefatos de borda ao redor do rosto, cabelo, microfones ou púlpitos.
3. Texturas de pele excessivamente lisas ("efeito plástico") ou iluminação incoerente com o ambiente.
4. Textos, legendas ou símbolos distorcidos ao fundo (faixas de igreja, Bíblias, bandeiras do Brasil).
5. Sinais de clonagem de voz/lip-sync ou descontextualização de vídeos antigos.

Retorne EXCLUSIVAMENTE um JSON válido com a seguinte estrutura:
{
  "classificacao": "PROVÁVEL VÍDEO GERADO POR IA" | "SINAIS DE MANIPULAÇÃO / EDIÇÃO" | "APARENTEMENTE AUTÊNTICO",
  "probabilidade_ia": 0,
  "resumo_forense": "Explicação clara e acessível sobre o que foi observado nos quadros.",
  "indicadores_visuais": ["lista de sinais técnicos observados nos quadros"],
  "alerta_contextual": "Observação sobre como vídeos sintéticos ou descontextualizados costumam ser usados para enganar o público religioso.",
  "recomendacao": "Como o usuário pode confirmar a origem original do vídeo."
}
"""


def analisar_artigo_texto(conteudo: str, url: str = "") -> dict:
    client = get_client()
    prompt_usuario = "Analise o seguinte conteúdo:\n\n"
    if url:
        prompt_usuario += f"URL informada: {url}\n\n"
    prompt_usuario += f"Texto/Artigo:\n{conteudo}"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_usuario,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT_TEXTO,
            tools=[{"google_search": {}}],
            temperature=0.2,
        ),
    )

    texto_limpo = response.text.strip()
    if texto_limpo.startswith("```json"):
        texto_limpo = texto_limpo[7:-3].strip()
    elif texto_limpo.startswith("```"):
        texto_limpo = texto_limpo[3:-3].strip()

    return json.loads(texto_limpo)


def extrair_quadros_video(caminho_video: str, max_quadros: int = 6) -> list[bytes]:
    captura = cv2.VideoCapture(caminho_video)
    total_quadros = int(captura.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_quadros <= 0:
        captura.release()
        raise ValueError("Não foi possível ler os quadros do vídeo enviado.")

    intervalo = max(1, total_quadros // max_quadros)
    quadros_bytes = []

    for i in range(max_quadros):
        posicao = i * intervalo
        if posicao >= total_quadros:
            break
        captura.set(cv2.CAP_PROP_POS_FRAMES, posicao)
        sucesso, frame = captura.read()
        if sucesso:
            altura, largura = frame.shape[:2]
            if largura > 1024:
                nova_altura = int(altura * (1024 / largura))
                frame = cv2.resize(frame, (1024, nova_altura))
            ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            if ok:
                quadros_bytes.append(buffer.tobytes())

    captura.release()
    return quadros_bytes


def analisar_video_ia(caminho_video: str, contexto_usuario: str = "") -> dict:
    client = get_client()
    quadros = extrair_quadros_video(caminho_video, max_quadros=6)

    partes = [
        f"Analise estes {len(quadros)} quadros extraídos sequencialmente de um vídeo enviado para verificação de geração por IA/deepfake."
    ]
    if contexto_usuario:
        partes.append(f"Contexto informado pelo usuário sobre onde recebeu o vídeo: {contexto_usuario}")

    for q_bytes in quadros:
        partes.append(types.Part.from_bytes(data=q_bytes, mime_type="image/jpeg"))

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=partes,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT_VIDEO,
            temperature=0.2,
        ),
    )

    texto_limpo = response.text.strip()
    if texto_limpo.startswith("```json"):
        texto_limpo = texto_limpo[7:-3].strip()
    elif texto_limpo.startswith("```"):
        texto_limpo = texto_limpo[3:-3].strip()

    return json.loads(texto_limpo)
