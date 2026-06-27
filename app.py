import time
import os
from collections import deque
from datetime import datetime
from flask import Flask, jsonify, request, abort, render_template_string, Response

app = Flask(__name__)

MAX_HISTORICO = 500
historico = deque(maxlen=MAX_HISTORICO)

# ──────────────────────────────────────────
# Dados fictícios (simulando banco de dados)
# ──────────────────────────────────────────

PRODUTOS = [
    {"id": 1,  "nome": "Notebook Pro 15",      "preco": 4299.90, "categoria": "informatica", "estoque": 12, "avaliacao": 4.8},
    {"id": 2,  "nome": "Mouse Gamer RGB",       "preco":   189.90, "categoria": "informatica", "estoque": 45, "avaliacao": 4.5},
    {"id": 3,  "nome": "Teclado Mecânico",      "preco":   349.90, "categoria": "informatica", "estoque": 30, "avaliacao": 4.7},
    {"id": 4,  "nome": "Monitor 27\" 4K",       "preco":  2199.90, "categoria": "informatica", "estoque":  8, "avaliacao": 4.9},
    {"id": 5,  "nome": "Headset Bluetooth",     "preco":   299.90, "categoria": "audio",       "estoque": 20, "avaliacao": 4.3},
    {"id": 6,  "nome": "Webcam Full HD",        "preco":   249.90, "categoria": "informatica", "estoque": 15, "avaliacao": 4.4},
    {"id": 7,  "nome": "SSD 1TB NVMe",          "preco":   399.90, "categoria": "informatica", "estoque": 25, "avaliacao": 4.8},
    {"id": 8,  "nome": "Caixa de Som Bluetooth","preco":   159.90, "categoria": "audio",       "estoque": 35, "avaliacao": 4.2},
    {"id": 9,  "nome": "Smartphone X12",        "preco":  3199.90, "categoria": "celulares",   "estoque":  6, "avaliacao": 4.6},
    {"id": 10, "nome": "Tablet Pro 10\"",       "preco":  1899.90, "categoria": "celulares",   "estoque": 10, "avaliacao": 4.5},
    {"id": 11, "nome": "Carregador Turbo 65W",  "preco":    99.90, "categoria": "acessorios",  "estoque": 60, "avaliacao": 4.1},
    {"id": 12, "nome": "Cabo USB-C 2m",         "preco":    39.90, "categoria": "acessorios",  "estoque": 80, "avaliacao": 4.0},
]

CATEGORIAS = [
    {"id": 1, "slug": "informatica",  "nome": "Informática",  "icone": "💻", "descricao": "Notebooks, periféricos e componentes"},
    {"id": 2, "slug": "audio",        "nome": "Áudio",        "icone": "🎧", "descricao": "Headsets, caixas de som e fones"},
    {"id": 3, "slug": "celulares",    "nome": "Celulares",    "icone": "📱", "descricao": "Smartphones e tablets"},
    {"id": 4, "slug": "acessorios",   "nome": "Acessórios",   "icone": "🔌", "descricao": "Cabos, carregadores e adaptadores"},
]

USUARIOS = {
    1: {"id": 1, "nome": "Ana Silva",    "email": "ana@email.com",    "plano": "premium"},
    2: {"id": 2, "nome": "Bruno Costa",  "email": "bruno@email.com",  "plano": "basico"},
    3: {"id": 3, "nome": "Carla Mendes", "email": "carla@email.com",  "plano": "premium"},
}

PEDIDOS = [
    {"id": 101, "usuario_id": 1, "produto_id": 1,  "quantidade": 1, "status": "entregue",   "total": 4299.90},
    {"id": 102, "usuario_id": 2, "produto_id": 5,  "quantidade": 2, "status": "em_transito","total":  599.80},
    {"id": 103, "usuario_id": 1, "produto_id": 7,  "quantidade": 1, "status": "processando","total":  399.90},
    {"id": 104, "usuario_id": 3, "produto_id": 9,  "quantidade": 1, "status": "entregue",   "total": 3199.90},
]

BLOG_POSTS = [
    {"id": 1, "slug": "guia-notebook-2025",       "titulo": "Guia completo para escolher seu notebook em 2025",   "autor": "Ana Silva",    "data": "2025-05-10", "resumo": "Tudo que você precisa saber antes de comprar."},
    {"id": 2, "slug": "melhores-headsets",        "titulo": "Os 5 melhores headsets para home office",           "autor": "Bruno Costa",  "data": "2025-04-28", "resumo": "Compare os modelos mais vendidos do mercado."},
    {"id": 3, "slug": "ssd-vs-hd",               "titulo": "SSD ou HD? Qual vale mais a pena em 2025?",         "autor": "Carla Mendes", "data": "2025-04-15", "resumo": "Entenda as diferenças e faça a escolha certa."},
    {"id": 4, "slug": "configurar-home-office",   "titulo": "Como montar o home office perfeito",                "autor": "Ana Silva",    "data": "2025-03-30", "resumo": "Dicas práticas para aumentar sua produtividade."},
]

# ──────────────────────────────────────────
# Layout HTML base
# ──────────────────────────────────────────

