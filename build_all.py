#!/usr/bin/env python3
"""
build_all.py — combined "All brands" catalogue page + AI finder, run AFTER build.py.
Creates /catalog-en/all/ and /catalog-pt/all/ with the full order tool over all
brands, an embedded AI finder (local by default, live when AI_ENDPOINT is set),
lazy rendering, an "All" nav tab on every page, hub cards, and sitemap entries.
English pages are the single source of truth; PT derives via build.make_pt_page.
"""
import re, json, subprocess, importlib.util, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("build", REPO / "build.py")
build = importlib.util.module_from_spec(spec); spec.loader.exec_module(build)

SITE = build.SITE
EN_DIR, PT_DIR = build.EN_DIR, build.PT_DIR
ITEMS_RE = build.ITEMS_RE
esc = build.esc

AI_ENDPOINT = "REPLACE_WITH_WORKER_URL"
AI_TURNSTILE_SITEKEY = ""

BRAND_LABEL = {"vw":"VW","man":"MAN","mercedes":"Mercedes","iveco":"Iveco","toyota":"Toyota"}
SLUGS = ["vw","man","mercedes","iveco","toyota"]

L = {
  "en": {
    "title":"Van Vliet Automotive — All Brands Parts Catalogue",
    "sub_from":"Genuine MAN Parts &bull; OE surplus stock",
    "sub_to":"Genuine OE surplus parts &bull; all brands",
    "brand":"All","navlabel":"All","defcat":"All",
    "prompt":"Search above, pick a category, or use the AI finder to see parts.",
    "ai_title":"AI parts finder","ai_sub":"Describe what you need &mdash; in any language",
    "ai_ph":"e.g. front brake linings &middot; air dryer cartridge &middot; 81.50221",
    "ai_go":"Find","ai_all":"All","ai_empty":"No matches &mdash; try different words.",
    "ai_live":"AI &middot; live","ai_local":"Smart search","ai_show":"Show in list &rarr;",
    "ai_ts":"Please complete the check above, then search.",
    "meta_desc":"Search all genuine OE surplus truck parts across MAN, VW, Iveco, Mercedes-Benz and Toyota in one place. AI-assisted search, reference prices in EUR, ships from the Netherlands.",
  },
  "pt": {
    "title":"Van Vliet Automotive — Catálogo de Peças (Todas as Marcas)",
    "sub_from":"Peças genuínas MAN &bull; Estoque excedente OE",
    "sub_to":"Peças genuínas OE &bull; todas as marcas",
    "brand":"Todos","navlabel":"Todos","defcat":"Todas",
    "prompt":"Busque acima, escolha uma categoria ou use a busca IA para ver as peças.",
    "ai_title":"Busca IA de peças","ai_sub":"Descreva o que precisa &mdash; em qualquer idioma",
    "ai_ph":"ex.: lonas de freio &middot; vedação do motor &middot; 81.50221",
    "ai_go":"Buscar","ai_all":"Todas","ai_empty":"Nenhum resultado &mdash; tente outras palavras.",
    "ai_live":"IA &middot; ao vivo","ai_local":"Busca inteligente","ai_show":"Ver na lista &rarr;",
    "ai_ts":"Conclua a verificação acima e busque novamente.",
    "meta_desc":"Busque todas as peças genuínas OE excedentes de MAN, VW, Iveco, Mercedes-Benz e Toyota em um só lugar. Busca assistida por IA, preços em EUR, enviamos da Holanda.",
  },
}

def git_show(path):
    return subprocess.check_output(["git","show",f"HEAD:{path}"], cwd=REPO).decode("utf-8")

def parse_items(html):
    m = ITEMS_RE.search(html); return json.loads(m.group(1)) if m else []

