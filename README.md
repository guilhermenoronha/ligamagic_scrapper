# Liga Magic Scrapper
[![](https://img.shields.io/static/v1?label=python&message=3.10&color=blue&logo=python)](https://www.python.org/downloads/release/python-3100/)
[![](https://img.shields.io/static/v1?label=linter&message=flake8&color=green&logo=flake8)](https://flake8.pycqa.org/en/latest/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![](https://img.shields.io/static/v1?label=unit-tests&message=pytest&color=green&logo=pytest)](https://docs.pytest.org/en/latest/)
![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/guilhermenoronha/parquet-to-hyper/python-package.yml?label=tests)


Scrapper pra pegar os melhores preços de cartas dentre as lojas selecionadas pelo jogador.

**ATENÇÃO:** use com moderação. Scrappers podem sobrecarregar o servidor da Liga Magic. Use apenas para uso pessoal, esporadicamente e com poucas cartas.

Script ainda em fase de testes. Podendo conter bugs e comportamentos erráticos.

## Introdução

O objetivo deste script é coletar, dentre as lojas de interesse, qual delas possui o melhor preço para a lista de compras de cartas avulsas. Além disso, este script compara os preços encontrados nas lojas com o menor preço encontrado na Liga Magic. Assim, fica fácil de comparar se os preços praticados nas lojas de interesse estão competitivos ou não em relação ao mercado nacional de magic. 


## Como usar?

Este projeto serve para coletar alguns insights relacionados à lista de compra de *singles* em relação às lojas de interesse e ao mercado nacional de Magic. O scrapper busca quais *singles* estão disponíveis nas lojas de interesse. Além disso ele extrai algumas métricas como:

- Quantidade em estoque.
- Quantidade de ofertas mais baratas que foram encontradas em outras lojas.
- Valor mínimo e médio da liga.
- Valor encontrado na loja.
- Ágio/Deságio do valor encontrado na loja em relação aos preços mínimo e médio.

Essas métricas ajudam na tomada de decisão na hora de comprar uma carta ou não.

Exemplo:
 
 - A carta Tutor Demoníaco está 189,99 na UG Cardshop.
 - O menor preço mínimo e médio encontrado foi de 125.
 - Existem 53 ofertas melhores de tutor demoníaco que a da UG Cardshop.
 - O preço está 52% mais caro em relação ao preço médio e ao preço mínimo.
 - Vale a pena comprar esta carta?

## Configuração

Segue o passo a passo para instalar e configurar o projeto.

### Instalação

- Requer [Python](https://www.python.org/downloads/release/python-31110/) (testado apenas em Python 3.10)
- Instale o poetry com o comando `pip install poetry`
- Abra o terminal na pasta do projeto e inicialize o projeto com o comando `poetry install`

### Configuração

#### Arquivo .env

- Crie um arquivo .env na raiz do projeto. Ele deve conter duas configurações:
    
    - **MINIMAL_CARD_QUALITY**: qual é qualidade mínima que você aceita durante a busca de cartas? Valores aceitos: D, HP, MP, SP, NM. 
    
        Exemplo de uso:  MINIMAL_CARD_QUALITY=HP

    - **ACCEPTED_LANGUAGES**: quais são os idiomas que você aceita durante a busca de carta? Esta variável aceita múltiplos valores separados por vírgula.
    
        Exemplo de uso: ACCEPTED_LANGUAGES=Português,Inglês,Português / Inglês

#### Arquivo cardlist.txt

Na pasta `assets/inputs/` crie um arquivo cardlist.txt. Este é o arquivo com a lista de cartas que será buscada pelo script. Ela possui o padrão de exportação de sites comuns de magic. Cartas que possuem dupla face, devem ter apenas o primeiro nome na lista. Um exemplo de como preencher a lista é encontrado em `assets/inputs/cardlist_example.txt` 

#### Arquivo stores.csv

Crie um arquivo stores_example.csv na pasta `assets/inputs`. Este arquivo deve conter informações sobre as lojas de interesse contendo as seguintes colunas:

- **name**: nome da loja. O nome deve ser o mesmo que consta no site da Liga Magic. Para saber qual é o nome da sua loja na Liga Magic, veja a seção X.
- **url**: url da loja.
- **discount**: coloca um valor em percentual caso a loja ofereça algum desconto em pagamentos pix, etc.

Um exemplo de como preencher as lojas é encontrado em `assets/inputs/stores_example.txt`

### Execução

Para executar o script, basta abrir o terminal e rodar o comando `poetry run python main.py`

## FAQ e problemas conhecidos

### Como pegar o nome correto da loja?

Nem sempre o nome da loja estará cadastrado corretamente no site da Liga Magic. Para descobrir, existe um truque bem simples:

- Abra o site da Liga Magic no seu navegador e pesquise por uma carta qualquer.
- Aperte F12 no seu navegador e encontre uma oferta da loja alvo.

Em seguida repita os passos mostrados na figura abaixo:

1. Clique no botão de seleção.
2. Clique no banner da loja alvo.
3. Procure pelo nome da loja no código da página.

![teste](https://github.com/user-attachments/assets/ed10c9c2-dca9-41f6-9d9e-4ec71b63ccef)

Observe que neste caso, a Vault of Cards está cadastrada apenas como Vault na Liga Magic.

### O script está lento, é comum?

Sim. O script foi desenvolvido usando a biblioteca Selenium, que tem uma performance ruim. Infelizmente não encontrei outra biblioteca que consiga fazer scrapper da Liga Magic. A solução é usar listas pequenas de cartas.

### O script deu erro. Como proceder?

Em alguns casos, o script pode gerar um erro aleatório de requisições e travar. Isto acontece principalmente quando a lista de cartas é muito grande e o servidor bloqueia requisições futuras. 

Sempre que isto ocorrer, faça os seguintes procedimentos:

- Veja quais cartas foram extraídas no arquito **cards.csv**. 
- Em seguida remova estas cartas da sua lista de inputs em **cardlist.txt**.
- Rode novamente o script. 
- Repita este processo até o script extrair todas as cartas.

### Como contribuir?

Contribua com melhorias para o projeto abrindo issues no github ou submetendo suas próprias melhorias.