# TechStore HTTP Monitor

Servidor Flask que combina uma loja virtual fictícia com um **monitor de
requisições HTTP em tempo real**. A loja existe apenas como fachada para
gerar tráfego variado (GET, POST, erros 404/500); o verdadeiro objetivo do
projeto é o dashboard `/monitor`, que transforma esse tráfego em métricas e
gráficos visíveis — um pequeno laboratório de observabilidade HTTP.

## Sumário

- [Visão geral](#visão-geral)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Instalação](#instalação)
- [Como executar](#como-executar)
- [Rotas disponíveis](#rotas-disponíveis)
- [O monitor HTTP](#o-monitor-http)
- [Métricas de rede](#métricas-de-rede)
- [Notas técnicas e decisões de design](#notas-técnicas-e-decisões-de-design)


## Visão geral

| | |
|---|---|
| **Linguagem** | Python 3.10+ |
| **Framework** | Flask 3.x |
| **Persistência** | Nenhuma — dados fictícios e histórico ficam em memória |
| **Arquivo principal** | `artifacts/flask-api/app.py` |

O servidor expõe duas frentes:

1. **Loja simulada** — páginas de produtos, categorias, carrinho, login, blog,
   pedidos e contato, com dados fixos (sem banco de dados).
2. **Monitor HTTP** (`/monitor`) — um middleware (`before_request` /
   `after_request`) intercepta toda requisição, mede sua duração e grava um
   histórico em memória. O dashboard consome esse histórico via polling
   (atualização automática a cada 2 segundos) e exibe gráficos de método,
   status, tempo de resposta, ranking de rotas e métricas de rede.

## Estrutura do projeto

```
TechStore/
├── app.py             # Servidor Flask completo (loja + monitor)
└── requirements.txt   # Dependências (flask>=3.0.0)
```

> O restante do repositório (`lib/`, outros pacotes em `artifacts/`,
> `pnpm-lock.yaml`, `tsconfig*.json` etc.) pertence ao monorepo gerado pelo
> Replit e **não é necessário** para rodar este servidor Flask.

## Instalação

**Pré-requisitos:** Python 3.10 ou superior.

```bash
# 1. Acesse a pasta do servidor
cd artifacts/flask-api

# 2. (Recomendado) crie um ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Instale as dependências
python -m pip install -r requirements.txt
```

Se o `pip` do seu sistema estiver com problemas (erro de launcher no Windows,
por exemplo), prefira sempre `python -m pip install ...` em vez de chamar o
`pip` diretamente — isso evita depender de um executável `pip.exe` que pode
estar apontando para uma instalação Python incorreta.

## Como executar

```bash
python app.py
```

O servidor inicia em modo debug, escutando em todas as interfaces:

```
* Running on http://127.0.0.1:5000
* Running on http://0.0.0.0:5000
```

Acesse no navegador:

| Recurso | URL |
|---|---|
| Loja (página inicial) | http://127.0.0.1:5000 |
| Monitor HTTP (dashboard) | http://127.0.0.1:5000/monitor |

A porta pode ser alterada pela variável de ambiente `PORT`:

```bash
PORT=8080 python app.py
```

## Rotas disponíveis

### Páginas (HTML)

| Rota | Descrição |
|---|---|
| `GET /` | Início — destaques e estatísticas da loja |
| `GET /produtos` | Listagem de produtos, com filtro por categoria e busca |
| `GET /produtos/<id>` | Detalhe de um produto, com itens relacionados |
| `GET /categorias` | Listagem de categorias |
| `GET /carrinho` | Carrinho de compras (estático/demonstrativo) |
| `GET /login` | Formulário de login |
| `GET /sobre` | Sobre a loja e stack tecnológico |
| `GET /contato` | Formulário de contato |
| `GET /blog` | Listagem de posts |
| `GET /blog/<slug>` | Post individual |
| `GET /pedidos` | Histórico de pedidos fictícios |

### API (JSON)

| Rota | Método | Descrição |
|---|---|---|
| `/api/produtos` | GET | Lista todos os produtos |
| `/api/produtos/<id>` | GET | Detalhe de um produto |
| `/api/comprar` | POST | Simula adicionar um produto ao carrinho |
| `/api/usuarios/<id>` | GET / PUT / DELETE | Consulta, atualização ou remoção fictícia de usuário |
| `/api/login` | POST | Simula autenticação |
| `/api/contato` | POST | Simula envio de formulário de contato |
| `/api/pedidos` | GET | Lista todos os pedidos |

### Simulação de erros

| Rota | Descrição |
|---|---|
| `GET /simular/404` | Força uma resposta 404, para testar o monitor |
| `GET /simular/500` | Força uma resposta 500, para testar o monitor |

### Monitor

| Rota | Método | Descrição |
|---|---|---|
| `/monitor` | GET | Dashboard visual (HTML) |
| `/monitor/stats` | GET | Métricas agregadas (JSON) — consumida pelo dashboard |
| `/monitor/requisicoes` | GET | Histórico bruto de requisições (JSON). Aceita `?limite=N` |
| `/monitor/limpar` | POST | Zera o histórico em memória |

## O monitor HTTP

O middleware funciona em três peças:

1. **`@app.before_request`** — marca o instante de início de cada requisição.
2. **`@app.after_request`** — calcula a duração, monta uma entrada com
   método, rota, status, tempo de resposta, IP, User-Agent e tamanho de
   requisição/resposta, e grava no histórico (uma `deque` limitada a 500
   entradas).
3. **`@app.errorhandler(Exception)`** — garante que **nenhuma** requisição
   escape do monitor, mesmo quando uma exceção não tratada interromperia a
   view antes do `after_request` rodar. Erros HTTP (`abort(404)`,
   `abort(500)`) continuam seguindo o fluxo padrão do Flask; exceções
   genuinamente inesperadas (bugs de código) recebem uma página de erro 500
   genérica, e o registro do histórico acontece de forma centralizada no
   `after_request` em ambos os casos — sem duplicar entradas.

O dashboard (`/monitor`) busca `/monitor/stats` e `/monitor/requisicoes` a
cada 2 segundos via `fetch` e redesenha:

- Contadores: total de requisições, respostas 2xx, erros (4xx/5xx), taxa de
  erro, tempo médio de resposta.
- Gráficos de barra por método HTTP e por status code.
- Tempo de resposta (mínimo / médio / máximo).
- Ranking das rotas mais acessadas.
- Métricas de rede (ver seção a seguir).
- Feed de requisições em tempo real, com horário, método, status, tempo, IP
  e rota.

## Métricas de rede

Além das métricas originais de tempo e status, o monitor também coleta:

- **Tamanho de requisição/resposta** — bytes de cada chamada
  (`Content-Length`), com médias agregadas em `/monitor/stats`.
- **Top IPs de origem** — IP do cliente (`request.remote_addr`), com suporte
  a `X-Forwarded-For` quando o servidor está atrás de um proxy reverso.
- **Dispositivos e navegadores** — classificação simples do `User-Agent` em
  `desktop` / `mobile` / `outro` e em `chrome` / `firefox` / `safari` /
  `edge` / outros, por busca de palavras-chave na própria string (o
  Werkzeug 3.x não inclui mais um parser de User-Agent embutido).
- **Throughput** — total de bytes transferidos (requisição + resposta)
  dividido pela janela de tempo coberta pelo histórico considerado,
  expresso em bytes por segundo.

Essas métricas ficam disponíveis em `/monitor/stats` dentro do campo `rede`,
e são exibidas no dashboard nos painéis **Top IPs de Origem** e
**Dispositivos & Navegadores**, além dos cards de tráfego total e
throughput no topo da página.

## Notas técnicas e decisões de design

- **Sem banco de dados**: produtos, usuários, pedidos e posts do blog são
  listas/dicionários Python fixos no próprio `app.py`. O foco do projeto é o
  comportamento HTTP, não persistência.
- **Histórico em memória**: o monitor usa uma `collections.deque(maxlen=500)`
  — reiniciar o servidor zera o histórico.
- **Renderização sem Jinja2**: a função `layout()` monta o HTML via f-string
  Python e devolve uma `flask.Response` diretamente (em vez de
  `render_template_string`). Isso evita uma segunda passada de interpretação
  de template sobre conteúdo que já inclui JavaScript com chaves (`{ }`),
  que historicamente colidia com a sintaxe `{{ }}` do Jinja2.
- **Rotas ignoradas pelo monitor**: `/monitor/requisicoes`,
  `/monitor/stats` e `/monitor/limpar` não geram entradas no próprio
  histórico, para não poluir as métricas com o tráfego do dashboard
  monitorando a si mesmo.
