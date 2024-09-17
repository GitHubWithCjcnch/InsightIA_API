﻿# InsightIA_API (DEVE USAR A BRANCH caio)

## API Python - Azure Web App Service
Este repositório contém o código fonte de uma API desenvolvida em Python 3.10. O deploy é realizado na plataforma Azure Web App Service. O objetivo deste README é fornecer todas as informações necessárias para o deploy e testes da API.

###Índice
- Pré-requisitos
- Instalação
- Deploy na Azure
- Configuração do Firestore
- Scripts JSON de CRUD
- Testando a API
- Tecnologias Utilizadas

Pré-requisitos
Antes de realizar o deploy da aplicação, certifique-se de ter:

Conta no Azure com permissão para criar um Web App Service.
Python 3.10 instalado na máquina local.
API KEY para Firebase Firestore configurado para integração de dados.
API KEY para Gemini AI ou outro modelo de AI integrado (opcional, se aplicável).

###Instalação
1. Clone o repositório
```bash
git clone https://github.com/GitHubWithCjcnch/InsightIA_API.git
```

2. Crie um ambiente virtual e ative-o:
```bash
python -m venv venv
source venv/bin/activate
```

3. Instale as depedências:
```bash
pip install -r requirements.txt
```

###Deploy na Azure
Etapas para o deploy:
1. Login no Azure CLI:
```bash
az login
```

2. Criação do Web App:
Certifique-se de estar no diretório raiz do projeto e execute o seguinte comando:
```bash
az webapp up --runtime "PYTHON:3.10" --name <nome-do-app> --resource-group <grupo-de-recursos> --location <local>
```
- Substitua <nome-do-app>, <grupo-de-recursos>, e <local> com os valores correspondentes à sua configuração.

3. Configuração de variáveis de ambiente:
Será necessário navegar até Web App -> Configurações -> Configurações do aplicativo para colocar as variáveis de ambiente da aplicação para ela funcionar corretamente (cheque o teams no seu privado, estarei mandando as minhas para você testar...)

###Testando a API
####Testando localmente
1. Para rodar a API localmente, execute o seguinte comando:
```bash
uvicorn app.main:appApi --reload
```
2. Acesse http://127.0.0.1:8000 no navegador ou use uma ferramenta como o Postman para fazer requisições.

####Testando na Azure
Após o deploy, use o endereço gerado pela Azure para fazer requisições à API. Com o domínio padrão em mãos, deve colocar um /doc ao final para acessar a documentação do swagger na api. Por exemplo:
possuo este domínio -> insightaiapi.azurewebsites.net
ao final eu adiciono um '/doc' para acessar a documentação da api -> insightaiapi.azurewebsites.net/doc


###informações importantes
para testar os endpoints utilize este uuid conforme mostrado no video também -> 5rSzJuZMt6hkAVyR2dkd02GIQ1X2
veja o teams para ter as api_keys para serem colocadas na aplicação, se não ela não irá funcionar (vale comentar que caso queira rodar local, adicione um .env na pasta root do projeto e coloque as apikeys la dentro)
