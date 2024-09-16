import time
import os
from dotenv import load_dotenv
from fastapi import HTTPException
import google.generativeai as genai

setores = {
    "Bancos e Financeiras": [
        "Atendimento ao cliente",
        "Operações",
        "Tecnologia da Informação",
        "Risco",
        "Compliance",
        "Marketing",
        "Recursos Humanos"
    ],
    "Telefonia, TV e Internet": [
        "Atendimento ao cliente",
        "Rede",
        "Comercial",
        "Engenharia",
        "Tecnologia da Informação",
        "Financeiro"
    ],
    "Turismo e Lazer": [
        "Reservas",
        "Hospedagem",
        "Alimentação e Bebida",
        "Transporte",
        "Entretenimento",
        "Marketing"
    ],
    "Software": [
        "Desenvolvimento",
        "Qualidade",
        "Vendas",
        "Marketing",
        "Suporte técnico"
    ],
    "Casa e Construção": [
        "Vendas",
        "Projetos",
        "Construção",
        "Materiais",
        "Acabamento",
        "Marketing"
    ],
    "Saúde": [
        "Atendimento médico",
        "Administrativo",
        "Laboratório",
        "Farmácia",
        "Marketing"
    ],
    "Alimentos e Bebidas": [
        "Produção",
        "Qualidade",
        "Logística",
        "Vendas",
        "Marketing"
    ],
    "Setor Imobiliário": [
        "Corretoria",
        "Construção",
        "Administração de imóveis",
        "Marketing",
        "Financeiro"
    ],
    "Veículos e Acessórios": [
        "Produção",
        "Vendas",
        "Pós-venda",
        "Marketing",
        "Pesquisa e Desenvolvimento"
    ],
    "Varejo": ["Vendas", "Estoque", "Marketing, Logística, Financeiro"]
}

load_dotenv()

# AUTH FOR GEMINI
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# model = genai.GenerativeModel('gemini-1.5-flash') - isso aq é pra gerar o gemini-1.5-flash uma versao pior doq o pro
generation_config = {
  "temperature": 0.2,
  "top_p": 0.8,
  "top_K": 64,
  "max_output_tokens": 100
}
model = genai.GenerativeModel('gemini-1.5-flash')


def safe_generate_content(prompt, retry_count=5, retry_delay=10):
    for _ in range(retry_count):
        try:
            return model.generate_content(prompt)
        except Exception as e:
            if '429' in str(e):
                time.sleep(retry_delay)
                continue
            raise e
    raise HTTPException(status_code=500, detail="Quota excedeu, por favor tente novamente depois.")

def criar_analise_interna(dados, empresa, ramo_empresa):
    if not dados:
        raise ValueError("Dados não fornecidos ou vazios.")
    
    result = []
        
    try:
        categorias_problema = []
        quantidade_categorias_problema = []
        percentual_categorias_problema = []
        response_all_categorias = []
        
        for categoria_data in dados:
            categoria_problema = categoria_data.get("categoria", "Categoria não especificada")
            percentual_categoria_problema = str(categoria_data.get("percentual", "Percentual não especificada"))
            quantidade_categoria_problema = str(categoria_data.get("quantidade", "Quantidade não especificada"))
            
            reclamacoes = [reclamacao["descricao"] for reclamacao in categoria_data.get("reclamacoes", [])]

            categorias_problema.append(categoria_problema)
            quantidade_categorias_problema.append(quantidade_categoria_problema)
            percentual_categorias_problema.append(percentual_categoria_problema)

            reclamacoes_text = ',\n'.join([f"'{reclamacao}'" for reclamacao in reclamacoes])

            main_question = (
                f"Possuo essas reclamações, na categoria de problema '{categoria_problema}', "
                f"abaixo acerca de uma empresa chamada {empresa} que está no ramo de {ramo_empresa}:\n\n"
                f"{reclamacoes_text}\n\n"
                "Analise as reclamações pensando na categoria de problema que ela está inserida e faça um resumo.\n"
                "Em seguida liste para mim, ao menos, 5 possíveis causas e soluções, de forma geral, dos problemas ditos.\n"
            )

            main_response = safe_generate_content(main_question)

            response_all_categorias.append(main_response.text)

        for index, response_categoria in enumerate(response_all_categorias):
            result.append({
                "categoria_problema": categorias_problema[index],
                "percentual": percentual_categorias_problema[index],
                "quantidade": quantidade_categorias_problema[index],
                "analise_geral": response_categoria
            })
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar análise interna: {str(e)}")
    
    
def criar_analise_reclamacao(reclamacao, empresa, ramo):
    try: 
       setores_internos = setores.get(ramo, [])
    
       main_question = (
           f"Possuo essa reclamação abaixo acerca de uma empresa chamada {empresa} que está no ramo de {ramo}: \n\n"
           f"{reclamacao}\n\n"
           "Analise a reclamação, de forma a descobrir em qual(is) setor(es) interno(s) a reclamação está relacionada. Considere os seguintes setores internos:\n"
       )
    
       if setores_internos:
           for setor in setores_internos:
               main_question += f"- {setor}\n"
       else:
           main_question += "Não foram encontrados setores internos para este ramo.\n"

       main_question += (
        "\nBaseie sua análise nos setores acima e me forneça os seguintes dados: \n"
        "- Setores envolvidos e porque está envolvido naquele setor \n"
        "- Observação relacionado a reclamação, alguma informação útil que possa se adicionar. \n"
        "- Gere para mim uma resposta geral para essa categoria, de forma a retornar para o cliente o mais rápido possível alguma resposta, siga o formato como exemplo:\n\n"
        "' Prezado(a) cliente, já estamos analisando o seu problema.\n\n"
        "  [descricao geral do problema]\n\n"
        "  Para melhora mais fácil em relação ao seu problema, por favor me envie com mais detalhes em meu email {empresa}@{empresa}.com\n"
        "  [peça dados do cliente para atendimento privado via email ficticio da empresa]\n\n"
        f"  Atenciosamente,\n  {empresa}\n"
       )
       main_response = safe_generate_content(main_question)
       return main_response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar análise da reclamação: {str(e)}")
    

