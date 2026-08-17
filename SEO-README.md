# Van Vliet catalogue — bilingual + SEO update

This package makes the catalogue discoverable in search and adds a full
Brazilian-Portuguese version, without changing how the order tool works.

## What's in here

```
catalog-en/            English catalogue — now with SEO + hreflang + share image (overwrites existing)
catalog-pt/            NEW Brazilian-Portuguese catalogue (translated)
og/                    NEW — 1200x630 social share cards (og-en.png, og-pt.png)
sitemap.xml            NEW — lists all 13 URLs across both languages
robots.txt             NEW — points crawlers to the sitemap
build.py               The generator (re-run when inventory changes)
make_og_images.py      Regenerates the share cards (only if you want to change the art)
SEO-README.md          This file
```

Your existing `favicon.svg`, `favicon.ico` and `apple-touch-icon.png` already work
and are unchanged — the pages reference them by absolute path, so nothing to re-upload.

## How to upload

Everything is plain static files — just drop them into the repo root and push.

```bash
# from your local clone of order-List-EN, with this package extracted on top:
git add -A
git commit -m "Add pt-BR catalogue, SEO metadata, structured data, sitemap"
git push
```

GitHub Pages will serve `/catalog-en/` and `/catalog-pt/` automatically. Nothing
else to configure — the `CNAME` and Cloudflare setup are untouched.

## After it's live — do this once (this is what turns it into traffic)

1. **Google Search Console** → add property `oetrucksurplus.parts` (verify with a
   DNS TXT record in Cloudflare). Submit `https://oetrucksurplus.parts/sitemap.xml`.
2. **Bing Webmaster Tools** → same thing (you can import from Search Console).
3. Give it a few weeks. In Search Console → Performance, watch which OE part
   numbers show up as queries — that list is gold for outreach too.

## What changed technically

- Every part number was previously locked inside a `<script>` array, invisible to
  search engines. Each catalogue page now also has a real, crawlable stock list
  (grouped by category) exposing all part numbers as indexable text — same content
  users see, no cloaking.
- Each page got a unique `<title>`, meta description, canonical URL, Open Graph
  tags, and JSON-LD (AutoPartsStore + breadcrumbs + collection).
- `hreflang` tags link every English page to its Portuguese twin and back.
- Each page now advertises a branded 1200x630 share card (`og:image` +
  `twitter:image`), so links dropped in WhatsApp / LinkedIn / Telegram show a
  proper preview instead of bare text — English pages use the EN card, Portuguese
  pages the pt-BR card. Tip: after going live, paste a link into
  https://developers.facebook.com/tools/debug/ once to prime the preview cache.

## Regenerating (when the stock list changes)

The English pages under `catalog-en/` are the single source of truth. Update the
`ITEMS` data there as you do today, then:

```bash
python3 build.py
```

This rebuilds the Portuguese pages, refreshes all SEO blocks, and regenerates the
sitemap. It's safe to run repeatedly — it never duplicates anything.

## Notes / optional next steps

- Portuguese **part descriptions**: common terms (filters, seals, gaskets, hoses,
  screws, brakes, etc.) and all category names are translated; rarer technical
  descriptions fall back to English. The OE part number is the universal search
  key regardless. To translate more, extend the `TERM_PT` dictionary in `build.py`.
- **Cross-reference numbers**: if your source stock file has superseded/alternate
  OE numbers, adding them to the data would meaningfully widen search coverage —
  those alternates are half of how buyers search.
- The bare domain `oetrucksurplus.parts/` still redirects to the English catalogue.
  If you'd like it to offer a language choice (or auto-detect Portuguese visitors),
  that's a small follow-up.
