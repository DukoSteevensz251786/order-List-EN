#!/usr/bin/env python3
"""
build_gallery.py — "Warehouse & Stock" trust gallery (EN + PT), run after build.py/build_all.py.
Optimises the uploaded photos into /images/warehouse/{full,thumb}, builds a lightbox
gallery page per language, adds a "Warehouse" nav tab + hub card, and updates the sitemap.
"""
import re, shutil, importlib.util
from pathlib import Path
from PIL import Image, ImageOps

REPO = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("build", REPO / "build.py")
build = importlib.util.module_from_spec(spec); spec.loader.exec_module(build)
SITE, esc = build.SITE, build.esc
EN_DIR, PT_DIR = build.EN_DIR, build.PT_DIR
UPLOADS = Path("/mnt/user-data/uploads")
IMG_DIR = REPO / "images" / "warehouse"

# uploaded file -> (output slug, section, caption EN, caption PT)
PHOTOS = [
  ("WhatsApp_Image_2026-07-21_at_14_24_24__1_.jpeg","wh-01","warehouse",
     "Pallet racking with genuine MAN OE stock","Porta-paletes com estoque genuíno MAN OE"),
  ("WhatsApp_Image_2026-07-21_at_14_24_24.jpeg","wh-02","warehouse",
     "Genuine MAN &amp; NEOPLAN parts, boxed and stillaged","Peças genuínas MAN e NEOPLAN, encaixotadas"),
  ("WhatsApp_Image_2026-07-21_at_14_24_23__1_.jpeg","wh-03","warehouse",
     "Organised inventory, ready to ship","Inventário organizado, pronto para envio"),
  ("WhatsApp_Image_2026-07-21_at_14_24_23__2_.jpeg","wh-04","warehouse",
     "Location-labelled aisles across the warehouse","Corredores etiquetados por localização"),
  ("WhatsApp_Image_2026-07-21_at_14_24_23__4_.jpeg","wh-05","warehouse",
     "Part of our 1,500+ line-item surplus","Parte do excedente de mais de 1.500 itens"),
  ("WhatsApp_Image_2026-08-13_at_09_10_57.jpeg","part-01","parts",
     "AP Racing brake caliper — genuine OE","Pinça de freio AP Racing — OE genuína"),
  ("WhatsApp_Image_2026-07-24_at_11_39_58__3_.jpeg","part-02","parts",
     "ABS / hydraulic control unit","Unidade de controle ABS / hidráulica"),
  ("WhatsApp_Image_2026-07-24_at_10_04_11.jpeg","part-03","parts",
     "Complete overhaul kit — seals, bearings, gaskets","Kit de revisão — retentores, rolamentos, juntas"),
]

def process_images():
    (IMG_DIR/"full").mkdir(parents=True, exist_ok=True)
    (IMG_DIR/"thumb").mkdir(parents=True, exist_ok=True)
    done = []
    for src, slug, *_ in PHOTOS:
        p = UPLOADS / src
        if not p.exists():
            print(f"  ! missing {src}"); continue
        im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
        full = im.copy(); full.thumbnail((1600,1600), Image.LANCZOS)
        full.save(IMG_DIR/"full"/f"{slug}.jpg","JPEG",quality=82,optimize=True,progressive=True)
        th = im.copy(); th.thumbnail((700,700), Image.LANCZOS)
        th.save(IMG_DIR/"thumb"/f"{slug}.jpg","JPEG",quality=80,optimize=True,progressive=True)
        done.append(slug)
    return done