AI_CSS = """
.aip{max-width:1080px;margin:14px auto 0;padding:0 16px}
.aip-in{background:linear-gradient(135deg,var(--navy),var(--blue) 70%,var(--blue2));border-radius:14px;padding:16px;color:#fff;box-shadow:0 8px 24px rgba(20,41,75,.22);border:2px solid var(--amber)}
.aip-head{display:flex;align-items:center;gap:11px;margin-bottom:12px}
.aip-ico{width:34px;height:34px;border-radius:9px;background:var(--amber);display:grid;place-items:center;color:var(--navy);flex:none}
.aip-t{font-size:15px;font-weight:800}
.aip-s{font-size:11.5px;color:#C6D4EC;font-weight:600}
.aip-mode{margin-left:auto;font-size:10.5px;font-weight:800;padding:4px 10px;border-radius:20px;background:rgba(255,255,255,.14);color:#fff;display:inline-flex;align-items:center;gap:6px}
.aip-mode.live{background:#E8F6EE;color:#0f5c33}
.aip-mode .d{width:6px;height:6px;border-radius:50%;background:currentColor}
.aip-chips{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:11px}
.aip-chip{font-size:12px;font-weight:700;padding:6px 12px;border-radius:20px;background:rgba(255,255,255,.12);color:#D7E1F1;cursor:pointer;border:1.5px solid transparent;user-select:none}
.aip-chip.on{background:var(--amber);color:var(--navy);border-color:var(--amber)}
.aip-row{display:flex;gap:9px;align-items:stretch}
.aip-row textarea{flex:1;border:none;border-radius:10px;padding:11px 13px;font-family:inherit;font-size:14.5px;resize:vertical;min-height:46px;color:var(--ink)}
.aip-row textarea:focus{outline:3px solid var(--amber)}
.aip-go{flex:none;border:none;border-radius:10px;padding:0 18px;font-weight:800;font-family:inherit;font-size:14.5px;background:var(--amber);color:var(--navy);cursor:pointer}
.aip-go:hover{background:var(--amber-d);color:#fff}
.aip-go:disabled{opacity:.55;cursor:not-allowed}
.aip-res{margin-top:12px;display:grid;gap:8px}
.aip-res:empty{margin-top:0}
.aip-r{background:rgba(255,255,255,.10);border-radius:10px;padding:10px 12px;display:flex;align-items:center;gap:10px;cursor:pointer;transition:.12s}
.aip-r:hover{background:rgba(255,255,255,.18)}
.aip-r .rp{font-family:var(--mono);font-size:12.5px;font-weight:800;color:#fff;flex:none}
.aip-r .rb{font-size:9.5px;font-weight:800;color:var(--navy);background:var(--amber);border-radius:5px;padding:2px 6px;flex:none}
.aip-r .rd{font-size:13px;color:#EAF0FA;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.aip-r .rs{margin-left:auto;font-size:11.5px;font-weight:800;color:#F4B23E;flex:none}
.aip-note{font-size:12px;color:#C6D4EC;padding:6px 2px}
.aip-tsbox{margin-top:10px}
"""

def ai_html(t):
    return f"""<section class="aip">
  <div class="aip-in">
    <div class="aip-head">
      <div class="aip-ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#14294B" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.9 5.8L20 9l-4.8 3.7L17 19l-5-3.6L7 19l1.8-6.3L4 9l6.1-.2z"/></svg></div>
      <div><div class="aip-t">{t['ai_title']}</div><div class="aip-s">{t['ai_sub']}</div></div>
      <span class="aip-mode" id="aipMode"></span>
    </div>
    <div class="aip-chips" id="aipChips"></div>
    <div class="aip-row">
      <textarea id="aipQ" maxlength="300" placeholder="{t['ai_ph']}"></textarea>
      <button class="aip-go" id="aipGo">{t['ai_go']}</button>
    </div>
    <div class="aip-tsbox" id="aipTs"></div>
    <div class="aip-res" id="aipRes" aria-live="polite"></div>
  </div>
</section>
"""

