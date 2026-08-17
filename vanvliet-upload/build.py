#!/usr/bin/env python3
"""
build.py  —  Van Vliet OE surplus catalogue: bilingual (EN + pt-BR) SEO builder
==============================================================================

One command turns the English-only catalogue into a fully bilingual, search-
optimised site. Run from the repo root:

    python3 build.py

English catalogue pages under /catalog-en/ are the SINGLE SOURCE OF TRUTH.
This script derives everything else from them, so re-run it whenever the
inventory changes — nothing goes stale, and re-runs never duplicate.

What it produces
----------------
1. /catalog-pt/  — a Brazilian-Portuguese mirror of every catalogue page.
     * All interface text, buttons, the order form, the WhatsApp/email message
       templates and the spreadsheet export are translated to pt-BR.
     * Part categories and the common part-name vocabulary are translated;
       unusual technical descriptions fall back to English (the OE part number
       is the universal search key either way). Prices show in EUR with
       Brazilian number formatting.
     * The interactive order tool is preserved exactly.
2. SEO on BOTH languages — unique meta description, canonical, Open Graph, and
   JSON-LD (AutoPartsStore + breadcrumbs + collection), plus a real crawlable
   stock list exposing every OE number as indexable text (it was hidden in JS).
3. hreflang alternates linking each EN page to its pt-BR twin (and back), with
   x-default, so Google serves the right language per region.
4. /sitemap.xml and /robots.txt covering both language trees.

Idempotent: injected blocks use sentinel comments and are replaced in place.
No cloaking — the crawlable text is the same content shown to users.
"""

import re
import json
import html
import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SITE = "https://oetrucksurplus.parts"
REPO = Path(__file__).resolve().parent
TODAY = datetime.date.today().isoformat()

EN_DIR = REPO / "catalog-en"
PT_DIR = REPO / "catalog-pt"

BRANDS = {
    "vw":       "VW Truck & Bus",
    "man":      "MAN",
    "mercedes": "Mercedes-Benz",
    "iveco":    "Iveco / Fiat",
    "toyota":   "Toyota",
}

ORG_TELEPHONE = "+31614283465"
ORG_LEGAL_NAME = "Van Vliet Automotive B.V."
ORG_LOCALITY = "Nieuwerkerk aan den IJssel"
ORG_COUNTRY = "NL"

ITEMS_RE = re.compile(r"const ITEMS\s*=\s*(\[.*?\]);", re.S)

# Sentinels
HEAD_START, HEAD_END = "<!--SEO-HEAD-START-->", "<!--SEO-HEAD-END-->"
LIST_START, LIST_END = "<!--SEO-STOCKLIST-START-->", "<!--SEO-STOCKLIST-END-->"
HREF_START, HREF_END = "<!--HREFLANG-START-->", "<!--HREFLANG-END-->"

# ===========================================================================
# TRANSLATION TABLES (pt-BR)
# ===========================================================================

# Category names (used in the dropdown, item data, SEO headings).
CAT_PT = {
    "Body & Cab": "Carroceria e Cabine",
    "Brakes": "Freios",
    "Cooling": "Arrefecimento",
    "Electrical": "Elétrica",
    "Engine": "Motor",
    "Fasteners & Hardware": "Fixadores e Ferragens",
    "Filters": "Filtros",
    "Fuel System": "Sistema de Combustível",
    "Hoses, Pipes & Tubes": "Mangueiras e Tubos",
    "Hydraulics": "Hidráulica",
    "Lighting": "Iluminação",
    "Other": "Outros",
    "Suspension & Steering": "Suspensão e Direção",
    "Transmission & Clutch": "Transmissão e Embreagem",
    "Wipers": "Limpadores",
}

