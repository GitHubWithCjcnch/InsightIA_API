import os
import google.generativeai as genai
import json

prompt = """
Quero que analise este json e me retorne estas informações, enriquece bastante com valores estatisticos seguindo este modelo(pode varias um pouco as palavras conforme necessário para contexto) e formate o melhor que puder:

{EMPRESA} teve {numero de reclamações analisadas} reclamações coletadas e obtemos os seguintes insights:
	Houve diversas reclamações envolvendo {palavras com maiores números de repeticoes} em contextos como {1 contexto nos dados}.
	Concluindo temos algumas sugestões de atenção:
	{Monte de 3 até 5 sugestões pertinentes para pontuar insight valiosos}

Segue textos de reclamacoes.
"""

def configurar_modelo():
    gemini_key = os.getenv('GEMINI_KEY')
    gemini_key = 'AIzaSyCoZBHkcJCnN2VBc5DzeUkMNDc8GKiG8GY'
    if not gemini_key:
        raise ValueError("A chave da API do GEMINI IA não foi encontrada na variável de ambiente 'GEMINI_KEY'.")
    
    genai.configure(api_key=gemini_key)
    return genai.GenerativeModel('gemini-1.5-flash')


def interacao_gemini(model, parts, temperature=0.7):
    try:
        response = model.generate_content(
            {"parts": parts}, 
            generation_config=genai.types.GenerationConfig(temperature=temperature)
        )

        if not response or not response.text:
            raise ValueError("A resposta gerada está vazia!")

        return response.text

    except Exception as e:
        raise ValueError(f"Erro durante a interação com o modelo: {str(e)}")


def conversa_gemini(model, prompt):
    parts = [{"text": prompt}]
    return interacao_gemini(model, parts)

def gerar_analise(model, dados):
    dados_clean = json.dumps(dados, indent=2)
    parts = [{"text": prompt}, {"text": dados_clean}]
    return interacao_gemini(model, parts, temperature=0.2)

def gerar_analise_complexa(model, dados):
    dados_clean = json.dumps(dados, indent=2)
    details = {}
    chat = model.start_chat(history=[])
    chat.history.append({"role": "user", "parts": [{"text": prompt}, {"text": dados_clean}] })
    response = chat.send_message("Faça sugestões de melhoria. (Seu retorno sera mostrado em uma tela, entao seja agradavel para usuario e nao confunda)")
    details['sugestao'] = response.text
    response = chat.send_message("Possiveis causas e soluções. (Seu retorno sera mostrado em uma tela, entao seja agradavel para usuario e nao confunda)")
    details['causas'] = response.text
    return details