def ai_js(t):
    endpoint = "" if "REPLACE" in AI_ENDPOINT else AI_ENDPOINT
    return f"""
/* ===== embedded AI parts finder (local by default; live when endpoint set) ===== */
(function(){{
  const AI_ENDPOINT = {json.dumps(endpoint)};
  const AI_TS_KEY   = {json.dumps(AI_TURNSTILE_SITEKEY)};
  const LIVE = !!AI_ENDPOINT;
  const SLUG = {{VW:"vw",MAN:"man",Mercedes:"mercedes",Iveco:"iveco",Toyota:"toyota"}};
  const LABELS = ["VW","MAN","Mercedes","Iveco","Toyota"];
  const ALL_LABEL = {json.dumps(t['ai_all'])};
  const el = s => document.querySelector(s);
  let sel = new Set(LABELS), TS_TOKEN="", TS_W=null;

  const mb = el("#aipMode");
  mb.className = "aip-mode" + (LIVE?" live":"");
  mb.innerHTML = '<span class="d"></span>' + (LIVE ? {json.dumps(t['ai_live'])} : {json.dumps(t['ai_local'])});

  const chips = el("#aipChips");
  const mk = (label,on)=>{{ const b=document.createElement("span"); b.className="aip-chip"+(on?" on":""); b.textContent=label; return b; }};
  const allChip = mk(ALL_LABEL,true); chips.appendChild(allChip);
  const chipEls = {{}};
  LABELS.forEach(l=>{{ const c=mk(l,true); chipEls[l]=c; chips.appendChild(c);
    c.onclick=()=>{{ c.classList.toggle("on"); c.classList.contains("on")?sel.add(l):sel.delete(l); syncAll(); }};
  }});
  allChip.onclick=()=>{{ const on=!(sel.size===LABELS.length); sel=on?new Set(LABELS):new Set();
    LABELS.forEach(l=>chipEls[l].classList.toggle("on",on)); allChip.classList.toggle("on",on); }};
  function syncAll(){{ allChip.classList.toggle("on", sel.size===LABELS.length); }}

  if(LIVE && AI_TS_KEY){{
    const s=document.createElement("script");
    s.src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit"; s.async=true; s.defer=true;
    s.onload=()=>{{ try{{ TS_W=window.turnstile.render("#aipTs",{{sitekey:AI_TS_KEY,callback:t=>TS_TOKEN=t||"","expired-callback":()=>TS_TOKEN="","error-callback":()=>TS_TOKEN=""}}); }}catch(e){{}} }};
    document.head.appendChild(s);
  }}
  function tsReset(){{ try{{ if(TS_W!==null){{ window.turnstile.reset(TS_W); TS_TOKEN=""; }} }}catch(e){{}} }}

  const norm = s => (s||"").toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g,"");
  const SYN = {{
    brake:["brake","brakes","freio","freios","bremse","rem","lining","linings","shoe","drum","pad","pads","lona","lonas"],
    filter:["filter","filtro","filtre","filters","element","elemento","cartridge","cartucho","insert"],
    engine:["engine","motor","camshaft","turbo","turbocharger","turbocompressor","belt","correia","tensioner","tensor","exhaust","silencer"],
    cool:["cooling","radiator","radiador","coolant","thermostat","termostato","water","hose","mangueira","arrefecimento"],
    clutch:["clutch","embreagem","kupplung","release","bearing","rolamento"],
    light:["light","lamp","luz","farol","led","flasher","pisca","indicator","rear"],
    elec:["electric","electrical","battery","bateria","solenoid","solenoide","relay","rele","radio","sensor"],
    mirror:["mirror","espelho","spiegel"],
    wiper:["wiper","blade","washer","limpador","palheta"],
    fuel:["fuel","tank","tanque","combustivel","diesel"],
    susp:["suspension","spring","mola","steering","direcao","suspensao","parabolic"],
    seal:["seal","gasket","junta","retentor","vedacao","dichtung","o-ring","oring"],
  }};

  function localSearch(query, brands){{
    const nq=" "+norm(query)+" ";
    const isPN=/[0-9]{{2,}}[.\\-]?[0-9]/.test(query);
    const groups=Object.values(SYN).filter(ws=>ws.some(w=>nq.includes(" "+norm(w))));
    const pool=ITEMS.filter(i=>brands.includes(i.b));
    const scored=pool.map(i=>{{
      let s=0; const hay=norm(i.d+" "+i.c);
      if(isPN && i.pn.toLowerCase().replace(/\\s/g,"").includes(query.toLowerCase().replace(/\\s/g,""))) s+=100;
      norm(query).split(/\\s+/).filter(x=>x.length>2).forEach(x=>{{ if(hay.includes(x)) s+=8; }});
      groups.forEach(ws=>{{ if(ws.some(w=>hay.includes(norm(w)))) s+=5; }});
      return {{...i, s}};
    }}).filter(x=>x.s>0).sort((a,b)=>b.s-a.s).slice(0,15);
    return scored.map(x=>({{pn:x.pn,d:x.d,c:x.c,brand:x.b}}));
  }}

  async function liveSearch(query, brands){{
    const body={{brands:brands.map(b=>SLUG[b]).filter(Boolean),query}};
    if(AI_TS_KEY) body.token=TS_TOKEN;
    const r=await fetch(AI_ENDPOINT,{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify(body)}});
    tsReset();
    if(r.status===429) throw new Error("rate limit");
    if(!r.ok) throw new Error("server "+r.status);
    const d=await r.json();
    const label={{vw:"VW",man:"MAN",mercedes:"Mercedes",iveco:"Iveco",toyota:"Toyota"}};
    return (d.results||[]).map(x=>({{...x, brand: x.brand&&label[x.brand]?label[x.brand]:x.brand}}));
  }}

  const res=el("#aipRes"), go=el("#aipGo"), qbox=el("#aipQ");
  let busy=false, last=0;
  go.onclick=search;
  qbox.addEventListener("keydown",e=>{{ if((e.metaKey||e.ctrlKey)&&e.key==="Enter") search(); }});

  async function search(){{
    if(busy) return;
    const query=qbox.value.trim();
    if(query.length<2){{ res.innerHTML='<div class="aip-note">'+{json.dumps(t['ai_empty'])}+'</div>'; return; }}
    if(sel.size===0){{ res.innerHTML='<div class="aip-note">'+ALL_LABEL+'</div>'; return; }}
    if(Date.now()-last<1500) return; last=Date.now();
    if(LIVE && AI_TS_KEY && !TS_TOKEN){{ res.innerHTML='<div class="aip-note">'+{json.dumps(t['ai_ts'])}+'</div>'; return; }}
    busy=true; go.disabled=true; res.innerHTML='<div class="aip-note">…</div>';
    try{{
      const items = LIVE ? await liveSearch(query,[...sel]) : (await new Promise(r=>setTimeout(()=>r(localSearch(query,[...sel])),300)));
      if(!items.length){{ res.innerHTML='<div class="aip-note">'+{json.dumps(t['ai_empty'])}+'</div>'; return; }}
      res.innerHTML=items.map(it=>`<div class="aip-r" data-pn="${{it.pn}}"><span class="rb">${{it.brand||""}}</span><span class="rp">${{it.pn}}</span><span class="rd">${{(it.d||"").replace(/</g,"&lt;")}}</span><span class="rs">{json.dumps(t['ai_show'])}</span></div>`).join("");
      res.querySelectorAll(".aip-r").forEach(r=>r.onclick=()=>showInList(r.getAttribute("data-pn")));
    }}catch(e){{
      res.innerHTML='<div class="aip-note">'+(e.message==="rate limit"?"…":{json.dumps(t['ai_empty'])})+'</div>';
    }}finally{{ busy=false; go.disabled=false; }}
  }}

  function showInList(pn){{
    const inp=$("#q"); if(inp) inp.value=pn;
    term=pn; activeCat=DEFAULT_CAT;
    const cs=$("#catsel"); if(cs) cs.value=DEFAULT_CAT;
    render();
    const m=document.querySelector("main.wrap"); if(m) m.scrollIntoView({{behavior:"smooth"}});
  }}
}})();
"""