# Common part-name vocabulary. Applied as longest-match-first, word-bounded
# replacements over each description. Anything not covered stays in English.
TERM_PT = {
    "Engine oil filter element": "Elemento filtrante de óleo do motor",
    "Air filter element": "Elemento filtrante de ar",
    "Fuel filter insert": "Elemento filtrante de combustível",
    "Filter element": "Elemento filtrante",
    "Urea filter element": "Elemento filtrante de ureia",
    "Cab filter": "Filtro de cabine",
    "Pollen filter": "Filtro de pólen",
    "Air dryer cartridge": "Cartucho do secador de ar",
    "Belt tensioner kit": "Kit tensor de correia",
    "Belt tensioner": "Tensor de correia",
    "Tension pulley": "Polia tensora",
    "Ribbed v-belt": "Correia poli-V",
    "Narrow v-belt": "Correia em V estreita",
    "Radial shaft seal": "Retentor radial",
    "Radial seal": "Retentor radial",
    "Single-lead seal": "Vedação simples",
    "Sealing washer": "Arruela de vedação",
    "Seal": "Retentor",
    "Gasket": "Junta",
    "Flat gasket": "Junta plana",
    "O-ring": "Anel O-ring",
    "Cable harness": "Chicote elétrico",
    "Electronic control unit": "Unidade de controle eletrônico",
    "Engine control unit": "Unidade de controle do motor",
    "Control switch": "Interruptor de comando",
    "Toggle switch": "Interruptor de alavanca",
    "Pressure switch": "Pressostato",
    "Pressure sensor": "Sensor de pressão",
    "Pressure sender": "Sensor de pressão",
    "Temperature sender": "Sensor de temperatura",
    "Speed sender": "Sensor de velocidade",
    "Oil pressure sender": "Sensor de pressão de óleo",
    "Solenoid valve": "Válvula solenoide",
    "Check valve": "Válvula de retenção",
    "Relay": "Relé",
    "Flasher": "Pisca-alerta",
    "Bulb": "Lâmpada",
    "Fuse": "Fusível",
    "Fuse holder": "Porta-fusível",
    "Battery": "Bateria",
    "Wheel mounting bolt": "Parafuso de roda",
    "Hexagon screw": "Parafuso sextavado",
    "Hex lock screw": "Parafuso de trava sextavado",
    "Cylinder screw": "Parafuso cilíndrico",
    "Pan-head screw": "Parafuso de cabeça panela",
    "Countersunk screw": "Parafuso escareado",
    "Screw": "Parafuso",
    "Hex lock nut": "Porca de trava sextavada",
    "Hexagon nut": "Porca sextavada",
    "Hex collar nut": "Porca sextavada com flange",
    "Hex collar bolt": "Parafuso sextavado com flange",
    "Hex flange bolt": "Parafuso flangeado sextavado",
    "Hex shoulder stud": "Prisioneiro sextavado",
    "Nut": "Porca",
    "Bolt": "Parafuso",
    "Washer": "Arruela",
    "Circlip": "Anel de trava",
    "Split pin": "Contrapino",
    "Dowel pin": "Pino guia",
    "Spring washer": "Arruela de pressão",
    "Rivet": "Rebite",
    "Bracket": "Suporte",
    "Mount bracket": "Suporte de fixação",
    "Angle bracket": "Cantoneira",
    "Spacer": "Espaçador",
    "Bush": "Bucha",
    "Slotted bush": "Bucha ranhurada",
    "Shim": "Calço",
    "Cover": "Tampa",
    "Cap": "Tampa",
    "Protective cap": "Tampa protetora",
    "Plug": "Bujão",
    "Drain plug": "Bujão de dreno",
    "Housing": "Carcaça",
    "Cooling water hose": "Mangueira de água de arrefecimento",
    "Refrigerant hose": "Mangueira de refrigerante",
    "Refrigerant pipe": "Tubo de refrigerante",
    "Charge air hose": "Mangueira de ar de admissão",
    "Fuel hose": "Mangueira de combustível",
    "Fuel line": "Linha de combustível",
    "Hose pipe": "Tubo de mangueira",
    "Hose": "Mangueira",
    "Hollow screw": "Parafuso banjo",
    "Turbocharger": "Turbocompressor",
    "Camshaft": "Eixo de comando de válvulas",
    "Crankcase": "Cárter",
    "Flywheel": "Volante do motor",
    "Thermostat": "Termostato",
    "Radiator": "Radiador",
    "Water fuel filter": "Filtro separador de água",
    "Fuel tank": "Tanque de combustível",
    "Brake drum": "Tambor de freio",
    "Brake shoe": "Sapata de freio",
    "Brake cylinder": "Cilindro de freio",
    "Set of drum brake linings": "Jogo de lonas de freio",
    "Slack adjuster": "Catraca de freio",
    "Spring brake cylinder": "Cilindro de freio de mola",
    "Clutch booster": "Servo de embreagem",
    "Release bearing": "Rolamento de embreagem",
    "Power take-off": "Tomada de força",
    "Propeller shaft": "Eixo cardã",
    "Taper roller bearing": "Rolamento de rolos cônicos",
    "Ball joint": "Junta esférica",
    "Outside mirror": "Espelho externo",
    "Mirror bracket": "Suporte do espelho",
    "Wiper linkage": "Mecanismo do limpador",
    "Wiper blade": "Palheta do limpador",
    "Windscreen washer pump": "Bomba do lavador de para-brisa",
    "Parabolic spring": "Feixe de mola parabólica",
    "Pressure spring": "Mola de pressão",
    "Gas spring": "Amortecedor a gás",
    "Air spring system": "Sistema de suspensão a ar",
    "Air-suspension bellows": "Fole de suspensão a ar",
    "Bellows": "Fole",
    "Lens": "Lente",
    "Adapter": "Adaptador",
    "Support": "Suporte",
    "Cross member": "Travessa",
    "Grille": "Grade",
    "Packing": "Vedação",
    "Ring": "Anel",
    "Roller": "Rolete",
    "Valve": "Válvula",
    "Sender": "Sensor",
    "Switch": "Interruptor",
    "Reflector": "Refletor",
}
# Longest phrases first so multi-word terms win.
TERM_ITEMS = sorted(TERM_PT.items(), key=lambda kv: -len(kv[0]))
TERM_PATTERNS = [(re.compile(r"\b" + re.escape(en) + r"\b", re.I), pt)
                 for en, pt in TERM_ITEMS]