L = {
  "en":{"navlabel":"Warehouse","title":"Warehouse &amp; Stock — Van Vliet Automotive",
    "h1":"Warehouse &amp; Stock","sub":"Real photos of our stock and premises",
    "intro":"Van Vliet Automotive is an official MAN Truck &amp; Bus importer in the Netherlands. Below are photos of our actual warehouse and surplus stock &mdash; genuine OE parts, organised and ready to ship worldwide. What you see is what we hold.",
    "s_wh":"Inside our warehouse","s_pt":"Genuine parts, up close",
    "back":"&larr; Back to catalogue","cta":"Browse the parts catalogue &rarr;",
    "meta":"Photos of the Van Vliet Automotive warehouse and genuine OE surplus truck-parts stock in the Netherlands. MAN, VW, Iveco, Mercedes-Benz, Toyota.",
    "loc":"Nieuwerkerk aan den IJssel, Netherlands"},
  "pt":{"navlabel":"Estoque","title":"Armazém &amp; Estoque — Van Vliet Automotive",
    "h1":"Nosso Armazém &amp; Estoque","sub":"Fotos reais do nosso estoque e instalações",
    "intro":"A Van Vliet Automotive é importadora oficial MAN Truck &amp; Bus na Holanda. Abaixo estão fotos do nosso armazém e do estoque excedente &mdash; peças genuínas OE, organizadas e prontas para envio mundial. O que você vê é o que temos.",
    "s_wh":"Dentro do nosso armazém","s_pt":"Peças genuínas, de perto",
    "back":"&larr; Voltar ao catálogo","cta":"Ver o catálogo de peças &rarr;",
    "meta":"Fotos do armazém da Van Vliet Automotive e do estoque excedente de peças genuínas OE para caminhões na Holanda. MAN, VW, Iveco, Mercedes-Benz, Toyota.",
    "loc":"Nieuwerkerk aan den IJssel, Holanda"},
}

def tiles(section, lang):
    out=[]
    for src,slug,sec,cap_en,cap_pt in PHOTOS:
        if sec!=section: continue
        cap = cap_en if lang=="en" else cap_pt
        out.append(
          f'<figure class="tile" data-full="/images/warehouse/full/{slug}.jpg" data-cap="{esc(cap)}">'
          f'<img src="/images/warehouse/thumb/{slug}.jpg" alt="{esc(cap)}" loading="lazy" width="700" height="933">'
          f'<figcaption>{cap}</figcaption></figure>')
    return "\n".join(out)

