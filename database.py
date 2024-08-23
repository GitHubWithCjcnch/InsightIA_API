import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
def iniciar_conexao():
    # Obtém as credenciais do ambiente
    database = os.getenv('FIREBASE_CREDENTIALS')

    if database is None:
        chave_acesso = 'C:/Users/User/Desktop/InsightIA/db_config.json'
        print(f"As credenciais do Firebase não foram encontradas na variavel de ambiente: {database}")
    else:
        chave_acesso = json.loads(database)
    
    cred = credentials.Certificate(chave_acesso)
    firebase_admin.initialize_app(cred)

    return firestore.client()