def translate_desc(desc: str) -> str:
    out = desc
    for pat, pt in TERM_PATTERNS:
        out = pat.sub(pt, out)
    return out


# HTML interface strings (exact substring replacements on the page body).
HTML_PT = {
    "Genuine MAN Parts &bull; OE surplus stock":
        "Peças genuínas MAN &bull; Estoque excedente OE",
    "Search by part number or description&hellip;":
        "Busque por número de peça ou descrição&hellip;",
    'placeholder="Search by part number or description…"':
        'placeholder="Busque por número de peça ou descrição…"',
    ">Category<": ">Categoria<",
    "We ship from the <span class=\"hl\">Netherlands</span> &mdash; and still aim to come in <span class=\"hl\">BELOW</span> your local purchase price":
        "Enviamos da <span class=\"hl\">Holanda</span> &mdash; e ainda assim buscamos ficar <span class=\"hl\">ABAIXO</span> do seu preço de compra local",
    "Compare us with your local suppliers: our goal is that, <b>even with freight included</b>, the final price still works out cheaper. Send us your request and we'll agree the best price by volume.":
        "Compare com seus fornecedores locais: nosso objetivo é que, <b>mesmo com o frete incluído</b>, o preço final ainda seja mais barato. Envie sua solicitação e definimos o melhor preço por volume.",
    "<b>Reference prices</b> in EUR, ex-works (Netherlands). An order here is a <b>quotation request</b> — we confirm the final price by lot/volume and come back to you with freight and lead time. Your order is kept as you move between brand catalogues.":
        "<b>Preços de referência</b> em EUR, ex-works (Holanda). Um pedido aqui é uma <b>solicitação de cotação</b> — confirmamos o preço final por lote/volume e retornamos com frete e prazo de entrega. Seu pedido é mantido ao navegar entre os catálogos de marcas.",
    "Questions or ready to order? Contact Duko Steevensz &bull; Van Vliet Automotive":
        "Dúvidas ou pronto para pedir? Fale com Duko Steevensz &bull; Van Vliet Automotive",
    ">View order<": ">Ver pedido<",
    ">Your order<": ">Seu pedido<",
    ">Clear order<": ">Limpar pedido<",
    "Subtotal (ref.)": "Subtotal (ref.)",
    ">Continue<": ">Continuar<",
    ">Send request<": ">Enviar solicitação<",
    "Company <span class=\"req\">*</span>": "Empresa <span class=\"req\">*</span>",
    "Your name <span class=\"req\">*</span>": "Seu nome <span class=\"req\">*</span>",
    "WhatsApp or email <span class=\"req\">*</span>": "WhatsApp ou e-mail <span class=\"req\">*</span>",
    ">Notes<": ">Observações<",
    'placeholder="Lead time, destination, container quantity…"':
        'placeholder="Prazo, destino, quantidade de contêineres…"',
    "Download spreadsheet (.xlsx)": "Baixar planilha (.xlsx)",
    "Send by email": "Enviar por e-mail",
    "Send via WhatsApp": "Enviar via WhatsApp",
    "Your order can include parts from more than one brand. Download the spreadsheet (.xlsx), then tap <b>Send by email</b> or <b>Send via WhatsApp</b> to send us the summary — remember to attach the downloaded spreadsheet before sending.":
        "Seu pedido pode incluir peças de mais de uma marca. Baixe a planilha (.xlsx) e toque em <b>Enviar por e-mail</b> ou <b>Enviar via WhatsApp</b> para nos enviar o resumo — lembre-se de anexar a planilha baixada antes de enviar.",
    ">0 items<": ">0 itens<",
    "&euro; 0.00": "&euro; 0,00",
}