def make_all_page(lang):
    t = L[lang]
    tpl = git_show("catalog-en/man/index.html")
    if lang == "pt":
        tpl = build.make_pt_page(tpl, "man")
    h = build.strip_all_sentinels(tpl)

    merged = []
    for slug in SLUGS:
        if lang == "en":
            items = parse_items(git_show(f"catalog-en/{slug}/index.html"))
        else:
            items = parse_items((PT_DIR / slug / "index.html").read_text(encoding="utf-8"))
        for it in items:
            it["b"] = BRAND_LABEL[slug]; merged.append(it)

    h = re.sub(r"<title>.*?</title>", f"<title>{esc(t['title'])}</title>", h, count=1, flags=re.S)
    h = h.replace(t["sub_from"], t["sub_to"])

    h = h.replace('const BRAND = "MAN";',
                  f'const BRAND = "{t["brand"]}";\nconst DEFAULT_CAT = "{t["defcat"]}";\n'
                  f'const PROMPT_HTML = \'<div class="empty" style="grid-column:1/-1"><svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="#6A7788" stroke-width="1.6"><circle cx="11" cy="11" r="7"/><path d="m20 20-3-3"/></svg><div>{t["prompt"]}</div></div>\';', 1)

    m = ITEMS_RE.search(h)
    h = h[:m.start()] + "const ITEMS = " + json.dumps(merged, ensure_ascii=False) + ";" + h[m.end():]

    h = re.sub(r"const BRANDS_NAV=\[.*?\];",
               f'const BRANDS_NAV=[["{t["navlabel"]}","../all/"],["VW","../vw/"],["MAN","../man/"],["Mercedes","../mercedes/"],["Iveco","../iveco/"],["Toyota","../toyota/"]];',
               h, count=1)

    h = h.replace("ck(BRAND,i.pn)", "ck(i.b,i.pn)")
    h = h.replace("{brand:BRAND,pn:i.pn,", "{brand:i.b,pn:i.pn,")
    h = h.replace('<div class="pn">${i.pn}</div>',
                  '<div class="pn"><span class="bpill">${i.b}</span>${i.pn}</div>')
    h = h.replace('const list=visible(), grid=$("#grid");',
                  'const grid=$("#grid");\n  if(!term.trim() && activeCat===DEFAULT_CAT){ $("#count").textContent=""; grid.innerHTML=PROMPT_HTML; return; }\n  const list=visible();', 1)

    h = h.replace("</style>", AI_CSS + "</style>", 1)
    h = h.replace('<main class="wrap">', ai_html(t) + '<main class="wrap">', 1)
    h = h.replace("render();updateBar();\n</script>", ai_js(t) + "\nrender();updateBar();\n</script>", 1)

    url = f"{SITE}/catalog-{lang}/all/"
    ld = {"@context":"https://schema.org","@type":"CollectionPage","url":url,
          "name":t["title"],"description":t["meta_desc"],
          "inLanguage":"pt-BR" if lang=="pt" else "en",
          "isPartOf":{"@type":"AutoPartsStore","name":"Van Vliet Automotive","url":SITE+"/"}}
    head = "\n".join([
        build.HEAD_START,
        f'<meta name="description" content="{esc(t["meta_desc"])}">',
        '<meta name="robots" content="index,follow,max-image-preview:large">',
        f'<link rel="canonical" href="{url}">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Van Vliet Automotive">',
        f'<meta property="og:title" content="{esc(t["title"])}">',
        f'<meta property="og:description" content="{esc(t["meta_desc"])}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{SITE}/og/og-{lang}.png">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<script type="application/ld+json">{json.dumps(ld,ensure_ascii=False,separators=(",",":"))}</script>',
        build.HEAD_END,
    ]) + "\n"
    href = "\n".join([
        build.HREF_START,
        f'<link rel="alternate" hreflang="en" href="{SITE}/catalog-en/all/">',
        f'<link rel="alternate" hreflang="pt-BR" href="{SITE}/catalog-pt/all/">',
        f'<link rel="alternate" hreflang="x-default" href="{SITE}/catalog-en/all/">',
        build.HREF_END,
    ]) + "\n"
    h = h.replace("</head>", head + href + "</head>", 1)

    out = (EN_DIR if lang=="en" else PT_DIR) / "all"
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(h, encoding="utf-8")
    return len(merged)

