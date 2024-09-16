import re
from .web_scraping import Scraping
from app.database.connection import get_db
from fastapi import FastAPI, Query, HTTPException, File, UploadFile, APIRouter

router = APIRouter()

def process_scraping_results(raw_dados, max_pages):
    ramo_empresa = raw_dados['ramo']
    total_reclamacoes = raw_dados['total_reclamacoes']
    categorias = raw_dados['dados']

    for categoria_data in categorias:
        quantidade = len(categoria_data['reclamacoes'])
        percentual = (quantidade / total_reclamacoes) * 100

        categoria_data['quantidade'] = quantidade
        categoria_data['percentual'] = round(percentual, 2)

    categorias_sorted = sorted(categorias, key=lambda x: x['quantidade'], reverse=True)

    dados = {
        "ramo": ramo_empresa,
        "total_reclamacoes": total_reclamacoes,
        "categorias": categorias_sorted,
        "max_pages": max_pages
    }

    return dados

def sanitize_firestore_field_name(name):
    return re.sub(r"[^a-zA-Z0-9]", "_", name)

async def save_db(dados, uuid, empresa, max_pages):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="A conexão com o Firestore não foi estabelecida")

    sanitized_empresa = sanitize_firestore_field_name(empresa)

    try:
        scrapping_document = db.collection("dadosWebScrapping").document(uuid)
        doc = scrapping_document.get()
        
        if doc.exists:
            scrapping_data = doc.to_dict()
            
            if sanitized_empresa in scrapping_data:
                existing_data = scrapping_data[sanitized_empresa]
                existing_max_pages = existing_data.get("max_pages", 0)
                
                if max_pages > existing_max_pages:
                    scrapping_document.update({sanitized_empresa: dados})
                    return {"status_code": 200, "mensagem": "Dados atualizados com sucesso", "dados": dados}
                else:
                    return {"status_code": 200, "mensagem": "Número de páginas não é maior que o atual. Dados não atualizados."}
            else:
                scrapping_document.update({sanitized_empresa: dados})
                return {"status_code": 200, "mensagem": "Dados coletados e salvos com sucesso", "dados": dados}
        else:
            scrapping_document.set({sanitized_empresa: dados})
            return {"status_code": 200, "mensagem": "Documento criado e dados salvos com sucesso", "dados": dados}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar no banco de dados: {str(e)}")


@router.get("/scraping/{empresa}")
async def web_scraping(uuid: str, empresa: str, apelido: str = Query(None, description="Apelido para nome da Empresa"), max_page: int = Query(None, description="Número máximo de páginas para scraping")):
    try:
        empresa = empresa.replace(' ', '-')
        scraper = Scraping(empresa, apelido, max_page)
        status, raw_dados = await scraper.iniciar()

        if status['status_code'] == 200:
            dados = process_scraping_results(raw_dados, max_page)
            return await save_db(dados, uuid, empresa, max_page)
        else:
            raise HTTPException(status_code=status['status_code'], detail=f"{status['mensagem']}")

    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao realizar web scraping: " + str(e))

# @router.get("/empresas/")
# async def consultar_empresa():
#     try:
#         dados = {doc.to_dict().get("empresa") for doc in db.collection("reclamacoes").stream()}
#         if not dados:
#             raise HTTPException(status_code=404, detail=f"Nenhuma empresa com reclamações encontrada.")
        
#         return {"status_code": 200, "Empresas": [dados] }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Erro ao buscar empresas:  {str(e)}")

@router.get("/reclamacoes/{empresa}")
async def consultar_reclamacoes(empresa: str, uuid: str):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="A conexão com o Firestore não foi estabelecida")
    empresa = empresa.replace(' ', '-')
    try:
        user_document = db.collection("dadosUsuarios").document(uuid)
        doc = user_document.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Usuário com UUID {uuid} não encontrado.")

        user_data = doc.to_dict()
        
        web_scrapping_dados = user_data.get("web_scrapping_dados", [])
        empresa_dados = next((item for item in web_scrapping_dados if empresa in item), None)
        
        if empresa_dados is None:
            raise HTTPException(status_code=404, detail=f"Nenhuma reclamação encontrada para a empresa {empresa}.")

        dados = empresa_dados.get(empresa, [])
        
        return {"status_code": 200, "dados": dados}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar dados: {str(e)}")


@router.delete("/reclamacoes/{empresa}")
async def apagar_reclamacoes_empresa(empresa: str, uuid: str):
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="A conexão com o Firestore não foi estabelecida")
    
    empresa = empresa.replace(' ', '-')
    
    try:
        user_document = db.collection("dadosUsuarios").document(uuid)
        doc = user_document.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Usuário com UUID {uuid} não encontrado.")

        user_data = doc.to_dict()
        
        web_scrapping_dados = user_data.get("web_scrapping_dados", [])
        novo_web_scrapping_dados = [item for item in web_scrapping_dados if empresa not in item]
        
        if len(novo_web_scrapping_dados) == len(web_scrapping_dados):
            raise HTTPException(status_code=404, detail=f"Nenhuma reclamação encontrada para a empresa {empresa} no histórico do usuário.")

        user_document.update({
            "web_scrapping_dados": novo_web_scrapping_dados
        })
        
        return {"status_code": 200, "mensagem": f"Reclamações para a empresa {empresa} foram apagadas com sucesso."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar os dados: {str(e)}")