# JavaScript string replacements (exact).
JS_PT = {
    "'en-GB'": "'pt-BR'",
    '"en-GB"': '"pt-BR"',
    "(list.length===1?\" item\":\" items\")": "(list.length===1?\" item\":\" itens\")",
    "n+(n===1?\" item\":\" items\")": "n+(n===1?\" item\":\" itens\")",
    ">No parts found.<": ">Nenhuma peça encontrada.<",
    "In stock: <b>": "Em estoque: <b>",
    ">/ ea.<": ">/ un.<",
    "'&#10003; In order ('+e0.q+')'": "'&#10003; No pedido ('+e0.q+')'",
    "'Add'": "'Adicionar'",
    ">Your order is empty.<": ">Seu pedido está vazio.<",
    ">Remove<": ">Remover<",
    'confirm("Remove all items from your order?")':
        'confirm("Remover todos os itens do seu pedido?")',
    # spreadsheet
    '"Order"': '"Pedido"',
    "Quotation Request \\u2014 Genuine OE Surplus Parts":
        "Solicitação de Cotação \\u2014 Peças Genuínas OE Excedentes",
    '"Company:"': '"Empresa:"',
    '"Date:"': '"Data:"',
    '"Name:"': '"Nome:"',
    '"Contact:"': '"Contato:"',
    '"Part Number"': '"Número da peça"',
    '"Brand"': '"Marca"',
    '"Description"': '"Descrição"',
    '"Category"': '"Categoria"',
    '"Qty requested"': '"Qtd. solicitada"',
    '"Unit price (EUR)"': '"Preço unit. (EUR)"',
    '"Line total (EUR)"': '"Total da linha (EUR)"',
    '"TOTAL"': '"TOTAL"',
    '"Notes:"': '"Observações:"',
    "Reference prices ex-works (NL). Final price by lot/volume, on request. Freight and lead time quoted separately.":
        "Preços de referência ex-works (NL). Preço final por lote/volume, sob consulta. Frete e prazo de entrega cotados à parte.",
    "VanVliet_Order_": "VanVliet_Pedido_",
    # whatsapp + email templates
    "*Quotation request \\u2014 Van Vliet*": "*Solicitação de cotação \\u2014 Van Vliet*",
    "Company: ${$(\"#fEmp\").value.trim()}\\nName: ${$(\"#fNome\").value.trim()}\\nContact: ${$(\"#fCont\").value.trim()}":
        "Empresa: ${$(\"#fEmp\").value.trim()}\\nNome: ${$(\"#fNome\").value.trim()}\\nContato: ${$(\"#fCont\").value.trim()}",
    "\\u2014 Qty: ${e.q}": "\\u2014 Qtd: ${e.q}",
    "\\nSubtotal (ref.): ${eur(total)}": "\\nSubtotal (ref.): ${eur(total)}",
    "\\nNotes: ${obs}": "\\nObservações: ${obs}",
    "(spreadsheet attached)": "(planilha em anexo)",
    "Quotation request \\u2014 Van Vliet\\n\\n": "Solicitação de cotação \\u2014 Van Vliet\\n\\n",
    "Company: ${company}\\nName: ${$(\"#fNome\").value.trim()}\\nContact: ${$(\"#fCont\").value.trim()}":
        "Empresa: ${company}\\nNome: ${$(\"#fNome\").value.trim()}\\nContato: ${$(\"#fCont\").value.trim()}",
    "Please attach the downloaded spreadsheet (.xlsx) before sending.":
        "Anexe a planilha (.xlsx) baixada antes de enviar.",
    "Quotation request \\u2014 ${company||\"Van Vliet parts\"}":
        "Solicitação de cotação \\u2014 ${company||\"Peças Van Vliet\"}",
    "The category dropdown \"All\"": "",  # placeholder, handled below
    "[\"All\",...CATS]": "[\"Todas\",...CATS]",
    "if(activeCat!==\"All\"": "if(activeCat!==\"Todas\"",
    "let activeCat = \"All\"": "let activeCat = \"Todas\"",
}


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def parse_items(page_html):
    m = ITEMS_RE.search(page_html)
    return json.loads(m.group(1)) if m else None


