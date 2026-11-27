import os
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from analyzer import analisar_artigo_texto, analisar_video_ia

app = FastAPI(title="A Verdade Fortalece a Sua Fé")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TextoRequest(BaseModel):
    texto: str
    url: str = ""


@app.get("/api/status")
def status():
    return {"status": "online", "plataforma": "A Verdade Fortalece a Sua Fé"}


@app.post("/api/analisar-texto")
def endpoint_analisar_texto(dados: TextoRequest):
    if not dados.texto.strip() and not dados.url.strip():
        raise HTTPException(status_code=400, detail="Envie um texto ou link para verificação.")
    try:
        resultado = analisar_artigo_texto(dados.texto, dados.url)
        return {"sucesso": True, "dados": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar texto: {str(e)}")


@app.post("/api/analisar-video")
async def endpoint_analisar_video(
    video: UploadFile = File(...),
    contexto: str = Form("")
):
    if not video.content_type or not video.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Envie um arquivo de vídeo válido (MP4, MOV, WEBM).")

    sufixo = os.path.splitext(video.filename or ".mp4")[1] or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=sufixo) as tmp:
        conteudo = await video.read()
        if len(conteudo) > 25 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="O vídeo excede o limite de 25 MB do servidor gratuito.")
        tmp.write(conteudo)
        caminho_temporario = tmp.name

    try:
        resultado = analisar_video_ia(caminho_temporario, contexto)
        return {"sucesso": True, "dados": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao analisar vídeo: {str(e)}")
    finally:
        if os.path.exists(caminho_temporario):
            os.remove(caminho_temporario)


app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def ler_pagina_inicial():
    return FileResponse("frontend/index.html")