def page(lang):
    t=L[lang]; url=f"{SITE}/catalog-{lang}/warehouse/"
    nav = "".join(f'<a href="../{s}/">{n}</a>' for n,s in
        [("All" if lang=="en" else "Todos","all"),("VW","vw"),("MAN","man"),
         ("Mercedes","mercedes"),("Iveco","iveco"),("Toyota","toyota")])
    return f"""<!DOCTYPE html>
<html lang="{'pt-BR' if lang=='pt' else 'en'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{t['title']}</title>
<meta name="description" content="{esc(t['meta'])}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="en" href="{SITE}/catalog-en/warehouse/">
<link rel="alternate" hreflang="pt-BR" href="{SITE}/catalog-pt/warehouse/">
<link rel="alternate" hreflang="x-default" href="{SITE}/catalog-en/warehouse/">
<meta property="og:type" content="website">
<meta property="og:title" content="{t['title']}">
<meta property="og:description" content="{esc(t['meta'])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/images/warehouse/full/wh-01.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<style>
:root{{--navy:#14294B;--blue:#2E5496;--blue2:#3D6BC4;--amber:#E8850C;--amber-d:#C4700A;--bg:#EAEEF3;--card:#fff;--ink:#182233;--muted:#6A7788;--line:#DCE3EC;--sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
*{{box-sizing:border-box}}html,body{{margin:0}}
body{{font-family:var(--sans);background:var(--bg);color:var(--ink)}}
.top{{background:var(--navy);color:#fff;box-shadow:0 2px 10px rgba(20,41,75,.25)}}
.top-in{{max-width:1080px;margin:0 auto;padding:15px 18px;display:flex;align-items:center;gap:11px}}
.mark{{width:38px;height:38px;border-radius:9px;background:var(--amber);display:grid;place-items:center;font-weight:800;color:var(--navy);font-size:16px;flex:none}}
.top h1{{font-size:17px;font-weight:800;margin:0}}
.top .s{{font-size:11.5px;color:#B9C6DD;font-weight:600}}
.nav{{background:#0F1F3A;border-top:1px solid rgba(255,255,255,.08)}}
.nav-in{{max-width:1080px;margin:0 auto;padding:0 12px;display:flex;flex-wrap:wrap;gap:2px}}
.nav a{{color:#C6D4EC;text-decoration:none;font-size:13px;font-weight:700;padding:11px 13px}}
.nav a:hover{{color:#fff}}
.nav a.active{{color:var(--amber);box-shadow:inset 0 -3px 0 var(--amber)}}
.wrap{{max-width:1080px;margin:0 auto;padding:22px 18px 50px}}
.intro{{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--amber);border-radius:12px;padding:16px 18px;font-size:14.5px;line-height:1.55;color:#33445c}}
.intro b{{color:var(--navy)}}
.crumbs{{display:flex;justify-content:space-between;align-items:center;margin:18px 2px 8px;gap:12px;flex-wrap:wrap}}
.crumbs a{{color:var(--blue);font-weight:800;font-size:13.5px;text-decoration:none}}
.crumbs a:hover{{text-decoration:underline}}
h2.sec{{font-size:15px;font-weight:800;color:var(--navy);margin:26px 2px 12px;padding-bottom:8px;border-bottom:2px solid var(--line)}}
.grid{{columns:3;column-gap:12px}}
@media(max-width:820px){{.grid{{columns:2}}}}
@media(max-width:520px){{.grid{{columns:1}}}}
.tile{{break-inside:avoid;margin:0 0 12px;position:relative;border-radius:12px;overflow:hidden;cursor:zoom-in;box-shadow:0 3px 12px rgba(20,41,75,.12);background:#000}}
.tile img{{width:100%;display:block;transition:.25s}}
.tile:hover img{{transform:scale(1.04);opacity:.92}}
.tile figcaption{{position:absolute;left:0;right:0;bottom:0;padding:22px 12px 10px;font-size:12.5px;font-weight:700;color:#fff;background:linear-gradient(transparent,rgba(10,20,40,.82))}}
.loc{{text-align:center;color:var(--muted);font-size:12.5px;margin-top:26px}}
/* lightbox */
.lb{{position:fixed;inset:0;background:rgba(9,16,30,.94);display:none;z-index:100;align-items:center;justify-content:center;flex-direction:column;padding:20px}}
.lb.open{{display:flex}}
.lb img{{max-width:94vw;max-height:82vh;border-radius:8px;box-shadow:0 12px 40px rgba(0,0,0,.5)}}
.lb .cap{{color:#fff;font-size:14px;font-weight:600;margin-top:14px;text-align:center;max-width:90vw}}
.lb .x{{position:absolute;top:16px;right:20px;color:#fff;font-size:30px;font-weight:300;cursor:pointer;line-height:1;opacity:.85}}
.lb .nav-btn{{position:absolute;top:50%;transform:translateY(-50%);color:#fff;font-size:44px;font-weight:300;cursor:pointer;opacity:.7;user-select:none;padding:0 18px}}
.lb .nav-btn:hover{{opacity:1}}
.lb .prev{{left:4px}}.lb .next{{right:4px}}
.cta-b{{display:inline-block;margin-top:8px;background:var(--amber);color:var(--navy);font-weight:800;text-decoration:none;padding:12px 20px;border-radius:11px;font-size:14.5px}}
.cta-b:hover{{background:var(--amber-d);color:#fff}}
</style>
</head>
<body>
<header class="top"><div class="top-in">
  <div class="mark">VV</div>
  <div><h1>Van Vliet Automotive</h1><div class="s">{t['sub']}</div></div>
</div>
<div class="nav"><div class="nav-in">{nav}<a href="../warehouse/" class="active">{t['navlabel']}</a></div></div>
</header>

<main class="wrap">
  <div class="intro">{t['intro']}</div>
  <div class="crumbs"><a href="../all/">{t['back']}</a></div>

  <h2 class="sec">{t['s_wh']}</h2>
  <div class="grid">
{tiles("warehouse",lang)}
  </div>

  <h2 class="sec">{t['s_pt']}</h2>
  <div class="grid">
{tiles("parts",lang)}
  </div>

  <p class="loc">{t['loc']}</p>
  <div style="text-align:center;margin-top:14px"><a class="cta-b" href="../all/">{t['cta']}</a></div>
</main>

<div class="lb" id="lb">
  <span class="x" id="lbx">&times;</span>
  <span class="nav-btn prev" id="lbp">&lsaquo;</span>
  <span class="nav-btn next" id="lbn">&rsaquo;</span>
  <img id="lbimg" src="" alt="">
  <div class="cap" id="lbcap"></div>
</div>
<script>
(function(){{
  const tiles=[...document.querySelectorAll(".tile")];
  const lb=document.getElementById("lb"),img=document.getElementById("lbimg"),cap=document.getElementById("lbcap");
  let idx=0;
  function show(i){{ idx=(i+tiles.length)%tiles.length; const t=tiles[idx];
    img.src=t.getAttribute("data-full"); cap.textContent=t.getAttribute("data-cap"); lb.classList.add("open"); }}
  tiles.forEach((t,i)=>t.addEventListener("click",()=>show(i)));
  document.getElementById("lbx").onclick=()=>lb.classList.remove("open");
  document.getElementById("lbp").onclick=e=>{{e.stopPropagation();show(idx-1);}};
  document.getElementById("lbn").onclick=e=>{{e.stopPropagation();show(idx+1);}};
  lb.addEventListener("click",e=>{{ if(e.target===lb) lb.classList.remove("open"); }});
  document.addEventListener("keydown",e=>{{ if(!lb.classList.contains("open"))return;
    if(e.key==="Escape")lb.classList.remove("open"); if(e.key==="ArrowLeft")show(idx-1); if(e.key==="ArrowRight")show(idx+1); }});
}})();
</script>
</body>
</html>
"""