def strip_all_sentinels(h):
    for a, b in [(HEAD_START, HEAD_END), (LIST_START, LIST_END), (HREF_START, HREF_END)]:
        h = re.sub(re.escape(a) + r".*?" + re.escape(b) + r"\s*", "", h, flags=re.S)
    return h


# ===========================================================================
# PT PAGE GENERATION
# ===========================================================================
def make_pt_page(en_html, slug):
    h = strip_all_sentinels(en_html)

    # lang attribute
    h = h.replace('<html lang="en">', '<html lang="pt-BR">', 1)
    # title
    h = h.replace("Van Vliet Automotive — MAN Parts Catalogue",
                  f"Van Vliet Automotive — Catálogo de Peças {BRANDS[slug]}")
    h = re.sub(r"<title>.*?</title>",
               f"<title>Van Vliet Automotive — Catálogo de Peças {esc(BRANDS[slug])}</title>",
               h, count=1, flags=re.S)

    # Translate the ITEMS array (category + description).
    m = ITEMS_RE.search(h)
    items = json.loads(m.group(1))
    for it in items:
        it["c"] = CAT_PT.get(it.get("c", "Other"), it.get("c", "Other"))
        it["d"] = translate_desc(it.get("d", ""))
    new_items = "const ITEMS = " + json.dumps(items, ensure_ascii=False) + ";"
    h = h[:m.start()] + new_items + h[m.end():]

    # HTML interface strings
    for en, pt in HTML_PT.items():
        h = h.replace(en, pt)
    # JS strings
    for en, pt in JS_PT.items():
        if en and pt is not None:
            h = h.replace(en, pt)

    return h


# ===========================================================================
# SEO HEAD + STOCKLIST + HREFLANG  (language-aware)
# ===========================================================================
STOCKLIST_CSS = """
<style>
.seo-stocklist{max-width:1080px;margin:26px auto 0;padding:0 16px 8px}
.seo-stocklist h2{font-size:15px;font-weight:800;color:var(--navy);letter-spacing:.2px}
.seo-stocklist .lead{font-size:12.5px;color:var(--muted);line-height:1.5;margin:6px 0 14px;max-width:70ch}
.seo-stocklist details{background:var(--card);border:1px solid var(--line);border-radius:11px;margin-bottom:9px;overflow:hidden}
.seo-stocklist summary{cursor:pointer;list-style:none;padding:12px 14px;font-size:13.5px;font-weight:700;color:var(--navy);display:flex;justify-content:space-between;align-items:center;gap:10px}
.seo-stocklist summary::-webkit-details-marker{display:none}
.seo-stocklist summary .cnt{font-size:11.5px;font-weight:700;color:var(--muted);background:var(--bg);border-radius:20px;padding:2px 9px;flex:none}
.seo-stocklist ul{list-style:none;margin:0;padding:2px 14px 12px;border-top:1px solid var(--line)}
.seo-stocklist li{padding:6px 0;border-bottom:1px solid var(--line);font-size:12.5px;line-height:1.4}
.seo-stocklist li:last-child{border-bottom:none}
.seo-stocklist li .pn{font-family:var(--mono);font-weight:700;color:var(--navy)}
.seo-stocklist li .d{color:var(--ink)}
</style>
"""