def patch_brand_nav():
    for lang, base in (("en",EN_DIR),("pt",PT_DIR)):
        label = L[lang]["navlabel"]
        for slug in SLUGS:
            p = base / slug / "index.html"; h = p.read_text(encoding="utf-8")
            new = re.sub(r'const BRANDS_NAV=\[\["VW"',
                         f'const BRANDS_NAV=[["{label}","../all/"],["VW"', h, count=1)
            if new != h: p.write_text(new, encoding="utf-8")

def patch_hubs():
    for lang, base in (("en",EN_DIR),("pt",PT_DIR)):
        p = base / "index.html"; h = p.read_text(encoding="utf-8")
        if 'href="all/"' in h: continue
        if lang == "en":
            card = ('    <a class="card" href="all/" style="border-top-color:#E8850C;background:linear-gradient(135deg,#14294B,#2E5496);color:#fff">\n'
                    '      <div class="bn" style="color:#fff">All brands</div>\n'
                    '      <div class="cnt" style="color:#C6D4EC">Search everything &middot; AI finder</div>\n'
                    '      <div class="go" style="color:#F4B23E">Open &rarr;</div>\n    </a>\n')
        else:
            card = ('    <a class="card" href="all/" style="border-top-color:#E8850C;background:linear-gradient(135deg,#14294B,#2E5496);color:#fff">\n'
                    '      <div class="bn" style="color:#fff">Todas as marcas</div>\n'
                    '      <div class="cnt" style="color:#C6D4EC">Buscar tudo &middot; busca IA</div>\n'
                    '      <div class="go" style="color:#F4B23E">Abrir &rarr;</div>\n    </a>\n')
        h = h.replace('<div class="grid">', '<div class="grid">\n' + card, 1)
        p.write_text(h, encoding="utf-8")