def layout(titulo, corpo, ativo=""):
    nav_links = [
        ("/"         , "Início",     "inicio"),
        ("/produtos"  , "Produtos",   "produtos"),
        ("/categorias", "Categorias", "categorias"),
        ("/blog"      , "Blog",       "blog"),
        ("/sobre"     , "Sobre",      "sobre"),
        ("/contato"   , "Contato",    "contato"),
    ]
    nav_html = "".join(
        f'<a href="{href}" class="nav-link {"active" if ativo==key else ""}">{label}</a>'
        for href, label, key in nav_links
    )
    return Response(f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo} — TechStore</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',sans-serif;background:#f5f6fa;color:#222}}
  header{{background:#1a1a2e;color:#fff;padding:0 2rem}}
  .header-inner{{max-width:1100px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:60px}}
  .logo{{font-size:1.4rem;font-weight:700;color:#e94560;text-decoration:none}}
  nav{{display:flex;gap:.5rem}}
  .nav-link{{color:#ccc;text-decoration:none;padding:.4rem .8rem;border-radius:4px;font-size:.9rem;transition:.2s}}
  .nav-link:hover,.nav-link.active{{background:#e94560;color:#fff}}
  main{{max-width:1100px;margin:2rem auto;padding:0 1.5rem}}
  footer{{background:#1a1a2e;color:#888;text-align:center;padding:1.2rem;margin-top:4rem;font-size:.85rem}}
  .badge{{display:inline-block;padding:.2rem .6rem;border-radius:12px;font-size:.75rem;font-weight:600}}
  .badge-green{{background:#d4edda;color:#155724}}
  .badge-blue{{background:#cce5ff;color:#004085}}
  .badge-red{{background:#f8d7da;color:#721c24}}
  .btn{{display:inline-block;padding:.5rem 1.2rem;border-radius:6px;text-decoration:none;font-weight:600;font-size:.9rem;cursor:pointer;border:none}}
  .btn-primary{{background:#e94560;color:#fff}}
  .btn-outline{{background:transparent;border:2px solid #e94560;color:#e94560}}
  .card{{background:#fff;border-radius:10px;padding:1.5rem;box-shadow:0 2px 8px rgba(0,0,0,.07)}}
  .grid-3{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.5rem}}
  .grid-4{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:1.5rem}}
  h1{{font-size:1.8rem;margin-bottom:1rem;color:#1a1a2e}}
  h2{{font-size:1.3rem;margin-bottom:.8rem;color:#1a1a2e}}
  .price{{font-size:1.3rem;font-weight:700;color:#e94560}}
  .rating{{color:#f59e0b;font-size:.9rem}}
  .muted{{color:#888;font-size:.85rem}}
  table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.07)}}
  th{{background:#1a1a2e;color:#fff;padding:.8rem 1rem;text-align:left;font-size:.85rem}}
  td{{padding:.8rem 1rem;border-bottom:1px solid #f0f0f0;font-size:.9rem}}
  tr:last-child td{{border-bottom:none}}
  .hero{{background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;padding:3rem 2rem;border-radius:12px;margin-bottom:2rem;text-align:center}}
  .hero h1{{color:#fff;font-size:2.2rem}}
  .hero p{{color:#aaa;margin:1rem 0 1.5rem}}
  .stat-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:1rem;margin-bottom:2rem}}
  .stat-card{{background:#fff;border-radius:10px;padding:1.2rem;box-shadow:0 2px 8px rgba(0,0,0,.07);text-align:center}}
  .stat-num{{font-size:2rem;font-weight:700;color:#e94560}}
  .stat-label{{color:#888;font-size:.85rem;margin-top:.3rem}}
  .form-group{{margin-bottom:1rem}}
  .form-group label{{display:block;margin-bottom:.4rem;font-weight:600;font-size:.9rem}}
  .form-group input,.form-group textarea{{width:100%;padding:.6rem .8rem;border:1px solid #ddd;border-radius:6px;font-size:.9rem}}
  .alert{{padding:1rem 1.5rem;border-radius:8px;margin-bottom:1rem}}
  .alert-info{{background:#e0f0ff;color:#0066cc;border-left:4px solid #0066cc}}
</style>
</head>
<body>
<header>
  <div class="header-inner">
    <a class="logo" href="/">⚡ TechStore</a>
    <nav>{nav_html}</nav>
  </div>
</header>
<main>{corpo}</main>
<footer>
  © 2025 TechStore — Projeto de demonstração HTTP com Flask
  &nbsp;|&nbsp; <a href="/monitor/stats" style="color:#e94560">Monitor de Requisições</a>
</footer>
</body>
</html>""", mimetype="text/html")


# ──────────────────────────────────────────
# Middleware: registra cada requisição
# ──────────────────────────────────────────

def _ip_cliente():
    """Resolve o IP de origem, considerando proxy reverso (X-Forwarded-For)."""
    encaminhado = request.headers.get("X-Forwarded-For", "")
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    return request.remote_addr or "desconhecido"


def _dispositivo_user_agent():
    """
    Classifica o User-Agent em um rótulo simples de dispositivo/navegador.

    O Werkzeug 3.x não inclui mais um parser de User-Agent embutido
    (request.user_agent.platform/.browser retornam sempre None), então
    a classificação é feita aqui por palavras-chave na própria string —
    suficiente para fins de monitoramento, sem depender de bibliotecas externas.
    """
    ua_string = request.headers.get("User-Agent", "") or ""
    ua_lower = ua_string.lower()

    if not ua_string:
        return {"tipo": "outro", "navegador": "desconhecido", "string_completa": "—"}

    if "iphone" in ua_lower or "ipad" in ua_lower or "android" in ua_lower or "mobile" in ua_lower:
        tipo = "mobile"
    elif "windows" in ua_lower or "macintosh" in ua_lower or "linux" in ua_lower or "x11" in ua_lower:
        tipo = "desktop"
    else:
        tipo = "outro"

    if "edg/" in ua_lower:
        navegador = "edge"
    elif "chrome/" in ua_lower and "chromium" not in ua_lower:
        navegador = "chrome"
    elif "firefox/" in ua_lower:
        navegador = "firefox"
    elif "safari/" in ua_lower and "chrome/" not in ua_lower:
        navegador = "safari"
    elif "curl/" in ua_lower:
        navegador = "curl"
    elif "python-requests" in ua_lower or "werkzeug" in ua_lower:
        navegador = "script/teste"
    else:
        navegador = "outro"

    return {
        "tipo": tipo,
        "navegador": navegador,
        "string_completa": ua_string,
    }


@app.before_request
def iniciar_timer():
    request._tempo_inicio = time.time()


ROTAS_IGNORAR = {"/monitor/requisicoes", "/monitor/stats", "/monitor/limpar"}


def _registrar_entrada(status_code, tamanho_resposta_bytes):
    """Monta e grava no histórico uma entrada de requisição (sucesso ou erro)."""
    duracao_ms = round((time.time() - getattr(request, "_tempo_inicio", time.time())) * 1000, 2)
    dispositivo = _dispositivo_user_agent()
    entrada = {
        "timestamp": datetime.now().isoformat(),
        "metodo": request.method,
        "rota": request.path,
        "status": status_code,
        "tempo_ms": duracao_ms,
        "ip": _ip_cliente(),
        "user_agent": dispositivo["string_completa"],
        "dispositivo": dispositivo["tipo"],
        "navegador": dispositivo["navegador"],
        "bytes_requisicao": request.content_length or 0,
        "bytes_resposta": tamanho_resposta_bytes,
    }
    historico.appendleft(entrada)
    return entrada


@app.after_request
def registrar_requisicao(response):
    if request.path in ROTAS_IGNORAR:
        return response
    tamanho_resposta = response.calculate_content_length() or 0
    _registrar_entrada(response.status_code, tamanho_resposta)
    return response


@app.errorhandler(Exception)
def tratar_erro_nao_capturado(erro):
    """
    Garante que NENHUM erro escape do monitor.

    Sem este handler, uma exceção genuína não tratada (ex.: bug de
    código) interromperia a view e o Flask devolveria a tela de debug
    sem que o after_request chegasse a rodar — e o erro nunca apareceria
    no histórico do monitor.

    Com este handler registrado, o Flask sempre invoca o after_request
    sobre a resposta produzida aqui (para QUALQUER exceção, incluindo
    abort(404)/abort(500)), então o registro no histórico continua
    sendo feito em um único lugar: a função registrar_requisicao().
    Não duplicar o registro aqui.
    """
    from werkzeug.exceptions import HTTPException

    if isinstance(erro, HTTPException):
        # Mantém o comportamento padrão do Flask para erros HTTP (abort, 404, etc.)
        return erro

    # Exceção genuína não tratada: devolve uma página de erro 500 genérica.
    corpo_resposta = (
        "<h1>Erro interno do servidor</h1>"
        "<p>Ocorreu uma falha ao processar esta página.</p>"
    )
    return Response(corpo_resposta, status=500, mimetype="text/html")


# ──────────────────────────────────────────
# Páginas HTML
# ──────────────────────────────────────────

@app.route("/")
def index():
    destaques = PRODUTOS[:4]
    cards = "".join(f"""
    <div class="card">
      <div style="font-size:2rem;margin-bottom:.5rem">🛒</div>
      <h2>{p['nome']}</h2>
      <div class="rating">{"★" * int(p['avaliacao'])}{"☆" * (5 - int(p['avaliacao']))} {p['avaliacao']}</div>
      <div class="price">R$ {p['preco']:,.2f}</div>
      <div class="muted" style="margin-top:.5rem">{p['estoque']} em estoque</div>
      <br>
      <a href="/produtos/{p['id']}" class="btn btn-primary">Ver produto</a>
    </div>""" for p in destaques)

    corpo = f"""
    <div class="hero">
      <h1>Tecnologia ao seu alcance</h1>
      <p>Os melhores produtos de informática com entrega rápida e garantia estendida.</p>
      <a href="/produtos" class="btn btn-primary">Ver todos os produtos</a>
    </div>

    <div class="stat-grid">
      <div class="stat-card"><div class="stat-num">{len(PRODUTOS)}</div><div class="stat-label">Produtos disponíveis</div></div>
      <div class="stat-card"><div class="stat-num">{len(CATEGORIAS)}</div><div class="stat-label">Categorias</div></div>
      <div class="stat-card"><div class="stat-num">{len(USUARIOS)}</div><div class="stat-label">Clientes ativos</div></div>
      <div class="stat-card"><div class="stat-num">{len(PEDIDOS)}</div><div class="stat-label">Pedidos realizados</div></div>
    </div>

    <h1>Produtos em destaque</h1>
    <div class="grid-4">{cards}</div>
    <br>
    <div class="alert alert-info">
      🔍 Este é um servidor de demonstração HTTP. Cada clique gera uma requisição registrada no
      <a href="/monitor/stats"><strong>monitor em tempo real</strong></a>.
    </div>
    """
    return layout("Início", corpo, "inicio")


@app.route("/produtos")
def produtos_html():
    categoria_filtro = request.args.get("categoria")
    busca = request.args.get("busca", "").lower()

    lista = PRODUTOS
    if categoria_filtro:
        lista = [p for p in lista if p["categoria"] == categoria_filtro]
    if busca:
        lista = [p for p in lista if busca in p["nome"].lower()]

    filtros_html = "".join(
        f'<a href="/produtos?categoria={c["slug"]}" class="btn {"btn-primary" if categoria_filtro == c["slug"] else "btn-outline"}" style="margin:.2rem">{c["icone"]} {c["nome"]}</a>'
        for c in CATEGORIAS
    )

    cards = "".join(f"""
    <div class="card">
      <div style="font-size:1.8rem;margin-bottom:.5rem">{'💻' if p['categoria']=='informatica' else '🎧' if p['categoria']=='audio' else '📱' if p['categoria']=='celulares' else '🔌'}</div>
      <h2 style="font-size:1rem">{p['nome']}</h2>
      <div class="rating" style="margin:.3rem 0">{"★" * int(p['avaliacao'])}{"☆" * (5 - int(p['avaliacao']))} <span class="muted">{p['avaliacao']}</span></div>
      <div class="price">R$ {p['preco']:,.2f}</div>
      <div class="muted">{p['estoque']} em estoque &nbsp;·&nbsp; {p['categoria']}</div>
      <br>
      <a href="/produtos/{p['id']}" class="btn btn-primary" style="width:100%;text-align:center">Ver detalhes</a>
    </div>""" for p in lista)

    corpo = f"""
    <h1>Produtos <span class="muted" style="font-size:1rem">({len(lista)} encontrados)</span></h1>
    <form method="get" style="margin-bottom:1rem">
      <input name="busca" value="{request.args.get('busca','')}" placeholder="Buscar produto..." style="padding:.5rem .8rem;border:1px solid #ddd;border-radius:6px;margin-right:.5rem;width:250px">
      <button type="submit" class="btn btn-primary">Buscar</button>
      {'<a href="/produtos" class="btn btn-outline" style="margin-left:.5rem">Limpar</a>' if busca or categoria_filtro else ''}
    </form>
    <div style="margin-bottom:1.5rem">
      <a href="/produtos" class="btn {"btn-primary" if not categoria_filtro else "btn-outline"}" style="margin:.2rem">Todos</a>
      {filtros_html}
    </div>
    {"<p class='muted'>Nenhum produto encontrado.</p>" if not lista else f'<div class="grid-4">{cards}</div>'}
    """
    return layout("Produtos", corpo, "produtos")


@app.route("/produtos/<int:produto_id>")
def produto_detalhe(produto_id):
    produto = next((p for p in PRODUTOS if p["id"] == produto_id), None)
    if not produto:
        abort(404)
    relacionados = [p for p in PRODUTOS if p["categoria"] == produto["categoria"] and p["id"] != produto_id][:3]
    rel_html = "".join(f"""
    <div class="card">
      <div style="font-size:1.4rem">{'💻' if p['categoria']=='informatica' else '🎧' if p['categoria']=='audio' else '📱' if p['categoria']=='celulares' else '🔌'}</div>
      <h2 style="font-size:.95rem;margin:.5rem 0">{p['nome']}</h2>
      <div class="price" style="font-size:1rem">R$ {p['preco']:,.2f}</div>
      <br><a href="/produtos/{p['id']}" class="btn btn-outline" style="font-size:.8rem">Ver</a>
    </div>""" for p in relacionados)

    corpo = f"""
    <p class="muted"><a href="/produtos">← Voltar para produtos</a></p><br>
    <div class="card" style="display:flex;gap:2rem;flex-wrap:wrap">
      <div style="font-size:5rem">{'💻' if produto['categoria']=='informatica' else '🎧' if produto['categoria']=='audio' else '📱' if produto['categoria']=='celulares' else '🔌'}</div>
      <div style="flex:1">
        <span class="badge badge-blue">{produto['categoria']}</span>
        <h1 style="margin:.5rem 0">{produto['nome']}</h1>
        <div class="rating" style="margin-bottom:.5rem">{"★" * int(produto['avaliacao'])}{"☆" * (5 - int(produto['avaliacao']))} <span class="muted">{produto['avaliacao']} / 5.0</span></div>
        <div class="price" style="font-size:2rem">R$ {produto['preco']:,.2f}</div>
        <div class="muted" style="margin:.5rem 0">
          {'<span class="badge badge-green">Em estoque</span>' if produto['estoque'] > 0 else '<span class="badge badge-red">Esgotado</span>'}
          &nbsp; {produto['estoque']} unidades disponíveis
        </div>
        <br>
        <button class="btn btn-primary" onclick="comprar({produto['id']})">🛒 Adicionar ao carrinho</button>
        &nbsp;
        <a href="/carrinho" class="btn btn-outline">Ver carrinho</a>
        <div id="msg" style="margin-top:1rem"></div>
      </div>
    </div>
    <br>
    {"<h2>Produtos relacionados</h2><div class='grid-3'>" + rel_html + "</div>" if relacionados else ""}
    <script>
    function comprar(id){{
      fetch('/api/comprar', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify({{produto_id: id, quantidade: 1}})}})
        .then(r => r.json()).then(d => {{
          document.getElementById('msg').innerHTML = '<div class="alert alert-info">✅ ' + d.mensagem + '</div>';
        }});
    }}
    </script>
    """
    return layout(produto["nome"], corpo, "produtos")


@app.route("/categorias")
def categorias_html():
    cards = "".join(f"""
    <a href="/produtos?categoria={c['slug']}" style="text-decoration:none">
      <div class="card" style="text-align:center;cursor:pointer;transition:.2s" onmouseover="this.style.transform='translateY(-4px)'" onmouseout="this.style.transform=''">
        <div style="font-size:3rem;margin-bottom:.5rem">{c['icone']}</div>
        <h2>{c['nome']}</h2>
        <p class="muted">{c['descricao']}</p>
        <br>
        <span class="badge badge-blue">{sum(1 for p in PRODUTOS if p['categoria']==c['slug'])} produtos</span>
      </div>
    </a>""" for c in CATEGORIAS)
    corpo = f"""<h1>Categorias</h1><br><div class="grid-4">{cards}</div>"""
    return layout("Categorias", corpo, "categorias")


@app.route("/carrinho")
def carrinho():
    corpo = """
    <h1>🛒 Meu Carrinho</h1><br>
    <div class="alert alert-info">Seu carrinho está vazio. <a href="/produtos">Continuar comprando</a></div>
    <br>
    <div class="card">
      <h2>Resumo do pedido</h2>
      <table style="margin-top:.5rem">
        <tr><td>Subtotal</td><td style="text-align:right">R$ 0,00</td></tr>
        <tr><td>Frete</td><td style="text-align:right">Grátis</td></tr>
        <tr><td><strong>Total</strong></td><td style="text-align:right"><strong>R$ 0,00</strong></td></tr>
      </table>
      <br>
      <button class="btn btn-primary" style="width:100%">Finalizar compra</button>
    </div>
    """
    return layout("Carrinho", corpo)


@app.route("/login")
def login():
    corpo = """
    <div style="max-width:400px;margin:2rem auto">
      <div class="card">
        <h1 style="text-align:center;margin-bottom:1.5rem">Entrar na conta</h1>
        <div class="form-group">
          <label>E-mail</label>
          <input type="email" placeholder="seu@email.com">
        </div>
        <div class="form-group">
          <label>Senha</label>
          <input type="password" placeholder="••••••••">
        </div>
        <button class="btn btn-primary" style="width:100%;padding:.8rem" onclick="fazerLogin()">Entrar</button>
        <p class="muted" style="text-align:center;margin-top:1rem">Não tem conta? <a href="#">Cadastre-se</a></p>
        <div id="msg" style="margin-top:1rem"></div>
      </div>
    </div>
    <script>
    function fazerLogin(){
      fetch('/api/login', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({email:'usuario@email.com', senha:'1234'})})
        .then(r => r.json()).then(d => {
          document.getElementById('msg').innerHTML = '<div class="alert alert-info">' + JSON.stringify(d) + '</div>';
        });
    }
    </script>
    """
    return layout("Login", corpo)


@app.route("/sobre")
def sobre():
    corpo = """
    <h1>Sobre a TechStore</h1><br>
    <div class="grid-3">
      <div class="card">
        <div style="font-size:2.5rem">🚀</div>
        <h2>Nossa missão</h2>
        <p class="muted" style="margin-top:.5rem">Democratizar o acesso à tecnologia com preços justos e atendimento de qualidade.</p>
      </div>
      <div class="card">
        <div style="font-size:2.5rem">🛡️</div>
        <h2>Garantia estendida</h2>
        <p class="muted" style="margin-top:.5rem">Todos os produtos com 12 meses de garantia e suporte técnico especializado.</p>
      </div>
      <div class="card">
        <div style="font-size:2.5rem">🚚</div>
        <h2>Entrega rápida</h2>
        <p class="muted" style="margin-top:.5rem">Entrega em até 2 dias úteis para todo o Brasil com rastreamento em tempo real.</p>
      </div>
    </div>
    <br>
    <div class="card">
      <h2>Stack tecnológico deste projeto</h2><br>
      <table>
        <tr><th>Tecnologia</th><th>Função</th></tr>
        <tr><td><strong>Python 3.11</strong></td><td>Linguagem principal</td></tr>
        <tr><td><strong>Flask</strong></td><td>Framework web / servidor HTTP</td></tr>
        <tr><td><strong>HTML + CSS</strong></td><td>Interface do usuário</td></tr>
        <tr><td><strong>Replit</strong></td><td>Hospedagem e execução na nuvem</td></tr>
      </table>
    </div>
    """
    return layout("Sobre", corpo, "sobre")


@app.route("/contato")
def contato():
    corpo = """
    <h1>Fale conosco</h1><br>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;flex-wrap:wrap">
      <div class="card">
        <h2>Envie uma mensagem</h2><br>
        <div class="form-group"><label>Nome</label><input type="text" placeholder="Seu nome"></div>
        <div class="form-group"><label>E-mail</label><input type="email" placeholder="seu@email.com"></div>
        <div class="form-group"><label>Mensagem</label><textarea rows="4" placeholder="Como podemos ajudar?"></textarea></div>
        <button class="btn btn-primary" onclick="enviarContato()">Enviar mensagem</button>
        <div id="msg" style="margin-top:1rem"></div>
      </div>
      <div>
        <div class="card" style="margin-bottom:1rem">
          <h2>📍 Endereço</h2>
          <p class="muted" style="margin-top:.5rem">Av. Tecnologia, 1024<br>São Paulo — SP, 01310-100</p>
        </div>
        <div class="card" style="margin-bottom:1rem">
          <h2>📞 Telefone</h2>
          <p class="muted" style="margin-top:.5rem">(11) 9999-8888<br>Seg–Sex, 9h às 18h</p>
        </div>
        <div class="card">
          <h2>✉️ E-mail</h2>
          <p class="muted" style="margin-top:.5rem">contato@techstore.com.br</p>
        </div>
      </div>
    </div>
    <script>
    function enviarContato(){
      fetch('/api/contato', {method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({nome:'Visitante', email:'teste@email.com', mensagem:'Olá!'})
      }).then(r=>r.json()).then(d=>{
        document.getElementById('msg').innerHTML = '<div class="alert alert-info">✅ '+d.mensagem+'</div>';
      });
    }
    </script>
    """
    return layout("Contato", corpo, "contato")


@app.route("/blog")
def blog():
    cards = "".join(f"""
    <div class="card">
      <div class="muted">{p['data']} · {p['autor']}</div>
      <h2 style="margin:.5rem 0;font-size:1.1rem">{p['titulo']}</h2>
      <p class="muted">{p['resumo']}</p>
      <br>
      <a href="/blog/{p['slug']}" class="btn btn-outline" style="font-size:.85rem">Ler artigo →</a>
    </div>""" for p in BLOG_POSTS)
    corpo = f"""<h1>Blog</h1><p class="muted">Dicas, análises e novidades do mundo tech.</p><br><div class="grid-3">{cards}</div>"""
    return layout("Blog", corpo, "blog")


@app.route("/blog/<slug>")
def blog_post(slug):
    post = next((p for p in BLOG_POSTS if p["slug"] == slug), None)
    if not post:
        abort(404)
    corpo = f"""
    <p class="muted"><a href="/blog">← Voltar para o Blog</a></p><br>
    <div class="card">
      <div class="muted">{post['data']} · Escrito por <strong>{post['autor']}</strong></div>
      <h1 style="margin:.8rem 0">{post['titulo']}</h1>
      <p style="font-size:1.05rem;line-height:1.7;margin-top:1rem">{post['resumo']} Lorem ipsum dolor sit amet, consectetur adipiscing elit.
      Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,
      quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
      <br>
      <a href="/blog" class="btn btn-outline">← Mais artigos</a>
    </div>
    """
    return layout(post["titulo"], corpo, "blog")


@app.route("/pedidos")
def pedidos():
    status_badge = {
        "entregue":    "badge-green",
        "em_transito": "badge-blue",
        "processando": "badge-red",
    }
    linhas = "".join(f"""
    <tr>
      <td>#{p['id']}</td>
      <td>{next((pr['nome'] for pr in PRODUTOS if pr['id']==p['produto_id']), '—')}</td>
      <td>{p['quantidade']}</td>
      <td>R$ {p['total']:,.2f}</td>
      <td><span class="badge {status_badge.get(p['status'],'badge-blue')}">{p['status'].replace('_',' ')}</span></td>
    </tr>""" for p in PEDIDOS)
    corpo = f"""
    <h1>Pedidos recentes</h1><br>
    <table>
      <tr><th>Nº Pedido</th><th>Produto</th><th>Qtd</th><th>Total</th><th>Status</th></tr>
      {linhas}
    </table>
    """
    return layout("Pedidos", corpo)


# ──────────────────────────────────────────
# API JSON (rotas de ação)
# ──────────────────────────────────────────

@app.route("/api/produtos")
def api_produtos():
    return jsonify({"produtos": PRODUTOS, "total": len(PRODUTOS)})


@app.route("/api/produtos/<int:produto_id>")
def api_produto(produto_id):
    produto = next((p for p in PRODUTOS if p["id"] == produto_id), None)
    if not produto:
        abort(404)
    return jsonify(produto)


@app.route("/api/comprar", methods=["POST"])
def api_comprar():
    dados = request.get_json(silent=True) or {}
    if "produto_id" not in dados:
        return jsonify({"erro": "produto_id é obrigatório"}), 400
    produto = next((p for p in PRODUTOS if p["id"] == dados["produto_id"]), None)
    if not produto:
        return jsonify({"erro": "Produto não encontrado"}), 404
    return jsonify({
        "mensagem": f"'{produto['nome']}' adicionado ao carrinho!",
        "produto_id": dados["produto_id"],
        "quantidade": dados.get("quantidade", 1),
        "total": produto["preco"] * dados.get("quantidade", 1),
    }), 201


@app.route("/api/usuarios/<int:usuario_id>", methods=["GET"])
def api_usuario(usuario_id):
    usuario = USUARIOS.get(usuario_id)
    if not usuario:
        abort(404)
    return jsonify(usuario)


@app.route("/api/usuarios/<int:usuario_id>", methods=["PUT"])
def api_atualizar_usuario(usuario_id):
    dados = request.get_json(silent=True) or {}
    return jsonify({"mensagem": f"Usuário {usuario_id} atualizado", "dados_atualizados": dados})


@app.route("/api/usuarios/<int:usuario_id>", methods=["DELETE"])
def api_deletar_usuario(usuario_id):
    return jsonify({"mensagem": f"Usuário {usuario_id} removido"})


@app.route("/api/login", methods=["POST"])
def api_login():
    dados = request.get_json(silent=True) or {}
    return jsonify({"mensagem": "Login realizado com sucesso!", "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...", "usuario": dados.get("email", "")})


@app.route("/api/contato", methods=["POST"])
def api_contato():
    dados = request.get_json(silent=True) or {}
    return jsonify({"mensagem": "Mensagem enviada! Responderemos em até 24h.", "recebido": dados})


@app.route("/api/pedidos")
def api_pedidos():
    return jsonify({"pedidos": PEDIDOS, "total": len(PEDIDOS)})


# ──────────────────────────────────────────
# Simulação de erros
# ──────────────────────────────────────────

@app.route("/simular/404")
def simular_404():
    abort(404)


@app.route("/simular/500")
def simular_500():
    abort(500)


# ──────────────────────────────────────────
# API do monitor
# ──────────────────────────────────────────

@app.route("/monitor/requisicoes")
def monitor_requisicoes():
    limite = int(request.args.get("limite", 50))
    return jsonify(list(historico)[:limite])


@app.route("/monitor/stats")
def monitor_stats():
    vazio = {
        "total": 0, "por_metodo": {}, "por_status": {}, "erros": 0,
        "tempo": {"min_ms": None, "max_ms": None, "media_ms": None},
        "ranking_rotas": [],
        "rede": {
            "bytes_requisicao_total": 0,
            "bytes_resposta_total": 0,
            "bytes_total": 0,
            "media_bytes_requisicao": None,
            "media_bytes_resposta": None,
            "throughput_bytes_s": 0,
            "top_ips": [],
            "dispositivos": {},
            "navegadores": {},
        },
    }
    if not historico:
        return jsonify(vazio)

    por_metodo, por_status, ranking = {}, {}, {}
    erros, tempos = 0, []
    rotas_ignorar = {"/monitor/requisicoes", "/monitor/stats"}

    bytes_req_total, bytes_resp_total = 0, 0
    ips, dispositivos, navegadores = {}, {}, {}
    timestamps_considerados = []

    for req in historico:
        if req["rota"] in rotas_ignorar:
            continue
        m, s, r = req["metodo"], str(req["status"]), req["rota"]
        por_metodo[m] = por_metodo.get(m, 0) + 1
        por_status[s] = por_status.get(s, 0) + 1
        ranking[r]    = ranking.get(r, 0) + 1
        tempos.append(req["tempo_ms"])
        if req["status"] >= 400:
            erros += 1

        # ── Métricas de rede ──
        bytes_req_total  += req.get("bytes_requisicao", 0)
        bytes_resp_total += req.get("bytes_resposta", 0)

        ip = req.get("ip", "desconhecido")
        ips[ip] = ips.get(ip, 0) + 1

        disp = req.get("dispositivo", "outro")
        dispositivos[disp] = dispositivos.get(disp, 0) + 1

        nav = req.get("navegador", "desconhecido")
        navegadores[nav] = navegadores.get(nav, 0) + 1

        timestamps_considerados.append(req["timestamp"])

    total = sum(por_metodo.values())
    por_metodo_pct = {m: {"total": c, "porcentagem": round(c / total * 100, 1)} for m, c in por_metodo.items()} if total else {}
    ranking_ord = sorted([{"rota": r, "acessos": c} for r, c in ranking.items()], key=lambda x: x["acessos"], reverse=True)

    top_ips = sorted([{"ip": ip, "requisicoes": c} for ip, c in ips.items()], key=lambda x: x["requisicoes"], reverse=True)[:5]

    # Throughput: bytes totais transferidos dividido pela janela de tempo coberta pelo histórico considerado
    throughput = 0
    if len(timestamps_considerados) >= 2:
        try:
            inicio = datetime.fromisoformat(min(timestamps_considerados))
            fim = datetime.fromisoformat(max(timestamps_considerados))
            janela_s = max((fim - inicio).total_seconds(), 0.001)
            throughput = round((bytes_req_total + bytes_resp_total) / janela_s, 1)
        except (ValueError, TypeError):
            throughput = 0

    return jsonify({
        "total": total,
        "por_metodo": por_metodo_pct,
        "por_status": por_status,
        "erros": erros,
        "tempo": {
            "min_ms": min(tempos) if tempos else None,
            "max_ms": max(tempos) if tempos else None,
            "media_ms": round(sum(tempos) / len(tempos), 2) if tempos else None,
        },
        "ranking_rotas": ranking_ord[:10],
        "rede": {
            "bytes_requisicao_total": bytes_req_total,
            "bytes_resposta_total": bytes_resp_total,
            "bytes_total": bytes_req_total + bytes_resp_total,
            "media_bytes_requisicao": round(bytes_req_total / total, 1) if total else None,
            "media_bytes_resposta": round(bytes_resp_total / total, 1) if total else None,
            "throughput_bytes_s": throughput,
            "top_ips": top_ips,
            "dispositivos": dispositivos,
            "navegadores": navegadores,
        },
    })


@app.route("/monitor")
def monitor_dashboard():
    return render_template_string("""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Monitor HTTP — TechStore</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Segoe UI',monospace;background:#0d1117;color:#e6edf3;min-height:100vh}
  header{background:#161b22;border-bottom:1px solid #30363d;padding:.8rem 1.5rem;display:flex;align-items:center;justify-content:space-between}
  .logo{color:#58a6ff;font-weight:700;font-size:1.1rem}
  .status{display:flex;align-items:center;gap:.5rem;font-size:.85rem;color:#8b949e}
  .dot{width:8px;height:8px;border-radius:50%;background:#3fb950;animation:pulse 2s infinite}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
  main{max-width:1200px;margin:1.5rem auto;padding:0 1.5rem}
  .grid-top{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:1rem;margin-bottom:1.5rem}
  .stat-card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1.2rem;text-align:center}
  .stat-num{font-size:2.2rem;font-weight:700;color:#58a6ff}
  .stat-num.green{color:#3fb950}
  .stat-num.red{color:#f85149}
  .stat-num.yellow{color:#d29922}
  .stat-label{font-size:.8rem;color:#8b949e;margin-top:.3rem;text-transform:uppercase;letter-spacing:.05em}
  .grid-mid{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1.5rem}
  .panel{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1.2rem}
  .panel-title{font-size:.85rem;color:#8b949e;text-transform:uppercase;letter-spacing:.1em;margin-bottom:1rem;border-bottom:1px solid #30363d;padding-bottom:.5rem}
  .bar-row{display:flex;align-items:center;gap:.8rem;margin-bottom:.6rem;font-size:.9rem}
  .bar-label{width:80px;text-align:right;color:#e6edf3;font-family:monospace}
  .bar-track{flex:1;background:#21262d;border-radius:3px;height:18px;overflow:hidden}
  .bar-fill{height:100%;border-radius:3px;transition:width .4s ease;display:flex;align-items:center;padding-left:6px;font-size:.75rem;font-weight:600;color:#0d1117}
  .bar-get{background:#58a6ff}
  .bar-post{background:#3fb950}
  .bar-put{background:#d29922}
  .bar-delete{background:#f85149}
  .bar-200{background:#3fb950}
  .bar-201{background:#3fb950}
  .bar-301{background:#d29922}
  .bar-302{background:#d29922}
  .bar-400{background:#f0883e}
  .bar-404{background:#f85149}
  .bar-500{background:#da3633}
  .bar-count{width:60px;color:#8b949e;font-size:.8rem}
  .ranking-item{display:flex;justify-content:space-between;align-items:center;padding:.4rem 0;border-bottom:1px solid #21262d;font-size:.85rem}
  .ranking-item:last-child{border-bottom:none}
  .ranking-rota{color:#58a6ff;font-family:monospace;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .ranking-count{background:#21262d;border-radius:12px;padding:.15rem .6rem;font-size:.75rem;color:#8b949e;margin-left:.5rem;white-space:nowrap}
  .tempo-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:.8rem;margin-top:.5rem}
  .tempo-box{background:#21262d;border-radius:6px;padding:.8rem;text-align:center}
  .tempo-val{font-size:1.3rem;font-weight:700;color:#d29922;font-family:monospace}
  .tempo-lbl{font-size:.75rem;color:#8b949e;margin-top:.2rem}
  .feed-panel{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1.2rem;margin-bottom:1.5rem}
  .feed-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:.8rem}
  .feed-list{max-height:320px;overflow-y:auto;font-family:monospace;font-size:.82rem}
  .feed-list::-webkit-scrollbar{width:4px}
  .feed-list::-webkit-scrollbar-track{background:#21262d}
  .feed-list::-webkit-scrollbar-thumb{background:#30363d;border-radius:2px}
  .feed-row{display:grid;grid-template-columns:140px 60px 70px 60px 110px 1fr;gap:.5rem;padding:.35rem .5rem;border-radius:4px;align-items:center;border-bottom:1px solid #21262d}
  .feed-row:first-child{background:#1f2937;animation:fadeIn .3s ease}
  @keyframes fadeIn{from{background:#2d4a22}to{background:#1f2937}}
  .feed-row:hover{background:#21262d}
  .ts{color:#8b949e}
  .method{font-weight:700;text-align:center;border-radius:3px;padding:.1rem .3rem;font-size:.75rem}
  .m-GET{color:#58a6ff;background:#132032}
  .m-POST{color:#3fb950;background:#122119}
  .m-PUT{color:#d29922;background:#2b2000}
  .m-DELETE{color:#f85149;background:#2d1a1a}
  .status-ok{color:#3fb950}
  .status-redir{color:#d29922}
  .status-err{color:#f85149}
  .path{color:#e6edf3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .ms{color:#8b949e;text-align:right}
  .ip-col{color:#8b949e;font-size:.78rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .feed-header-row{display:grid;grid-template-columns:140px 60px 70px 60px 110px 1fr;gap:.5rem;padding:.2rem .5rem;font-size:.75rem;color:#8b949e;text-transform:uppercase;letter-spacing:.05em;border-bottom:1px solid #30363d;margin-bottom:.3rem}
  .btn-clear{background:#21262d;border:1px solid #30363d;color:#8b949e;padding:.3rem .8rem;border-radius:4px;font-size:.8rem;cursor:pointer}
  .btn-clear:hover{background:#30363d;color:#e6edf3}
  .update-info{font-size:.75rem;color:#8b949e}
  .empty{text-align:center;color:#8b949e;padding:2rem;font-style:italic}
  .ip-item{display:flex;justify-content:space-between;align-items:center;padding:.4rem 0;border-bottom:1px solid #21262d;font-size:.85rem}
  .ip-item:last-child{border-bottom:none}
  .ip-addr{color:#58a6ff;font-family:monospace}
  .ip-count{background:#21262d;border-radius:12px;padding:.15rem .6rem;font-size:.75rem;color:#8b949e}
  @media(max-width:700px){.grid-mid{grid-template-columns:1fr}.feed-row{grid-template-columns:1fr 50px 60px 50px}.feed-header-row{grid-template-columns:1fr 50px 60px 50px}}
</style>
</head>
<body>
<header>
  <div class="logo">📡 Monitor HTTP — TechStore</div>
  <div class="status">
    <div class="dot"></div>
    <span>Atualizando a cada 2s</span>
    &nbsp;·&nbsp;
    <span id="last-update">—</span>
    &nbsp;·&nbsp;
    <a href="/" style="color:#58a6ff;text-decoration:none">← Voltar ao site</a>
  </div>
</header>

<main>
  <!-- Contadores principais -->
  <div class="grid-top">
    <div class="stat-card">
      <div class="stat-num" id="total">0</div>
      <div class="stat-label">Total de Requisições</div>
    </div>
    <div class="stat-card">
      <div class="stat-num green" id="total-ok">0</div>
      <div class="stat-label">Respostas 2xx</div>
    </div>
    <div class="stat-card">
      <div class="stat-num red" id="total-erros">0</div>
      <div class="stat-label">Erros (4xx/5xx)</div>
    </div>
    <div class="stat-card">
      <div class="stat-num yellow" id="pct-erros">0%</div>
      <div class="stat-label">Taxa de Erros</div>
    </div>
    <div class="stat-card">
      <div class="stat-num" id="tempo-media" style="color:#d29922">—</div>
      <div class="stat-label">Tempo Médio (ms)</div>
    </div>
    <div class="stat-card">
      <div class="stat-num" id="bytes-total" style="color:#58a6ff">—</div>
      <div class="stat-label">Tráfego Total</div>
    </div>
    <div class="stat-card">
      <div class="stat-num" id="throughput" style="color:#3fb950">—</div>
      <div class="stat-label">Throughput (B/s)</div>
    </div>
  </div>

  <!-- Gráficos e tempo -->
  <div class="grid-mid">
    <!-- Métodos HTTP -->
    <div class="panel">
      <div class="panel-title">📊 Requisições por Método</div>
      <div id="chart-metodos"><div class="empty">Sem dados ainda</div></div>
    </div>

    <!-- Status HTTP -->
    <div class="panel">
      <div class="panel-title">📊 Requisições por Status</div>
      <div id="chart-status"><div class="empty">Sem dados ainda</div></div>
    </div>
  </div>

  <div class="grid-mid">
    <!-- Tempo de resposta -->
    <div class="panel">
      <div class="panel-title">⏱️ Tempo de Resposta</div>
      <div class="tempo-grid">
        <div class="tempo-box">
          <div class="tempo-val" id="tempo-min">—</div>
          <div class="tempo-lbl">Mínimo (ms)</div>
        </div>
        <div class="tempo-box">
          <div class="tempo-val" id="tempo-med2">—</div>
          <div class="tempo-lbl">Média (ms)</div>
        </div>
        <div class="tempo-box">
          <div class="tempo-val" id="tempo-max">—</div>
          <div class="tempo-lbl">Máximo (ms)</div>
        </div>
      </div>
    </div>

    <!-- Ranking de rotas -->
    <div class="panel">
      <div class="panel-title">🏆 Ranking de Rotas</div>
      <div id="ranking"><div class="empty">Sem dados ainda</div></div>
    </div>
  </div>

  <!-- Métricas de rede -->
  <div class="grid-mid">
    <!-- Top IPs -->
    <div class="panel">
      <div class="panel-title">🌐 Top IPs de Origem</div>
      <div id="top-ips"><div class="empty">Sem dados ainda</div></div>
    </div>

    <!-- Dispositivos / Navegadores -->
    <div class="panel">
      <div class="panel-title">💻 Dispositivos &amp; Navegadores</div>
      <div class="tempo-grid" style="grid-template-columns:1fr;gap:.6rem">
        <div>
          <div class="bar-label" style="width:auto;text-align:left;margin-bottom:.4rem;color:#8b949e;font-size:.75rem;text-transform:uppercase;letter-spacing:.05em">Por dispositivo</div>
          <div id="chart-dispositivos"><div class="empty">Sem dados ainda</div></div>
        </div>
        <div>
          <div class="bar-label" style="width:auto;text-align:left;margin-bottom:.4rem;color:#8b949e;font-size:.75rem;text-transform:uppercase;letter-spacing:.05em">Por navegador</div>
          <div id="chart-navegadores"><div class="empty">Sem dados ainda</div></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Feed de requisições -->
  <div class="feed-panel">
    <div class="feed-header">
      <div class="panel-title" style="margin:0">🔴 Histórico em Tempo Real</div>
      <div style="display:flex;align-items:center;gap:1rem">
        <span class="update-info" id="feed-count">0 requisições</span>
        <button class="btn-clear" onclick="limparHistorico()">Limpar</button>
      </div>
    </div>
    <div class="feed-header-row">
      <span>Horário</span><span>Método</span><span>Status</span><span>Tempo</span><span>IP</span><span>Rota</span>
    </div>
    <div class="feed-list" id="feed">
      <div class="empty">Navegue pelo site para ver requisições aparecerem aqui...</div>
    </div>
  </div>
</main>

<script>
const COR_METODO = {GET:'bar-get', POST:'bar-post', PUT:'bar-put', DELETE:'bar-delete'};
const COR_STATUS = s => s.startsWith('2') ? 'bar-200' : s.startsWith('3') ? 'bar-301' : s === '400' ? 'bar-400' : s === '404' ? 'bar-404' : 'bar-500';
const STATUS_CLS = s => parseInt(s) < 300 ? 'status-ok' : parseInt(s) < 400 ? 'status-redir' : 'status-err';

let ultimaContagem = 0;

function barra(label, count, total, corClass) {
  const pct = total > 0 ? Math.round(count / total * 100) : 0;
  const blocos = Math.round(pct / 5);
  const barraTexto = '█'.repeat(blocos) + '░'.repeat(20 - blocos);
  return `
    <div class="bar-row">
      <div class="bar-label">${label}</div>
      <div class="bar-track">
        <div class="bar-fill ${corClass}" style="width:${pct}%">${pct > 12 ? pct+'%' : ''}</div>
      </div>
      <div class="bar-count">${count} <span style="color:#555">(${pct}%)</span></div>
    </div>`;
}

function ts(iso) {
  const d = new Date(iso);
  return d.toLocaleTimeString('pt-BR', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
}

function formatBytes(valor) {
  if (valor == null) return '—';
  if (valor < 1024) return valor + ' B';
  if (valor < 1024 * 1024) return (valor / 1024).toFixed(1) + ' KB';
  return (valor / (1024 * 1024)).toFixed(2) + ' MB';
}

const ROTULO_DISPOSITIVO = { desktop: '🖥️ Desktop', mobile: '📱 Mobile', outro: '❔ Outro' };

async function atualizarStats() {
  try {
    const r = await fetch('/monitor/stats');
    const s = await r.json();

    document.getElementById('total').textContent = s.total;
    document.getElementById('total-erros').textContent = s.erros;
    document.getElementById('tempo-media').textContent = s.tempo.media_ms != null ? s.tempo.media_ms : '—';
    document.getElementById('tempo-min').textContent  = s.tempo.min_ms  != null ? s.tempo.min_ms  : '—';
    document.getElementById('tempo-med2').textContent = s.tempo.media_ms != null ? s.tempo.media_ms : '—';
    document.getElementById('tempo-max').textContent  = s.tempo.max_ms  != null ? s.tempo.max_ms  : '—';

    const ok = Object.entries(s.por_status).filter(([k])=>k.startsWith('2')).reduce((a,[,v])=>a+v, 0);
    document.getElementById('total-ok').textContent = ok;
    const pct = s.total > 0 ? (s.erros / s.total * 100).toFixed(1) : 0;
    document.getElementById('pct-erros').textContent = pct + '%';

    // Métricas de rede
    const rede = s.rede || {};
    document.getElementById('bytes-total').textContent = formatBytes(rede.bytes_total);
    document.getElementById('throughput').textContent = rede.throughput_bytes_s ? formatBytes(rede.throughput_bytes_s) + '/s' : '—';

    // Top IPs
    if (rede.top_ips && rede.top_ips.length) {
      const maxIp = rede.top_ips[0].requisicoes;
      document.getElementById('top-ips').innerHTML = rede.top_ips.map(item => `
        <div class="ip-item">
          <span class="ip-addr">${item.ip}</span>
          <div style="display:flex;align-items:center;gap:.5rem">
            <div style="width:80px;background:#21262d;border-radius:2px;height:6px">
              <div style="width:${Math.round(item.requisicoes/maxIp*100)}%;background:#3fb950;height:100%;border-radius:2px"></div>
            </div>
            <span class="ip-count">${item.requisicoes}x</span>
          </div>
        </div>`).join('');
    }

    // Dispositivos
    if (rede.dispositivos && Object.keys(rede.dispositivos).length) {
      const totalDisp = Object.values(rede.dispositivos).reduce((a,b)=>a+b,0);
      document.getElementById('chart-dispositivos').innerHTML =
        Object.entries(rede.dispositivos)
          .sort((a,b) => b[1]-a[1])
          .map(([d, c]) => barra(ROTULO_DISPOSITIVO[d] || d, c, totalDisp, 'bar-get'))
          .join('');
    }

    // Navegadores
    if (rede.navegadores && Object.keys(rede.navegadores).length) {
      const totalNav = Object.values(rede.navegadores).reduce((a,b)=>a+b,0);
      document.getElementById('chart-navegadores').innerHTML =
        Object.entries(rede.navegadores)
          .sort((a,b) => b[1]-a[1])
          .map(([n, c]) => barra(n, c, totalNav, 'bar-post'))
          .join('');
    }

    // Gráfico métodos
    if (Object.keys(s.por_metodo).length) {
      const total = s.total;
      document.getElementById('chart-metodos').innerHTML =
        Object.entries(s.por_metodo)
          .sort((a,b) => b[1].total - a[1].total)
          .map(([m, d]) => barra(m, d.total, total, COR_METODO[m] || 'bar-get'))
          .join('');
    }

    // Gráfico status
    if (Object.keys(s.por_status).length) {
      const totalStatus = Object.values(s.por_status).reduce((a,b)=>a+b,0);
      document.getElementById('chart-status').innerHTML =
        Object.entries(s.por_status)
          .sort((a,b) => parseInt(a[0]) - parseInt(b[0]))
          .map(([st, c]) => barra(st, c, totalStatus, COR_STATUS(st)))
          .join('');
    }

    // Ranking de rotas
    if (s.ranking_rotas.length) {
      const max = s.ranking_rotas[0].acessos;
      document.getElementById('ranking').innerHTML = s.ranking_rotas.slice(0, 8).map((r, i) => `
        <div class="ranking-item">
          <span style="color:#8b949e;width:1.2rem;font-size:.8rem">${i+1}</span>
          <span class="ranking-rota">${r.rota}</span>
          <div style="display:flex;align-items:center;gap:.5rem">
            <div style="width:80px;background:#21262d;border-radius:2px;height:6px">
              <div style="width:${Math.round(r.acessos/max*100)}%;background:#58a6ff;height:100%;border-radius:2px"></div>
            </div>
            <span class="ranking-count">${r.acessos}x</span>
          </div>
        </div>`).join('');
    }

    document.getElementById('last-update').textContent = new Date().toLocaleTimeString('pt-BR');
  } catch(e) { console.error(e); }
}

async function atualizarFeed() {
  try {
    const r = await fetch('/monitor/requisicoes?limite=100');
    const lista = await r.json();

    document.getElementById('feed-count').textContent = lista.length + ' requisições';

    if (!lista.length) return;
    if (lista.length === ultimaContagem) return;
    ultimaContagem = lista.length;

    document.getElementById('feed').innerHTML = lista.map(req => {
      const status = req.status;
      const sCls = STATUS_CLS(String(status));
      const mCls = 'm-' + req.metodo;
      return `
        <div class="feed-row">
          <span class="ts">${ts(req.timestamp)}</span>
          <span class="method ${mCls}">${req.metodo}</span>
          <span class="${sCls}" style="font-weight:600">${status}</span>
          <span class="ms">${req.tempo_ms}ms</span>
          <span class="ip-col">${req.ip || '—'}</span>
          <span class="path">${req.rota}</span>
        </div>`;
    }).join('');
  } catch(e) { console.error(e); }
}

function limparHistorico() {
  fetch('/monitor/limpar', {method:'POST'})
    .then(() => { ultimaContagem = 0; atualizarStats(); atualizarFeed(); });
}

// Inicializa e atualiza a cada 2 segundos
atualizarStats();
atualizarFeed();
setInterval(() => { atualizarStats(); atualizarFeed(); }, 2000);
</script>
</body>
</html>""")


@app.route("/monitor/limpar", methods=["POST"])
def monitor_limpar():
    historico.clear()
    return jsonify({"mensagem": "Histórico limpo"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