COPY = {
    "en": {
        "title": lambda d, n: f"{d} OE surplus parts — {n} genuine line items | Van Vliet Automotive",
        "desc": lambda d, n, c: (f"{n} genuine {d} OE surplus parts in stock — {c} and more. "
                                 f"Reference prices in EUR, ships worldwide from the Netherlands. "
                                 f"Search by OE part number and request a quotation."),
        "h2": lambda d, n: f"Full {d} OE parts stock list — {n} line items",
        "lead": lambda d: (f"Every genuine {d} OE surplus part below is in stock at Van Vliet "
                           f"Automotive and shipped worldwide from the Netherlands, with reference "
                           f"prices in EUR. Search this page by OE part number or use the request "
                           f"tool above to build a quotation. Grouped by category:"),
        "crumb": "Catalogues",
    },
    "pt": {
        "title": lambda d, n: f"Peças excedentes OE {d} — {n} itens genuínos | Van Vliet Automotive",
        "desc": lambda d, n, c: (f"{n} peças genuínas {d} OE excedentes em estoque — {c} e mais. "
                                 f"Preços de referência em EUR, enviamos para todo o mundo a partir da Holanda. "
                                 f"Busque pelo número de peça OE e solicite uma cotação."),
        "h2": lambda d, n: f"Lista completa de peças OE {d} — {n} itens",
        "lead": lambda d: (f"Todas as peças genuínas {d} OE excedentes abaixo estão em estoque na Van Vliet "
                           f"Automotive e são enviadas para todo o mundo a partir da Holanda, com preços de "
                           f"referência em EUR. Busque nesta página pelo número de peça OE ou use a ferramenta "
                           f"de solicitação acima para montar uma cotação. Agrupadas por categoria:"),
        "crumb": "Catálogos",
    },
}


def cat_counts(items):
    c = {}
    for it in items:
        c[it["c"]] = c.get(it["c"], 0) + 1
    return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def build_head_block(lang, slug, display, items, url):
    n = len(items)
    cats = cat_counts(items)
    top = ", ".join(list(cats.keys())[:3]).lower()
    T = COPY[lang]
    title = T["title"](display, n)
    desc = T["desc"](display, n, top)[:300]

    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "AutoPartsStore", "@id": f"{SITE}/#business",
             "name": "Van Vliet Automotive", "legalName": ORG_LEGAL_NAME,
             "url": SITE + "/", "telephone": ORG_TELEPHONE,
             "address": {"@type": "PostalAddress", "addressLocality": ORG_LOCALITY,
                         "addressCountry": ORG_COUNTRY},
             "areaServed": "Worldwide"},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": T["crumb"],
                 "item": f"{SITE}/catalog-{lang}/"},
                {"@type": "ListItem", "position": 2, "name": f"{display}", "item": url},
            ]},
            {"@type": "CollectionPage", "@id": url + "#collection", "url": url,
             "name": title, "description": desc,
             "isPartOf": {"@id": f"{SITE}/#business"},
             "inLanguage": "pt-BR" if lang == "pt" else "en",
             "mainEntity": {"@type": "ItemList", "numberOfItems": n,
                            "itemListElement": [
                                {"@type": "ListItem", "position": i + 1,
                                 "name": f"{display} {cat} ({cnt})"}
                                for i, (cat, cnt) in enumerate(cats.items())]}},
        ],
    }
    ld_json = json.dumps(ld, ensure_ascii=False, separators=(",", ":"))
    return "\n".join([
        HEAD_START,
        f'<meta name="description" content="{esc(desc)}">',
        '<meta name="robots" content="index,follow,max-image-preview:large">',
        f'<link rel="canonical" href="{url}">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Van Vliet Automotive">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(desc)}">',
        f'<meta property="og:url" content="{url}">',
        '<meta name="twitter:card" content="summary">',
        f'<script type="application/ld+json">{ld_json}</script>',
        HEAD_END,
    ]) + "\n"


def build_hreflang_block(slug):
    en_url = f"{SITE}/catalog-en/{slug}/"
    pt_url = f"{SITE}/catalog-pt/{slug}/"
    return "\n".join([
        HREF_START,
        f'<link rel="alternate" hreflang="en" href="{en_url}">',
        f'<link rel="alternate" hreflang="pt-BR" href="{pt_url}">',
        f'<link rel="alternate" hreflang="x-default" href="{en_url}">',
        HREF_END,
    ]) + "\n"


def build_stocklist_block(lang, display, items):
    n = len(items)
    T = COPY[lang]
    groups = {}
    for it in items:
        groups.setdefault(it["c"], []).append(it)
    groups = dict(sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])))

    parts = [LIST_START, STOCKLIST_CSS,
             '<section class="seo-stocklist" aria-label="stock list">',
             f'<h2>{esc(T["h2"](display, n))}</h2>',
             f'<p class="lead">{esc(T["lead"](display))}</p>']
    for cat, its in groups.items():
        its = sorted(its, key=lambda it: str(it.get("pn", "")))
        parts.append("<details>")
        parts.append(f'<summary>{esc(display)} — {esc(cat)}<span class="cnt">{len(its)}</span></summary>')
        parts.append("<ul>")
        for it in its:
            parts.append(f'<li><span class="pn">{esc(it.get("pn",""))}</span> — '
                         f'<span class="d">{esc(it.get("d",""))}</span></li>')
        parts.append("</ul></details>")
    parts.append("</section>")
    parts.append(LIST_END)
    return "\n".join(parts) + "\n"


