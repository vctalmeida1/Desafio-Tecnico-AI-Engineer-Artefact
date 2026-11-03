# Empório da Música — agente de atendimento

Estrutura de um futuro agente de atendimento em Python. A camada inicial de leitura dos CSVs e as ferramentas comerciais independentes estão implementadas. O atendimento, a ligação ao Gemini por Function Calling e o processamento do manual ainda não foram implementados.

O planejamento é feito no ChatGPT e a execução técnica do projeto é feita pelo Codex.

## Tecnologias

- Python
- Google Gemini pela SDK oficial `google-genai`
- Arquivos CSV como fonte operacional
- Manual PDF como fonte de políticas e informações institucionais

O modelo configurado é `gemini-3.8-flash`. A versão está definida centralmente em `src/config/settings.py` para facilitar futuras alterações.

## Estrutura

```text
├── data/
│   ├── raw/          # CSVs operacionais originais
│   └── knowledge/    # Manual PDF original
├── src/
│   ├── config/       # Configuração centralizada
│   ├── data/         # Carregamento, validação e contexto de identidade
│   ├── agent/        # Integração inicial Gemini e futuro agente
│   ├── tools/        # Ferramentas comerciais independentes
│   └── interfaces/   # Futuras interfaces
├── scripts/          # Scripts manuais, incluindo o teste de conexão
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Ambiente e dependências

Ative o ambiente virtual na raiz do projeto:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale as dependências declaradas:

```powershell
python -m pip install -r requirements.txt
```

## Chave da API

Copie o exemplo e preencha `GEMINI_API_KEY` com sua chave local:

```powershell
Copy-Item .env.example .env
```

O arquivo `.env` é ignorado pelo Git. A configuração também aceita `GEMINI_API_KEY` definida diretamente no ambiente. Não registre ou compartilhe a chave.

## Teste manual de comunicação

O script faz uma chamada real à API e só deve ser executado quando você quiser testar a comunicação:

```powershell
python -m scripts.test_gemini_connection
```

Sem a chave configurada, o script encerra sem fazer requisição. A faixa gratuita do modelo está sujeita aos limites e às condições atuais do Google.

## Camada de dados e ferramentas

O carregador `src/data/repository.py` valida cabeçalhos, tipos e relacionamentos dos seis CSVs em UTF-8. O acesso usa a biblioteca padrão do Python, sem pandas. As ferramentas disponíveis são exportadas por `src/tools/`:

- `buscar_produto(termo=..., nome=..., categoria=...)`
- `consultar_estoque(product_id)`
- `consultar_promocao(product_id)`
- `consultar_pedido(order_id, identidade_verificada=...)`
- `consultar_itens_pedido(order_id, identidade_verificada=...)`
- `buscar_cliente(identificador)`

Valores opcionais ausentes, como rastreamento e previsão de entrega, são retornados como `None`. Estoque zero não é disponibilidade; produtos fora do status comercial `active` não são considerados vendáveis. A consulta de promoções retorna apenas promoções ativas e não calcula preços promocionais.

Pedidos e itens exigem um `VerifiedCustomerContext` confiável. O fluxo de verificação de identidade ainda precisa ser definido; somente a camada confiável da aplicação deverá criar esse contexto depois da validação. Não passe esse contexto por argumentos gerados pelo modelo.

Execute os testes automatizados (não fazem chamadas ao Gemini):

```powershell
python -m unittest discover -s tests -v
```

## Function Calling

O Gemini suporta Function Calling. Em uma etapa futura, o modelo poderá receber definições dessas funções Python e retornar chamadas estruturadas com nome e argumentos. A aplicação validará os argumentos, executará a função comercial apropriada e enviará o resultado ao modelo para compor a resposta. As ferramentas ainda não estão conectadas ao Gemini.

## Dados

Os CSVs originais estão em `data/raw/` e são lidos como UTF-8; o manual original está em `data/knowledge/manual.pdf`. Os arquivos originais não foram alterados. A ausência de valores opcionais nos CSVs permanece representada como informação não disponível.