def criar_analise_concorrente(dados_empresa_interna, dados_empresa_externa, empresa_interna, empresa_externa, ramo_empresa):
    if not dados_empresa_interna or not dados_empresa_externa:
        raise ValueError("Dados não fornecidos ou vazios.")
    
    try:
        result = []

        for interna_data in dados_empresa_interna.get("categorias", []):
            categoria_problema = interna_data.get("categoria", "Categoria não especificada")
            percentual_categoria_problema_interna = str(interna_data.get("percentual", "Percentual não especificado"))
            quantidade_categoria_problema_interna = str(interna_data.get("quantidade", "Quantidade não especificada"))
            
            externa_data = next((cat for cat in dados_empresa_externa.get("categorias", []) if cat.get("categoria") == categoria_problema), None)
            
            if externa_data:
                percentual_categoria_problema_externa = str(externa_data.get("percentual", "Percentual não especificado"))
                quantidade_categoria_problema_externa = str(externa_data.get("quantidade", "Quantidade não especificada"))
                
                reclamacoes_interna = [reclamacao["descricao"] for reclamacao in interna_data.get("reclamacoes", [])]
                reclamacoes_externa = [reclamacao["descricao"] for reclamacao in externa_data.get("reclamacoes", [])]

                reclamacoes_interna_text = ',\n'.join([f"'{reclamacao}'" for reclamacao in reclamacoes_interna])
                reclamacoes_externa_text = ',\n'.join([f"'{reclamacao}'" for reclamacao in reclamacoes_externa])

                main_question = (
                    f"Compare as reclamações entre duas empresas na categoria de problema '{categoria_problema}' "
                    f"no ramo de {ramo_empresa}.\n\n"
                    f"Minha Empresa ({empresa_interna}):\n"
                    f"{reclamacoes_interna_text}\n\n"
                    f"Empresa Concorrente ({empresa_externa}):\n"
                    f"{reclamacoes_externa_text}\n\n"
                    "Analise e compare as reclamações para esta categoria de problema e faça um resumo da comparação. Esse resumo deve pontuar os aspectos fortes e fracos em ambas as empresas em texto corrido.\n"
                    "Em seguida, liste os pontos fortes e fracos ditos no resumo.\n"
                )

                main_response = safe_generate_content(main_question)

                result.append({
                    "categoria_problema": categoria_problema,
                    "percentual_empresa_interna": percentual_categoria_problema_interna,
                    "quantidade_empresa_interna": quantidade_categoria_problema_interna,
                    "percentual_empresa_externa": percentual_categoria_problema_externa,
                    "quantidade_empresa_externa": quantidade_categoria_problema_externa,
                    "analise_geral": main_response.text
                })
        
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar análise concorrente: {str(e)}")