def inject(page_html, lang, slug, display):
    h = strip_all_sentinels(page_html)
    items = parse_items(h)
    url = f"{SITE}/catalog-{lang}/{slug}/"
    head = build_head_block(lang, slug, display, items, url)
    href = build_hreflang_block(slug)
    lst = build_stocklist_block(lang, display, items)
    h = h.replace("</head>", head + href + "</head>", 1)
    h = h.replace("</body>", lst + "</body>", 1)
    return h, len(items)


# ===========================================================================
# HUBS
# ===========================================================================
def build_hub(lang, en_hub_html, brand_infos):
    url = f"{SITE}/catalog-{lang}/"
    h = strip_all_sentinels(en_hub_html)

    if lang == "pt":
        h = h.replace('<html lang="en">', '<html lang="pt-BR">', 1)
        h = re.sub(r"<title>.*?</title>",
                   "<title>Van Vliet Automotive — Catálogos de Peças</title>", h, 1, re.S)
        h = h.replace("Genuine OE surplus parts &bull; Prices in EUR, ex-works (Netherlands)",
                      "Peças genuínas OE excedentes &bull; Preços em EUR, ex-works (Holanda)")
        h = h.replace(
            "Choose a brand catalogue below. Each is a live request tool — browse by category, add quantities, and send us a quotation request by WhatsApp or as a spreadsheet.",
            "Escolha um catálogo de marca abaixo. Cada um é uma ferramenta de solicitação — navegue por categoria, adicione quantidades e envie uma solicitação de cotação por WhatsApp ou como planilha.")
        h = h.replace("Open catalogue", "Abrir catálogo")
        h = h.replace("line items", "itens")
        h = h.replace(
            "<b>Reference prices</b> in EUR, ex-works (Netherlands). An order is a <b>quotation request</b> — final price is agreed by lot/volume, with freight and lead time quoted separately.",
            "<b>Preços de referência</b> em EUR, ex-works (Holanda). Um pedido é uma <b>solicitação de cotação</b> — o preço final é acordado por lote/volume, com frete e prazo cotados à parte.")
        # point the brand links at the PT tree
        h = re.sub(r'/catalog-en/(vw|man|mercedes|iveco|toyota)/',
                   r'/catalog-pt/\1/', h)

    total = sum(b["n"] for b in brand_infos)
    brand_names = ", ".join(b["display"] for b in brand_infos)
    if lang == "pt":
        desc = (f"{total} peças genuínas OE excedentes de caminhão em estoque nas marcas {brand_names}. "
                f"Preços de referência em EUR, enviamos para todo o mundo a partir da Holanda. "
                f"Navegue por marca e solicite uma cotação pelo número de peça.")[:300]
        title = "Peças OE excedentes de caminhão — MAN, VW, Iveco, Mercedes, Toyota | Van Vliet Automotive"
    else:
        desc = (f"{total} genuine OE surplus truck parts in stock across {brand_names}. "
                f"Reference prices in EUR, ships worldwide from the Netherlands. "
                f"Browse by brand and request a quotation by part number.")[:300]
        title = "Genuine OE truck parts surplus — MAN, VW, Iveco, Mercedes, Toyota | Van Vliet Automotive"

    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "AutoPartsStore", "@id": f"{SITE}/#business",
             "name": "Van Vliet Automotive", "legalName": ORG_LEGAL_NAME, "url": SITE + "/",
             "telephone": ORG_TELEPHONE,
             "address": {"@type": "PostalAddress", "addressLocality": ORG_LOCALITY,
                         "addressCountry": ORG_COUNTRY}, "areaServed": "Worldwide"},
            {"@type": "WebSite", "@id": f"{SITE}/#website", "url": SITE + "/",
             "name": "Van Vliet Automotive — OE surplus parts",
             "publisher": {"@id": f"{SITE}/#business"}},
            {"@type": "CollectionPage", "url": url, "name": title, "description": desc,
             "inLanguage": "pt-BR" if lang == "pt" else "en",
             "isPartOf": {"@id": f"{SITE}/#website"},
             "mainEntity": {"@type": "ItemList", "numberOfItems": len(brand_infos),
                            "itemListElement": [
                                {"@type": "ListItem", "position": i + 1,
                                 "name": f"{b['display']}", "url": b["url"]}
                                for i, b in enumerate(brand_infos)]}},
        ],
    }
    ld_json = json.dumps(ld, ensure_ascii=False, separators=(",", ":"))
    head = "\n".join([
        HEAD_START,
        f'<meta name="description" content="{esc(desc)}">',
        '<meta name="robots" content="index,follow,max-image-preview:large">',
        f'<link rel="canonical" href="{url}">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Van Vliet Automotive">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(desc)}">',
        f'<meta property="og:url" content="{url}">',
        '<meta name="twitter:card" content="summary">',
        f'<script type="application/ld+json">{ld_json}</script>',
        HEAD_END,
    ]) + "\n"
    href = "\n".join([
        HREF_START,
        f'<link rel="alternate" hreflang="en" href="{SITE}/catalog-en/">',
        f'<link rel="alternate" hreflang="pt-BR" href="{SITE}/catalog-pt/">',
        f'<link rel="alternate" hreflang="x-default" href="{SITE}/catalog-en/">',
        HREF_END,
    ]) + "\n"
    h = h.replace("</head>", head + href + "</head>", 1)
    return h


