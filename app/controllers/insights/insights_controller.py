from fastapi import FastAPI, Query, HTTPException, File, UploadFile, APIRouter
from .prompts import criar_analise_interna, criar_analise_reclamacao, criar_analise_concorrente
from app.database.connection import get_db

router = APIRouter()

async def save_db(uuid, dados, empresa, tipo_analise="interna"):
    db = get_db()
    if db is None:
        raise HTTPException(
            status_code=500, detail="A conexão com o Firestore não foi estabelecida"
        )

    try:
        analysis_document = db.collection("analises").document(uuid)
        doc = analysis_document.get()

        if not doc.exists:
            analysis_document.set({})

        analysis_data = doc.to_dict() if doc.exists else {}

        if empresa not in analysis_data:
            analysis_data[empresa] = {}

        analysis_data[empresa][tipo_analise] = dados

        analysis_document.set(analysis_data)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao salvar no Firestore: {str(e)}"
        )

@router.post("/insight/interno")
async def gerar_insight_interno(uuid: str, empresa: str):
    try:
        db = get_db()
        if db is None:
            raise HTTPException(
                status_code=500, detail="A conexão com o Firestore não foi estabelecida"
            )

        empresa = empresa.replace(" ", "-")

        scrapping_document = db.collection("dadosWebScrapping").document(uuid)
        doc = scrapping_document.get()
        if not doc.exists:
            raise HTTPException(
                status_code=404, detail=f"Documento com UUID {uuid} não encontrado."
            )

        scrapping_data = doc.to_dict()
        empresa_dados = scrapping_data.get(empresa)
        if not empresa_dados:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhuma reclamação encontrada para a empresa {empresa}.",
            )

        total_reclamacoes = empresa_dados.get("total_reclamacoes", 0)
        ramo = empresa_dados.get("setor", "")
        categorias = empresa_dados.get("categorias", [])

        if not categorias:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhum dado disponível para análise para a empresa {empresa}.",
            )

        response = criar_analise_interna(categorias, empresa, ramo)

        response_with_empresa = {
            "analises": response,
            "empresa": empresa,
            "total_reclamacoes": total_reclamacoes,
        }

        await save_db(uuid, response_with_empresa, empresa, tipo_analise="interna")

        return {"status_code": 200, "analise_interna": response_with_empresa}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insight/reclamacao")
async def gerar_insight_reclamao_unica(
    uuid: str, reclamacao: str, empresa: str, ramo: str
):
    try:
        db = get_db()
        if db is None:
            raise HTTPException(
                status_code=500, detail="A conexão com o Firestore não foi estabelecida"
            )

        response = criar_analise_reclamacao(reclamacao, empresa, ramo)

        return {"status_code": 200, "analise_reclamacao_unica": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insight/concorrente")
async def gerar_insight_concorrente(uuid: str, empresa_interna: str, empresa_externa: str):
    try:
        db = get_db()
        if db is None:
            raise HTTPException(
                status_code=500, detail="A conexão com o Firestore não foi estabelecida"
            )

        document_ref = db.collection("dadosWebScrapping").document(uuid)
        doc = document_ref.get()
        if not doc.exists:
            raise HTTPException(
                status_code=404, detail=f"Documento com UUID {uuid} não encontrado."
            )

        user_data = doc.to_dict()
        dados_empresa_interna = user_data.get(empresa_interna, None)
        dados_empresa_externa = user_data.get(empresa_externa, None)
        
        if dados_empresa_interna is None or dados_empresa_externa is None:
            raise HTTPException(
                status_code=404, detail=f"Dados não encontrados para uma ou ambas as empresas."
            )

        print("passou")
        result = criar_analise_concorrente(
            dados_empresa_interna,
            dados_empresa_externa,
            empresa_interna,
            empresa_externa,
            ramo_empresa=user_data.get("ramo", "Ramo não especificado")
        )

        return {"status_code": 200, "analise_concorrente": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