def write_pages():
    for lang,base in (("en",EN_DIR),("pt",PT_DIR)):
        out=base/"warehouse"; out.mkdir(exist_ok=True)
        (out/"index.html").write_text(page(lang),encoding="utf-8")

def patch_nav():
    for lang,base in (("en",EN_DIR),("pt",PT_DIR)):
        label=L[lang]["navlabel"]
        for sub in ["vw","man","mercedes","iveco","toyota","all"]:
            p=base/sub/"index.html"
            if not p.exists(): continue
            h=p.read_text(encoding="utf-8")
            if '"../warehouse/"' in h: continue
            new=re.sub(r'(\["Toyota","\.\./toyota/"\])(\];)',
                       rf'\1,["{label}","../warehouse/"]\2', h, count=1)
            if new!=h: p.write_text(new,encoding="utf-8")

def patch_hubs():
    for lang,base in (("en",EN_DIR),("pt",PT_DIR)):
        p=base/"index.html"; h=p.read_text(encoding="utf-8")
        if 'href="warehouse/"' in h: continue
        if lang=="en":
            card=('    <a class="card" href="warehouse/" style="border-top-color:#E8850C">\n'
                  '      <div class="bn">Warehouse &amp; stock</div>\n'
                  '      <div class="cnt">See our premises &amp; real stock</div>\n'
                  '      <div class="go">View photos &rarr;</div>\n    </a>\n')
        else:
            card=('    <a class="card" href="warehouse/" style="border-top-color:#E8850C">\n'
                  '      <div class="bn">Armazém &amp; estoque</div>\n'
                  '      <div class="cnt">Veja nossas instalações e estoque real</div>\n'
                  '      <div class="go">Ver fotos &rarr;</div>\n    </a>\n')
        h=h.replace('<div class="grid">','<div class="grid">\n'+card,1)
        p.write_text(h,encoding="utf-8")

def patch_sitemap():
    p=REPO/"sitemap.xml"
    if not p.exists(): return
    h=p.read_text(encoding="utf-8")
    if "/warehouse/" in h: return
    import datetime; today=datetime.date.today().isoformat()
    extra="".join(f'  <url><loc>{SITE}/catalog-{lg}/warehouse/</loc><lastmod>{today}</lastmod>'
                  f'<changefreq>monthly</changefreq><priority>0.7</priority></url>\n' for lg in ("en","pt"))
    p.write_text(h.replace("</urlset>",extra+"</urlset>"),encoding="utf-8")

def main():
    print("Warehouse & Stock gallery"); print("-"*40)
    done=process_images(); print(f"  \u2713 optimised {len(done)} photos -> images/warehouse/{{full,thumb}}")
    write_pages();  print("  \u2713 catalog-en/warehouse/ + catalog-pt/warehouse/")
    patch_nav();    print("  \u2713 'Warehouse' nav tab added")
    patch_hubs();   print("  \u2713 hub cards added")
    patch_sitemap();print("  \u2713 sitemap updated (+2 urls)")

if __name__=="__main__":
    main()