# ===========================================================================
# SITEMAP + ROBOTS
# ===========================================================================
def write_sitemap(brand_slugs):
    urls = [f"{SITE}/", f"{SITE}/catalog-en/", f"{SITE}/catalog-pt/"]
    for s in brand_slugs:
        urls.append(f"{SITE}/catalog-en/{s}/")
        urls.append(f"{SITE}/catalog-pt/{s}/")
    rows = []
    for u in urls:
        prio = "1.0" if u.endswith("/catalog-en/") else "0.8"
        rows.append(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod>"
                    f"<changefreq>weekly</changefreq><priority>{prio}</priority></url>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(rows) + "\n</urlset>\n")
    (REPO / "sitemap.xml").write_text(xml, encoding="utf-8")
    print(f"  \u2713 sitemap.xml  ({len(urls)} urls)")


def write_robots():
    (REPO / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    print("  \u2713 robots.txt")


# ===========================================================================
# MAIN
# ===========================================================================
def main():
    print("Bilingual SEO build — Van Vliet OE surplus catalogue")
    print("-" * 56)
    PT_DIR.mkdir(exist_ok=True)

    brand_infos = []
    for slug, display in BRANDS.items():
        en_path = EN_DIR / slug / "index.html"
        en_src = en_path.read_text(encoding="utf-8")

        # 1) generate PT page from EN source
        pt_html = make_pt_page(en_src, slug)
        (PT_DIR / slug).mkdir(exist_ok=True)
        pt_path = PT_DIR / slug / "index.html"

        # 2) inject SEO + hreflang into both
        en_out, n = inject(en_src, "en", slug, display)
        pt_out, _ = inject(pt_html, "pt", slug, display)
        en_path.write_text(en_out, encoding="utf-8")
        pt_path.write_text(pt_out, encoding="utf-8")

        brand_infos.append({"slug": slug, "display": display, "n": n,
                            "url": f"{SITE}/catalog-en/{slug}/"})
        print(f"  \u2713 {slug:9s} {n:4d} items  ->  EN + pt-BR, SEO + hreflang")

    # hubs
    en_hub_src = (EN_DIR / "index.html").read_text(encoding="utf-8")
    (EN_DIR / "index.html").write_text(build_hub("en", en_hub_src, brand_infos), encoding="utf-8")
    pt_infos = [{**b, "url": f"{SITE}/catalog-pt/{b['slug']}/"} for b in brand_infos]
    (PT_DIR / "index.html").write_text(build_hub("pt", en_hub_src, pt_infos), encoding="utf-8")
    print(f"  \u2713 hubs      EN + pt-BR")

    write_sitemap(list(BRANDS.keys()))
    write_robots()
    print("-" * 56)
    total = sum(b["n"] for b in brand_infos)
    print(f"Done. {total} parts × 2 languages now crawlable. "
          f"EN + pt-BR trees built.")


if __name__ == "__main__":
    main()