def patch_sitemap():
    p = REPO / "sitemap.xml"
    if not p.exists(): return
    h = p.read_text(encoding="utf-8")
    if "/catalog-en/all/" in h: return
    today = datetime.date.today().isoformat()
    extra = "".join(
        f'  <url><loc>{SITE}/catalog-{lg}/all/</loc><lastmod>{today}</lastmod>'
        f'<changefreq>weekly</changefreq><priority>0.9</priority></url>\n'
        for lg in ("en","pt"))
    h = h.replace("</urlset>", extra + "</urlset>")
    p.write_text(h, encoding="utf-8")

def main():
    print("Combined All-brands page + AI finder"); print("-"*46)
    for lang in ("en","pt"):
        n = make_all_page(lang); print(f"  \u2713 catalog-{lang}/all/  ({n} parts, embedded AI finder)")
    patch_brand_nav(); print("  \u2713 'All' tab added to brand nav (10 pages)")
    patch_hubs();      print("  \u2713 'All brands' card added to hubs")
    patch_sitemap();   print("  \u2713 sitemap updated (+2 urls)")
    print("-"*46)
    print("Done." + ("" if "REPLACE" not in AI_ENDPOINT else "  AI finder in LOCAL mode until AI_ENDPOINT is set."))

if __name__ == "__main__":
    main()
