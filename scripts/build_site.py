#!/usr/bin/env python3
"""Generate all Breaking Ground static HTML pages from data/*.json."""
from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TODAY = date.today().isoformat()

SITE = json.loads((DATA / "site.json").read_text(encoding="utf-8"))
SERVICES = json.loads((DATA / "services.json").read_text(encoding="utf-8"))
PROJECTS = json.loads((DATA / "projects.json").read_text(encoding="utf-8"))
AREAS = json.loads((DATA / "service-areas.json").read_text(encoding="utf-8"))
REVIEWS = json.loads((DATA / "google-reviews.json").read_text(encoding="utf-8"))
_FORMSPREE_CFG = json.loads((ROOT / "formspree.json").read_text(encoding="utf-8")) if (ROOT / "formspree.json").is_file() else {}
FORM = (
    _FORMSPREE_CFG.get("forms", {}).get("estimateForm", {}).get("endpoint")
    or SITE.get("formspreeEndpoint", "https://formspree.io/contact@breakinggroundlsad.com")
)
DOMAIN = SITE["domain"].rstrip("/")
BASE = (SITE.get("siteBase") or "").rstrip("/")
PHONE = SITE["phone"]
PHONE_TEL = SITE["phoneTel"]
EMAIL = SITE["email"]
NAME = SITE["name"]
SHORT = SITE["shortName"]
LEGAL = SITE["legalName"]
LOGO = SITE["logo"]
OG = SITE["defaultOgImage"]
GOOGLE_MAPS_URL = REVIEWS.get(
    "googleMapsUrl",
    "https://www.google.com/maps?cid=9571487126708767252",
)
MAP_EMBED_SRC = REVIEWS.get(
    "mapEmbedSrc",
    "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d28664363.395064767!2d-120.9932133287108!3d28.717519809660633!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0xadfede66cc9b47f9%3A0x84d4c0d46fb34a14!2sBreaking%20Ground%20Land%20Services%20and%20Demolition!5e0!3m2!1sen!2sus!4v1785159366164!5m2!1sen!2sus",
)
_MANIFEST_PATH = DATA / "image-manifest.json"
IMAGE_MANIFEST: dict = {}
if _MANIFEST_PATH.is_file():
    IMAGE_MANIFEST = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))

TILE_SIZES = "(max-width: 600px) 100vw, (max-width: 900px) 50vw, 33vw"
CARD_SIZES = "(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 400px"
HERO_SIZES = "100vw"
PAGE_HERO_SIZES = "(max-width: 900px) 100vw, 50vw"
LCP_HERO = "/assets/images/hero/IMG_0078-hero.jpg"


def p(path: str) -> str:
    """Prefix siteBase for GitHub project Pages preview; empty on custom domain."""
    if not path.startswith("/"):
        path = "/" + path
    return f"{BASE}{path}" if BASE else path


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def best_webp(path: str) -> str:
    if not path:
        return path
    key = path if path.startswith("/") else "/" + path.lstrip("/")
    if key.lower().endswith((".jpg", ".jpeg", ".png")):
        webp_key = f"{key.rsplit('.', 1)[0]}.webp"
        if webp_key in IMAGE_MANIFEST:
            return webp_key
    if key in IMAGE_MANIFEST:
        return key
    if key.lower().endswith((".jpg", ".jpeg", ".png")):
        return f"{key.rsplit('.', 1)[0]}.webp"
    return key


def img_entry(path: str) -> dict:
    key = best_webp(path)
    return IMAGE_MANIFEST.get(
        key,
        {"src": key, "width": None, "height": None, "variants": {}},
    )


def img_responsive(
    path: str,
    alt: str = "",
    *,
    sizes: str = "100vw",
    loading: str = "lazy",
    fetchpriority: str | None = None,
    width: int | None = None,
    height: int | None = None,
    klass: str = "",
    decoding: str = "async",
) -> str:
    entry = img_entry(path)
    variants = entry.get("variants") or {}
    src = entry["src"]
    if variants:
        src = variants.get("800") or variants.get("1200") or list(variants.values())[-1]
    attrs: list[str] = []
    if klass:
        attrs.append(f'class="{esc(klass)}"')
    attrs.append(f'alt="{esc(alt)}"')
    if variants:
        parts = [f"{esc(variants[w])} {w}w" for w in sorted(variants, key=int)]
        attrs.append(f'srcset="{", ".join(parts)}"')
        attrs.append(f'sizes="{esc(sizes)}"')
    attrs.append(f'src="{esc(src)}"')
    w = width or entry.get("width")
    h = height or entry.get("height")
    if w:
        attrs.append(f'width="{w}"')
    if h:
        attrs.append(f'height="{h}"')
    if loading:
        attrs.append(f'loading="{loading}"')
    if fetchpriority:
        attrs.append(f'fetchpriority="{fetchpriority}"')
    attrs.append(f'decoding="{decoding}"')
    return f"<img {' '.join(attrs)} />"


def lcp_preload_href(path: str) -> str:
    entry = img_entry(path)
    variants = entry.get("variants") or {}
    return variants.get("1200") or variants.get("800") or entry["src"]


def rewrite_html_images(fragment: str, *, sizes: str = CARD_SIZES) -> str:
    """Replace raw <img> tags with responsive webp markup."""

    def upgrade(match: re.Match[str]) -> str:
        tag = match.group(0)
        src_m = re.search(r'src=["\']([^"\']+)["\']', tag, re.I)
        if not src_m:
            return tag
        alt_m = re.search(r'alt=["\']([^"\']*)["\']', tag, re.I)
        alt = alt_m.group(1) if alt_m else ""
        loading_m = re.search(r'loading=["\']([^"\']+)["\']', tag, re.I)
        loading = loading_m.group(1) if loading_m else "lazy"
        return img_responsive(src_m.group(1), alt, sizes=sizes, loading=loading)

    return re.sub(r"<img\b[^>]*/?>", upgrade, fragment, flags=re.I)


def write(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if BASE and rel.endswith((".html",)):
        # Rewrite root-absolute URLs for project Pages hosting
        content = content.replace('href="/', f'href="{BASE}/')
        content = content.replace("href='/", f"href='{BASE}/")
        content = content.replace('src="/', f'src="{BASE}/')
        content = content.replace("src='/", f"src='{BASE}/")
        content = content.replace('data-bg="/', f'data-bg="{BASE}/')
        content = content.replace('content="/', f'content="{BASE}/')

        def _prefix_srcset(match: re.Match[str]) -> str:
            inner = re.sub(
                r"(/assets/[^\s,]+)",
                lambda u: f"{BASE}{u.group(1)}",
                match.group(1),
            )
            return f'srcset="{inner}"'

        content = re.sub(r'srcset="([^"]+)"', _prefix_srcset, content)
        content = content.replace('url(/', f"url({BASE}/")
        content = content.replace(
            'action="https://formspree.io',
            'action="https://formspree.io',
        )
    path.write_text(content, encoding="utf-8")
    print("wrote", rel)


def _label(text: str, *, required: bool = False) -> str:
    mark = '<span class="req" aria-hidden="true">*</span>' if required else ""
    return f'<span class="form-label-text">{text}{mark}</span>'


def _req(text: str) -> str:
    return _label(text, required=True)


def _form_hidden() -> str:
    return f"""  <input type="hidden" name="_next" value="{DOMAIN}/thank-you/" />
  <input type="hidden" name="_subject" value="New estimate request — Breaking Ground" />
  <input type="hidden" name="page" value="" />"""


def _form_required_note(klass: str = "") -> str:
    extra = f" {klass}" if klass else ""
    return f'<p class="form-required-note{extra}"><span class="req" aria-hidden="true">*</span> Required</p>'


def estimate_form(default_service: str = "") -> str:
    opts = "\n".join(
        f'<option value="{esc(s["navLabel"])}"{" selected" if s["navLabel"] == default_service else ""}>{esc(s["navLabel"])}</option>'
        for s in SERVICES
    )
    return f"""
<form class="form-grid" data-bg-form method="POST" action="{esc(FORM)}" enctype="multipart/form-data">
{_form_hidden()}
  <label>{_req("Name")}<input name="name" required autocomplete="name" /></label>
  <label>{_req("Phone")}<input name="phone" type="tel" required autocomplete="tel" /></label>
  <label>{_label("Email")}<input name="email" type="email" autocomplete="email" /></label>
  <label>{_req("Job location / city")}<input name="job_location" required /></label>
  <label>{_req("Service needed")}
    <select name="service" required>
      <option value="">Select a service</option>
      {opts}
      <option value="Other">Other</option>
    </select>
  </label>
  <label>{_label("Project details")}<textarea name="message" placeholder="Structure type, acreage, access notes…"></textarea></label>
  <label>{_label("Best time to call")}<input name="best_time" /></label>
  <label>{_req("Can we text you for photos?")}
    <select name="can_text_photos" required>
      <option value="Yes">Yes</option>
      <option value="No">No</option>
    </select>
  </label>
  <label>{_label("Photos (optional)")}<input name="photos" type="file" accept="image/*" multiple /></label>
  <button class="btn btn-primary" type="submit">Request Free Estimate</button>
  <p class="form-note">Estimates are free and informational. Final pricing is confirmed in writing before work begins.</p>
  {_form_required_note()}
</form>"""


def estimate_form_hero() -> str:
    """Homepage hero — minimal fields."""
    return f"""
<form class="form-grid form-grid--hero" data-bg-form method="POST" action="{esc(FORM)}">
{_form_hidden()}
  <label>{_req("Name")}<input name="name" required autocomplete="name" placeholder="Your name" /></label>
  <label>{_req("Phone")}<input name="phone" type="tel" required autocomplete="tel" placeholder="{esc(PHONE)}" /></label>
  <label>{_req("Job location / city")}<input name="job_location" required autocomplete="address-level2" placeholder="City or address area" /></label>
  <label>{_req("What do you need?")}<textarea name="message" rows="2" required placeholder="e.g. singlewide demo in Lakeland"></textarea></label>
  <button class="btn btn-primary" type="submit">Get Free Estimate</button>
  <p class="form-note">Or call <a href="tel:{PHONE_TEL}">{esc(PHONE)}</a>. Photos by text speed up estimates.</p>
  {_form_required_note(" form-required-note--hero")}
</form>"""


def estimate_form_contact() -> str:
    """Short contact-page form — fewer fields, faster to complete."""
    opts = "\n".join(
        f'<option value="{esc(s["navLabel"])}">{esc(s["navLabel"])}</option>'
        for s in SERVICES
    )
    return f"""
<form class="form-grid form-grid--area" data-bg-form method="POST" action="{esc(FORM)}">
{_form_hidden()}
  <div class="form-grid__row">
    <label>{_req("Name")}<input name="name" required autocomplete="name" placeholder="Your name" /></label>
    <label>{_req("Phone")}<input name="phone" type="tel" required autocomplete="tel" placeholder="{esc(PHONE)}" /></label>
  </div>
  <label>{_req("Job location / city")}<input name="job_location" required autocomplete="address-level2" placeholder="City or address area" /></label>
  <label>{_req("Service needed")}
    <select name="service" required>
      <option value="">Select a service</option>
      {opts}
      <option value="Other">Other</option>
    </select>
  </label>
  <label>{_req("What do you need?")}<textarea name="message" rows="3" required placeholder="Structure type, access, timeline…"></textarea></label>
  <button class="btn btn-primary" type="submit">Get Free Estimate</button>
  <p class="form-note">Or call <a href="tel:{PHONE_TEL}">{esc(PHONE)}</a>. Text photos for a faster quote.</p>
  {_form_required_note()}
</form>"""


def estimate_form_compact(default_service: str = "") -> str:
    opts = "\n".join(
        f'<option value="{esc(s["navLabel"])}"{" selected" if s["navLabel"] == default_service else ""}>{esc(s["navLabel"])}</option>'
        for s in SERVICES
    )
    return f"""
<form class="form-grid form-grid--hero" data-bg-form method="POST" action="{esc(FORM)}">
{_form_hidden()}
  <label>{_req("Name")}<input name="name" required autocomplete="name" placeholder="Your name" /></label>
  <label>{_req("Phone")}<input name="phone" type="tel" required autocomplete="tel" placeholder="{esc(PHONE)}" /></label>
  <label>{_req("Job location / city")}<input name="job_location" required placeholder="City or address area" /></label>
  <label>{_req("Service needed")}
    <select name="service" required>
      <option value="">Select a service</option>
      {opts}
      <option value="Other">Other</option>
    </select>
  </label>
  <label>{_req("What do you need?")}<textarea name="message" rows="2" required placeholder="Structure type, access, timeline…"></textarea></label>
  <button class="btn btn-primary" type="submit">Get Free Estimate</button>
  <p class="form-note">Or call <a href="tel:{PHONE_TEL}">{esc(PHONE)}</a>. Photos by text speed up quotes.</p>
  {_form_required_note(" form-required-note--hero")}
</form>"""


def estimate_form_area(city: str = "", default_service: str = "Mobile Home Demolition") -> str:
    """Short sticky-sidebar form for service area pages."""
    opts = "\n".join(
        f'<option value="{esc(s["navLabel"])}"{" selected" if s["navLabel"] == default_service else ""}>{esc(s["navLabel"])}</option>'
        for s in SERVICES
    )
    loc = city.strip()
    loc_value = f' value="{esc(loc)}"' if loc else ""
    loc_ph = esc(f"{loc}, FL" if loc else "City or address area")
    return f"""
<form class="form-grid form-grid--area" data-bg-form method="POST" action="{esc(FORM)}">
{_form_hidden()}
  <div class="form-grid__row">
    <label>{_req("Name")}<input name="name" required autocomplete="name" placeholder="Your name" /></label>
    <label>{_req("Phone")}<input name="phone" type="tel" required autocomplete="tel" placeholder="{esc(PHONE)}" /></label>
  </div>
  <label>{_req("Job location")}<input name="job_location" required autocomplete="address-level2" placeholder="{loc_ph}"{loc_value} /></label>
  <label>{_req("Service needed")}
    <select name="service" required>
      <option value="">Select a service</option>
      {opts}
      <option value="Other">Other</option>
    </select>
  </label>
  <label>{_req("What do you need?")}<textarea name="message" rows="2" required placeholder="e.g. singlewide demo, stump removal…"></textarea></label>
  <button class="btn btn-primary" type="submit">Get Free Estimate</button>
  <p class="form-note">Or call <a href="tel:{PHONE_TEL}">{esc(PHONE)}</a>. Text photos for a faster quote.</p>
  {_form_required_note()}
</form>"""


def schema_business(extra: list | None = None) -> str:
    graph = [
        {
            "@type": ["Organization", "LocalBusiness", "HomeAndConstructionBusiness"],
            "@id": f"{DOMAIN}/#business",
            "name": SHORT,
            "legalName": LEGAL,
            "url": DOMAIN,
            "telephone": PHONE_TEL,
            "email": EMAIL,
            "foundingDate": SITE["foundingYear"],
            "description": SITE["tagline"],
            "image": DOMAIN + OG,
            "logo": {"@type": "ImageObject", "url": DOMAIN + LOGO},
            "priceRange": SITE["priceRange"],
            "openingHours": SITE["hours"],
            "address": {
                "@type": "PostalAddress",
                **SITE["address"],
            },
            "geo": {
                "@type": "GeoCoordinates",
                **SITE["geo"],
            },
            "areaServed": "Florida",
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": REVIEWS.get("ratingValue", 5),
                "reviewCount": REVIEWS.get("reviewCount", len(REVIEWS.get("reviews") or [])),
                "bestRating": 5,
                "worstRating": 1,
            },
            "contactPoint": {
                "@type": "ContactPoint",
                "telephone": PHONE_TEL,
                "email": EMAIL,
                "contactType": "customer service",
                "areaServed": "US-FL",
                "availableLanguage": "English",
            },
        }
    ]
    if extra:
        graph.extend(extra)
    payload = {"@context": "https://schema.org", "@graph": graph}
    return f'<script type="application/ld+json">\n{json.dumps(payload, indent=2)}\n</script>'


def chrome_partial(name: str) -> str:
    """Read header/footer and apply siteBase for inlined chrome."""
    text = (ROOT / name).read_text(encoding="utf-8")
    if BASE:
        text = re.sub(rf"(?:{re.escape(BASE)})+/", "/", text)
        text = text.replace('href="/', f'href="{BASE}/')
        text = text.replace('src="/', f'src="{BASE}/')
    return text.strip()


def head(
    title: str,
    description: str,
    canonical: str,
    *,
    og_image: str | None = None,
    breadcrumbs: list[tuple[str, str]] | None = None,
    extra_schema: list | None = None,
    lcp_preload: str | None = None,
) -> str:
    img = DOMAIN + best_webp(og_image or OG)
    can = canonical if canonical.startswith("http") else DOMAIN + canonical
    crumbs = breadcrumbs or [("Home", "/")]
    crumb_schema = {
        "@type": "BreadcrumbList",
        "@id": can + "#breadcrumb",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": DOMAIN + u}
            for i, (n, u) in enumerate(crumbs)
        ],
    }
    extras = list(extra_schema or [])
    extras.append(crumb_schema)
    preload = ""
    if lcp_preload:
        preload = (
            f'  <link rel="preload" as="image" href="{esc(lcp_preload_href(lcp_preload))}" '
            f'fetchpriority="high" />\n'
        )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}" />
  <link rel="canonical" href="{esc(can)}" />
  <link rel="sitemap" type="application/xml" title="Sitemap" href="{DOMAIN}/sitemap.xml" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1" />
  <meta name="author" content="{esc(LEGAL)}" />
  <meta name="geo.region" content="US-FL" />
  <meta name="geo.placename" content="Kathleen, Florida" />
  <meta name="geo.position" content="{SITE['geo']['latitude']};{SITE['geo']['longitude']}" />
  <meta name="ICBM" content="{SITE['geo']['latitude']}, {SITE['geo']['longitude']}" />
  <meta name="theme-color" content="#0f172a" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{esc(can)}" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(description)}" />
  <meta property="og:image" content="{esc(img)}" />
  <meta property="og:site_name" content="{esc(SHORT)}" />
  <meta property="og:locale" content="en_US" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(title)}" />
  <meta name="twitter:description" content="{esc(description)}" />
  <meta name="twitter:image" content="{esc(img)}" />
  <link rel="icon" href="/favicon.ico" sizes="any" />
  <link rel="icon" type="image/png" sizes="192x192" href="/assets/icons/cropped-Logo-Square-192x192.png" />
  <link rel="apple-touch-icon" href="/assets/icons/cropped-Logo-Square-192x192.png" />
  <link rel="alternate" type="text/plain" href="/llms.txt" title="LLM site summary" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Source+Sans+3:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet" />
  {preload}  <link rel="stylesheet" href="/assets/css/style.css?v=nav3" />
  {schema_business(extras)}
</head>
<body>
  {chrome_partial("header.html")}
  <main id="main-content">
"""


def foot() -> str:
    return f"""
  </main>
  {chrome_partial("footer.html")}
  <script src="/includes.js?v=nav2" defer></script>
  <script src="/assets/js/main.js?v=reveal3" defer></script>
</body>
</html>
"""


def _review_stars(count: int = 5) -> str:
    n = max(1, min(5, int(count or 5)))
    return "&#9733;" * n


def _review_card(review: dict, index: int) -> str:
    name = review.get("name") or "Google User"
    meta = review.get("meta") or "Google review"
    colors = ["#1a56c4", "#c0392b", "#1e6b2e", "#FBBC05", "#0f766e", "#7c3aed"]
    bg = review.get("avatarColor") or colors[index % len(colors)]
    text_style = ' style="color:#0f172a;"' if bg.lower() == "#fbbc05" else ""
    initial = esc(name.strip()[:1].upper() or "?")
    stars = int(review.get("stars") or 5)
    return f"""
<article class="bg-review-card">
  <div class="bg-review-header">
    <span class="bg-review-avatar" style="background:{esc(bg)};"{text_style} aria-hidden="true">{initial}</span>
    <div>
      <h3 class="bg-review-name">{esc(name)}</h3>
      <div class="bg-review-sub">{esc(meta)}</div>
    </div>
  </div>
  <div class="bg-stars" role="img" aria-label="{stars} stars">{_review_stars(stars)}</div>
  <p class="bg-review-text">{esc(review.get("text") or "")}</p>
  <div class="bg-review-date">{esc(review.get("date") or "")}</div>
</article>"""


def local_trust_section() -> str:
    """Static Google reviews carousel + map embed (Knight Group pattern, no live GBP feed)."""
    reviews = REVIEWS.get("reviews") or []
    rating = float(REVIEWS.get("ratingValue") or 5)
    count = int(REVIEWS.get("reviewCount") or len(reviews) or 0)
    cards = "".join(_review_card(r, i) for i, r in enumerate(reviews))
    return f"""
  <section class="section-pad bg-local-trust" id="reviews" aria-label="Google reviews and map">
    <div class="container">
      <p class="section-eyebrow">Local Trust</p>
      <h2>Google reviews and map proof across Central Florida</h2>
      <div class="bg-map-review-shell">
        <div class="bg-google-reviews-showcase" aria-label="Customer Reviews">
          <div class="bg-google-reviews-header">
            <svg class="bg-google-g-logo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" aria-hidden="true" focusable="false">
              <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
              <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
              <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
              <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
            </svg>
            <span>Google Reviews</span>
            <div class="bg-google-stars-display" role="img" aria-label="5 star rating">&#9733;&#9733;&#9733;&#9733;&#9733;</div>
            <div class="bg-google-reviews-summary" id="bg-review-summary">{rating:.1f} &middot; {count} reviews</div>
          </div>
          <div class="bg-review-carousel-wrapper">
            <button class="bg-review-carousel-btn" type="button" id="bg-review-prev" aria-label="Previous reviews">&#8249;</button>
            <div class="bg-review-carousel-track-outer">
              <div class="bg-review-carousel-track" id="bg-review-track">{cards}
              </div>
            </div>
            <button class="bg-review-carousel-btn" type="button" id="bg-review-next" aria-label="Next reviews">&#8250;</button>
          </div>
          <div class="bg-review-carousel-dots" id="bg-review-dots" role="group" aria-label="Google review pages"></div>
          <p class="bg-google-review-links">
            <a href="{esc(GOOGLE_MAPS_URL)}" target="_blank" rel="noopener noreferrer">See our Google profile</a>
            <span aria-hidden="true">&middot;</span>
            <a href="{esc(GOOGLE_MAPS_URL)}" target="_blank" rel="noopener noreferrer">Leave a review</a>
          </p>
        </div>
        <div class="bg-map-panel is-map-loaded" id="bg-map-shell" aria-label="Breaking Ground Google map">
          <iframe class="bg-map-frame" id="bg-map-frame" title="Breaking Ground Land Services and Demolition on Google Maps" width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" src="{esc(MAP_EMBED_SRC)}"></iframe>
          <div class="bg-map-overlay">
            <strong>{esc(NAME)}</strong>
            <span class="bg-map-rating" aria-label="{rating:.1f} out of 5 stars, {count} Google reviews">&#9733;&#9733;&#9733;&#9733;&#9733; {rating:.1f} &middot; {count} Google reviews</span>
            <span>Kathleen, FL &bull; Central Florida service area</span>
          </div>
        </div>
      </div>
    </div>
  </section>
"""


def page_hero(
    h1: str,
    crumbs_html: str,
    image: str = "",
    lead: str = "",
    *,
    with_media: bool = True,
    image_alt: str = "",
    image_credit: str = "",
) -> str:
    lead_html = f"<p class=\"hero-lead\">{esc(lead)}</p>" if lead else ""
    compact = not with_media or not image
    media_html = ""
    if not compact:
        alt = image_alt or h1
        credit_html = (
            f'<p class="page-hero__credit">{esc(image_credit)}</p>' if image_credit else ""
        )
        media_html = f"""
    <div class="page-hero__media">{img_responsive(image, alt, sizes=PAGE_HERO_SIZES, loading="eager", width=1600, height=900)}</div>
    <div class="page-hero__overlay"></div>
    {credit_html}"""
    klass = "page-hero page-hero--compact" if compact else "page-hero"
    return f"""
  <section class="{klass}">
    {media_html}
    <div class="page-hero__copy">
      <div class="breadcrumbs">{crumbs_html}</div>
      <h1>{esc(h1)}</h1>
      {lead_html}
    </div>
  </section>"""


def related_links(current: str = "") -> str:
    """Dense internal linking block used across content pages."""
    service_links = [
        ("/demolition/", "Demolition"),
        ("/mobile-home-demolition/", "Mobile Home Demolition"),
        ("/shed-barn-removal/", "Shed & Barn Removal"),
        ("/land-clearing/", "Land Clearing"),
        ("/tree-removal/", "Tree Removal"),
        ("/stump-removal/", "Stump Removal"),
        ("/pond-drainage/", "Pond & Drainage"),
        ("/grading-site-preparation/", "Grading & Site Prep"),
        ("/storm-debris-cleanup/", "Storm Cleanup"),
    ]
    extra_links = [
        ("/projects/", "Project Gallery"),
        ("/pricing/", "Pricing Guide"),
        ("/service-areas/", "Service Areas"),
        ("/areas/kathleen-fl/", "Kathleen"),
        ("/areas/lakeland-fl/", "Lakeland"),
        ("/areas/plant-city-fl/", "Plant City"),
        ("/areas/brooksville-fl/", "Brooksville"),
        ("/areas/tampa-fl/", "Tampa"),
        ("/about/", "About Us"),
        ("/contact/", "Request Estimate"),
    ]
    items = []
    for href, label in service_links + extra_links:
        if href.rstrip("/") == current.rstrip("/"):
            continue
        items.append(f'<a href="{esc(href)}">{esc(label)}</a>')
    grid = "\n".join(f"<div>{a}</div>" for a in items[:18])
    return f"""
<aside class="related-links reveal">
  <h3>Explore related pages</h3>
  <p>Jump to another service, city, or project page on this site.</p>
  <div class="related-links-grid">{grid}</div>
</aside>
"""


def cta_band(headline: str, blurb: str, service: str = "") -> str:
    return f"""
  <section class="cta-band cta-band--parallax" data-parallax-band aria-label="Request an estimate">
    <div class="cta-band__bg" aria-hidden="true">
      {img_responsive("/assets/images/projects/IMG_9164-scaled.jpg", "", sizes=HERO_SIZES, width=1600, height=1200)}
    </div>
    <div class="cta-band__overlay" aria-hidden="true"></div>
    <div class="container cta-band__inner">
      <div class="cta-band__copy reveal">
        <p class="section-eyebrow">Next step</p>
        <h2>{esc(headline)}</h2>
        <p class="cta-band__lede">{esc(blurb)}</p>
        <ul class="cta-band__points" aria-label="What to expect">
          <li><span class="cta-band__mark" aria-hidden="true">01</span><span><strong>Free scope call</strong> — tell us about the structure, lot access, and your city.</span></li>
          <li><span class="cta-band__mark" aria-hidden="true">02</span><span><strong>Photos help</strong> — text gate widths, overhead lines, and debris piles for faster quotes.</span></li>
          <li><span class="cta-band__mark" aria-hidden="true">03</span><span><strong>Written confirmation</strong> — pricing and teardown scope agreed before work starts.</span></li>
        </ul>
        <div class="cta-band__actions">
          <a class="btn btn-primary" href="tel:{PHONE_TEL}">Call {esc(PHONE)}</a>
          <a class="btn btn-ghost" href="/contact/">Full estimate form</a>
        </div>
      </div>
      <aside class="cta-band__form hero-card reveal" aria-label="Quick estimate request">
        <p class="hero-card__eyebrow">Free Estimate</p>
        <h3 class="hero-card__title">Talk to the owners</h3>
        <p class="hero-card__note">Quick form — Guy or Andrew will follow up by phone or text.</p>
        {estimate_form_compact(service)}
      </aside>
    </div>
  </section>"""


def crumb(items: list[tuple[str, str]]) -> str:
    parts = []
    for i, (label, url) in enumerate(items):
        if i < len(items) - 1:
            parts.append(f'<a href="{esc(url)}">{esc(label)}</a>')
        else:
            parts.append(f"<span>{esc(label)}</span>")
    return " / ".join(parts)


# ── Content builders ──────────────────────────────────────────────


def service_body(svc: dict) -> str:
    slug = svc["slug"]
    bodies = {
        "demolition": """
<p>Breaking Ground focuses on <strong>smaller demolition and structure removal</strong> for homeowners, investors, and property managers across Central Florida. We take down mobile homes, sheds, barns, decks, and similar light structures, then haul the debris so your lot is ready for the next chapter.</p>
<p>We are an owner-operated father-and-son crew based in Kathleen. Andrew brings decades of heavy-equipment experience; Guy handles project coordination and customer communication. You work directly with the people running the machines — not a call center.</p>
<p>Permit requirements vary by property, structure, and jurisdiction. Polk County and many Florida cities require a demolition permit for structure removal. We evaluate each project individually and coordinate required permitting based on the scope of work. We do not perform asbestos abatement; if regulated materials are discovered, work pauses until qualified specialty contractors handle them.</p>
<h3>What we demolish and remove</h3>
<ul>
<li>Mobile homes and manufactured homes (singlewide and doublewide)</li>
<li>Sheds, barns, and outbuildings</li>
<li>Decks, porches, and carports attached to light structures</li>
<li>Storm-damaged or fire-damaged light structures (case by case)</li>
<li>Debris piles left after prior teardown attempts</li>
</ul>
<h3>What this service is not</h3>
<p>We do not market unrestricted commercial high-rise demolition or large engineered building teardown as a general contracting specialty. If your project involves a complex occupied structure, hazardous materials, or specialized engineering, we will say so clearly and help you understand next steps.</p>
<h3>Our typical process</h3>
<ol>
<li>Phone or form estimate with photos and site details</li>
<li>On-site walk-through when needed</li>
<li>Written scope covering teardown, haul-off, and grading expectations</li>
<li>Utility disconnect confirmation and permit coordination as required</li>
<li>Demolition, debris removal, and final cleanup</li>
</ol>
""",
        "mobile-home-demolition": """
<p>Mobile home and manufactured home removal is our priority service. Aging parks, inherited lots, storm-damaged units, and rebuild sites across Florida often start with a clean, complete demo and haul-off — and that is exactly the work we are built for.</p>
<p>Whether you have a vacant singlewide in Polk County or a doublewide that needs to come down before new construction, Breaking Ground brings equipment, hauling capacity, and owner-level accountability to the job.</p>
<p>Florida continues to see elevated teardown and redevelopment activity. Property owners clearing older housing stock for rebuilds or land sales need a crew that can remove the structure, manage debris, and leave a usable pad — without overpromising on scopes we do not perform.</p>
<h3>What affects mobile home demo pricing</h3>
<ul>
<li>Singlewide vs doublewide vs multi-section</li>
<li>Access roads, trees, and neighboring structures</li>
<li>Foundation type (pier, block, slab)</li>
<li>Attached porches, carports, and decks</li>
<li>Utility disconnect status</li>
<li>Disposal fees and haul distance</li>
<li>Permit and notification requirements in your city or county</li>
</ul>
<p>Ballpark ranges on our <a href="/pricing/">pricing page</a> help set expectations. Every job still needs a written estimate after we understand the site.</p>
<h3>Permits and utilities</h3>
<p>Most Florida jurisdictions require a demolition permit for manufactured home removal. Utility disconnection (electric, water, sewer/septic) must be confirmed before teardown. We discuss who pulls permits and who coordinates disconnects before work starts so responsibilities are clear.</p>
""",
        "shed-barn-removal": """
<p>Outdated sheds, leaning barns, and unused outbuildings take up space and create liability. Breaking Ground removes these structures, hauls the debris, and cleans the footprint so you can reclaim the yard or prepare for a new build.</p>
<p>Backyard access is often the hard part. We plan equipment selection around gates, fences, and overhead lines so the job finishes without unnecessary property damage.</p>
<h3>Common projects</h3>
<ul>
<li>Residential storage sheds and workshops</li>
<li>Agricultural barns and lean-tos</li>
<li>Carports and detached covered structures</li>
<li>Collapsed or storm-damaged outbuildings</li>
</ul>
<p>If concrete pads or footings need removal, we discuss that as a separate line item so your scope stays transparent.</p>
""",
        "land-clearing": """
<p>Need a wooded lot opened for a home site, driveway, or pasture? Breaking Ground provides residential and light-commercial land clearing, brush removal, and lot cleanup throughout Polk County and nearby Central Florida communities.</p>
<p>We clear vegetation, remove underbrush, and help get ground ready for the next step — whether that is grading, a building pad, or simply usable open land. Project photos from Brooksville and surrounding areas show the kind of dense Florida scrub we regularly handle.</p>
<p>For specialized forestry mulching programs in core Auburndale and Winter Haven markets, we may refer complementary partners when that approach better fits the property. Our strength is equipment-driven clearing combined with demolition and haul-off when structures are also in the way.</p>
<h3>Land clearing services</h3>
<ul>
<li>Residential lot clearing</li>
<li>Brush and overgrowth removal</li>
<li>Fence-line and trail opening</li>
<li>Build-site vegetation removal</li>
<li>Debris haul-off after clearing</li>
</ul>
""",
        "tree-removal": """
<p>From unwanted backyard trees to storm-fallen timber, Breaking Ground provides tree removal and equipment-assisted cleanup for Central Florida properties. We focus on practical removals where heavy equipment can safely access the work zone.</p>
<p>Hazardous trees over occupied structures or crane-assisted specialty removals may require additional partners. We will tell you honestly when a job needs different equipment or a climbing crew.</p>
<h3>Tree work we perform</h3>
<ul>
<li>Full tree removal with equipment support</li>
<li>Fallen tree cleanup after storms</li>
<li>Lot clearing tree removal tied to build prep</li>
<li>Log and brush haul-off</li>
</ul>
""",
        "stump-removal": """
<p>Stump grinding leaves roots behind. When you need the stump and root ball gone so you can grade, plant, fence, or build, excavation is the better answer. Breaking Ground digs stumps out, hauls the mass away, and leaves a usable hole ready for backfill — throughout Lakeland, Kathleen, and Polk County.</p>
<p>Our project photos show full stump removal: before, digging, carrying, loading, and after. That is different from a ground-out stump that still owns the yard. If you have been quoted grinding only, ask what happens to the roots — then compare it to excavation.</p>
<h3>What full stump removal includes</h3>
<ul>
<li>Excavating the stump and major root mass</li>
<li>Loading and hauling stump material to disposal</li>
<li>Backfill expectations stated in the written scope</li>
<li>Honest guidance when grinding is enough for cosmetics only</li>
</ul>
""",
        "pond-drainage": """
<p>Property owners call us for ponds when they want livestock water, irrigation buffering, wildlife habitat, a family water feature, or a practical wet area that will not wash out after the first Florida storm. Breaking Ground excavates and shapes ponds, builds berms, stages spoil, and installs drainage and aeration details that keep the finished basin usable.</p>
<p>We know this work. Empty-basin earthwork, slope geometry, berm height, overflow pipe, and spoil placement are sequenced on purpose — not guessed on site. If your lot needs a farm pond, ornamental basin, or drainage-related earthwork, we walk the goals first, then dig to a written scope.</p>
<h3>Why customers dig a pond</h3>
<ul>
<li>Livestock or pasture water on acreage</li>
<li>Irrigation buffering and groundwater access</li>
<li>Wildlife habitat and a usable water feature for the family</li>
<li>Managing low spots and storm runoff with intentional banks and berms</li>
</ul>
<h3>What we deliver on pond jobs</h3>
<ul>
<li>Defined pond geometry with intentional slopes</li>
<li>Berm and high-side protection against washouts</li>
<li>Drainage / overflow detailing when the site needs it</li>
<li>Spoil management — berms, grading, or landscape features instead of abandoned piles</li>
<li>Aerator install when Florida heat and algae risk call for it</li>
</ul>
<p>Wetlands, surface-water connections, and local rules can change scope. We flag those conditions early and coordinate permitting based on the job — while staying focused on excavation and earthwork, not engineered drainage design.</p>
""",
        "grading-site-preparation": """
<p>Home builders, developers, and GC teams need a lot that is ready for the next trade — not a leftover demo pile or uneven clearing scar. Breaking Ground provides rough grading and site preparation after demolition or clearing so builders can mobilize pads, driveways, and foundations without reworking our mess.</p>
<p>We are an owner-operated father-and-son crew. Guy and Andrew handle estimates and equipment directly, which keeps communication short when you are sequencing subcontractors on a Central Florida build schedule.</p>
<h3>Builder-focused site prep</h3>
<ul>
<li>Rough grade after mobile-home or structure demolition</li>
<li>Fill placement and spreading for workable pads</li>
<li>Shaping disturbed ground so water drains away from future building areas</li>
<li>Driveway and access prep support for material deliveries</li>
<li>Combined scopes: demo + clear + grade in one mobilization when the lot allows</li>
</ul>
<h3>What builders should send for a fast quote</h3>
<ul>
<li>Address or subdivision, gate width, and overhead line notes</li>
<li>Pad / building footprint goals and any survey stakes already on site</li>
<li>Whether demolition or clearing is still needed before grade</li>
<li>Timeline for foundation or shell crews</li>
</ul>
<p>Project-specific grading photos will be added as those jobs are documented. Until then, this page shows the crew and equipment that show up for builder site work — and the scope language you can put in front of your superintendent.</p>
""",
        "storm-debris-cleanup": """
<p>Hurricanes and seasonal storms leave yards buried in limbs, sheets of debris, and downed trees. Breaking Ground provides storm debris cleanup and haul-off for Polk County and Central Florida property owners who need a crew that shows up with equipment and leaves the site clear.</p>
<p>The photos on this page come from a real storm tree cleanup job — cutting, processing, stump work, and follow-up — not unrelated clearing galleries. After major storm events, schedule can tighten quickly. Contact us early with photos so we can prioritize access, safety, and disposal logistics.</p>
""",
    }
    base = bodies.get(slug, f"<p>{esc(svc['meta'])}</p>")
    faqs = f"""
<div class="faq">
  <details open><summary>Do you offer free estimates?</summary><p>Yes. Estimates are free. Final pricing is confirmed in a written scope before work begins.</p></details>
  <details><summary>Do you handle permits?</summary><p>Permit requirements vary by jurisdiction and structure. We evaluate each project and coordinate required permitting based on the scope of work.</p></details>
  <details><summary>Where do you work?</summary><p>We are based in Kathleen and serve Central Florida routinely. Larger demolition and site jobs are considered statewide by project scope.</p></details>
  <details><summary>Are you a general contractor?</summary><p>No. We provide smaller demolition, structure removal, land clearing, and related site services as an owner-operated equipment company.</p></details>
</div>"""
    # Expand word count with process + CTA prose
    expand = f"""
<h3>Why property owners call {SHORT}</h3>
<p>Direct owner communication, real project photography, and a demolition-first mindset for the jobs Florida lots actually need — mobile homes, sheds, storm messes, and clearing that supports the next use of the land. Call <a href="tel:{PHONE_TEL}">{esc(PHONE)}</a> or use the form below.</p>
<p>Every estimate includes a clear description of what is included: teardown or clearing, debris handling, and what is excluded (such as hazardous material abatement or engineered design). That clarity protects both sides and keeps projects moving.</p>
<p>If your property needs both structure removal and land clearing, we can often combine scopes in one mobilization — reducing duplicate mobilizations and disposal trips. Ask about bundling when you request your estimate on our <a href="/contact/">contact page</a>, review <a href="/pricing/">pricing ranges</a>, or browse the <a href="/projects/">project gallery</a>.</p>
<p>Common next steps from this page: <a href="/mobile-home-demolition/">mobile home demolition</a>, <a href="/land-clearing/">land clearing</a>, <a href="/stump-removal/">stump removal</a>, <a href="/areas/lakeland-fl/">Lakeland</a>, <a href="/areas/kathleen-fl/">Kathleen</a>, and <a href="/service-areas/">all service areas</a>.</p>
{faqs}
"""
    return base + expand


def area_body(area: dict) -> str:
    short = area["shortName"]
    county = area["county"]
    angle = area.get("angle", "full")
    nearby = ", ".join(area.get("nearby", [])[:4])
    demo_lead = f"""
<p>Looking for <strong>mobile home demolition or light structure removal in {esc(short)}</strong>? Breaking Ground is an owner-operated crew based in Kathleen, Florida. We serve {esc(county)} and consider larger demolition jobs across the state by scope and schedule.</p>
<p>Florida property owners clearing aging manufactured homes, sheds, and outbuildings need a practical equipment crew — not marketing fluff. We provide written estimates, discuss permits, and haul debris so your {esc(short)} lot is ready for sale, rebuild, or cleanup.</p>
"""
    full_extra = f"""
<p>In addition to demolition, property owners in {esc(short)} also call us for land clearing, tree and stump removal, grading support, and storm debris cleanup. Demolition remains our lead specialty; clearing and earthwork are available when they fit the site.</p>
"""
    demo_only_note = f"""
<p>For {esc(short)}, our published focus is mobile-home and light-structure demolition plus related debris removal. Land clearing may be available as a secondary scope on the same property when it supports the demolition or lot reset.</p>
"""
    mid = full_extra if angle == "full" else demo_only_note
    return f"""
{demo_lead}
{mid}
<h3>Services commonly requested in {esc(short)}</h3>
<ul>
<li><a href="/mobile-home-demolition/">Mobile home demolition</a></li>
<li><a href="/demolition/">Small structure demolition</a></li>
<li><a href="/shed-barn-removal/">Shed and barn removal</a></li>
{"<li><a href='/land-clearing/'>Land clearing</a></li><li><a href='/stump-removal/'>Stump removal</a></li>" if angle == "full" else ""}
<li><a href="/storm-debris-cleanup/">Storm debris cleanup</a></li>
</ul>
<h3>Local context</h3>
<p>{esc(short)} sits in {esc(county)}. Nearby communities we also serve include {esc(nearby)}. Travel and scheduling for {esc(short)} jobs depend on project size — ask when you request your estimate.</p>
<p>Permit rules differ between cities and counties. Structure demolition often requires a local permit and utility disconnect confirmation. We review those requirements as part of scoping work in {esc(short)}.</p>
<h3>How to get started</h3>
<p>Send photos of the structure or lot, note gate widths and overhead lines, and tell us your goal (rebuild, sell, clean up). Call <a href="tel:{PHONE_TEL}">{esc(PHONE)}</a> or use the estimate form. Free estimates; written confirmation before work begins.</p>
<p>Breaking Ground Land Services and Demolition LLC was founded in 2024 by Guy and Andrew McMillen. Andrew has operated heavy equipment for decades. That experience shows up in how we plan access, sequence teardown, and leave sites cleaner than we found them.</p>
<div class="faq">
<details open><summary>Do you serve all of {esc(short)}?</summary><p>Yes — we consider jobs throughout {esc(short)} and surrounding {esc(county)}, subject to schedule and scope.</p></details>
<details><summary>Can you demolish a mobile home in {esc(short)}?</summary><p>Mobile home and manufactured home removal is our priority service. Share photos and location details for an estimate.</p></details>
<details><summary>Is land clearing available?</summary><p>{"Yes, land clearing and related site work are available in our Central Florida coverage area." if angle == "full" else "Land clearing may be offered as a secondary scope tied to demolition or lot reset. Ask when you request your estimate."}</p></details>
</div>
"""


def contact_body() -> str:
  service_links = "\n".join(
      f'<li><a href="{esc(s["path"])}">{esc(s["navLabel"])}</a> — {esc(s["meta"][:100])}…</li>'
      for s in SERVICES
  )
  return f"""
<p class="section-eyebrow">Contact</p>
<h2>Request a free demolition or land-services estimate</h2>
<p>Breaking Ground Land Services and Demolition LLC is an owner-operated equipment company based in Kathleen, Florida. Guy and Andrew McMillen handle estimates directly — no call center, no franchise script. When you call <a href="tel:{PHONE_TEL}">{esc(PHONE)}</a> or submit the short form on this page, you are reaching the people who will plan access, select equipment, and show up on your lot.</p>
<p><strong>Phone:</strong> <a href="tel:{PHONE_TEL}">{esc(PHONE)}</a><br/>
<strong>Email:</strong> <a href="mailto:{EMAIL}">{esc(EMAIL)}</a><br/>
<strong>Office:</strong> 4633 Clayton Road, Kathleen, FL 33849<br/>
<strong>Hours:</strong> Monday–Saturday, 7:00 a.m.–6:00 p.m.</p>

<h3>How free estimates work</h3>
<p>Every estimate starts with a conversation about what is on the property and what you want gone when we leave. That might be a singlewide mobile home, a leaning shed, a quarter-acre of brush, or a combination of structure removal and land clearing on the same lot. We do not charge for scoping calls or site visits within our normal Central Florida travel area, and we do not pressure you to book on the spot.</p>
<p>After we understand the job, we provide a written scope that lists what is included: teardown or clearing work, debris handling, haul-off, and any add-ons such as concrete pad removal or rough grading. Final pricing is confirmed in that scope before mobilization. If something changes once we are on site — buried concrete, extra structures, restricted access — we discuss it before doing additional work.</p>
<p>Estimates are informational until accepted in writing. That protects you from surprise line items and protects our schedule from jobs that were never clearly defined. If you are comparing contractors, ask each one whether haul-off, permit coordination, and utility disconnect planning are included. Those details change the real cost of a Florida demolition job.</p>

<h3>What to send for a faster quote</h3>
<p>Photos are the fastest way to narrow a price range. You do not need professional images — phone pictures taken from the street, driveway, or back gate are enough for a first pass. Helpful shots include:</p>
<ul>
<li>Wide views of the structure or lot from two angles</li>
<li>Gate width, fence lines, and anything overhead (power lines, tree limbs)</li>
<li>Interior photos for mobile homes if you can safely capture them</li>
<li>Debris piles, stumps, or brush density for clearing jobs</li>
<li>Driveway or access path equipment would use to reach the work zone</li>
</ul>
<p>Text photos to {esc(PHONE)} if that is easier than uploading. Mention your city or neighborhood, whether utilities are still connected, and your timeline (urgent storm cleanup vs. planning a sale six months out). The more honest you are about access constraints, the more accurate the first estimate will be.</p>

<h3>Services we quote every week</h3>
<p>Demolition is our lead specialty. Most estimate requests involve manufactured housing, sheds, barns, carports, and other light structures that need to come down before a lot can be sold, rebuilt, or cleared. We also provide land clearing, tree and stump work, pond and drainage earthwork support, grading after teardown, and storm debris haul-off when equipment access allows.</p>
<ul>
{service_links}
</ul>
<p>Browse individual service pages for scope details, project photos, and pricing context: <a href="/mobile-home-demolition/">mobile home demolition</a>, <a href="/shed-barn-removal/">shed &amp; barn removal</a>, <a href="/land-clearing/">land clearing</a>, and the full <a href="/services/">services hub</a>. Our <a href="/projects/">project gallery</a> shows real before-and-after work across Polk County and nearby communities.</p>

<h3>Where we work</h3>
<p>We are based in Kathleen and routinely serve Lakeland, Plant City, Winter Haven, Bartow, Mulberry, Zephyrhills, Brooksville, Tampa, and surrounding Central Florida communities. Polk County is our home base; Hillsborough, Pasco, Hernando, Orange, Osceola, and Marion counties are common travel zones for the right scope.</p>
<p>Larger demolition and multi-day site jobs are considered statewide when schedule and logistics allow. If you are outside our usual map, send the address area and photos anyway — we will tell you honestly whether travel and disposal costs make the job practical for both sides.</p>
<p>City-specific pages with local context and estimate forms are listed on our <a href="/service-areas/">service areas</a> hub, including <a href="/areas/kathleen-fl/">Kathleen</a>, <a href="/areas/lakeland-fl/">Lakeland</a>, and <a href="/areas/polk-county-fl/">Polk County</a>.</p>

<h3>What happens after you contact us</h3>
<p>When you submit the form or leave a voicemail, Guy or Andrew typically responds the same business day during normal hours. We may call back with clarifying questions, request additional photos, or schedule a walk-through if the site is local and access is unclear from pictures alone.</p>
<p>Once scope is agreed, we coordinate mobilization dates, permit steps if required, and utility disconnect timing for structure removals. Payment terms follow our published <a href="/payment-deposit-policy/">payment &amp; deposit policy</a>. We do not ask for full payment upfront on standard residential demolition work; deposits and progress milestones are spelled out in writing.</p>
<p>If we are not the right fit — specialty hazardous abatement, crane-only tree work, engineered drainage design — we will say so early rather than take a job we cannot execute safely.</p>

<h3>Permits, utilities, and realistic scope</h3>
<p>Florida jurisdictions differ on when a demolition permit is required for manufactured homes, sheds, and accessory structures. Utility disconnects (electric, water, sewer or septic) must be confirmed before teardown begins. We discuss who pulls permits and who coordinates disconnects as part of scoping so responsibilities are clear before work starts.</p>
<p>We are not a general contractor and do not provide architectural, engineering, or environmental consulting. We excavate, demolish, clear, haul, and grade within the limits of the written estimate. Wetlands, asbestos, and other regulated materials may require licensed specialists; we flag those conditions when photos or walk-throughs reveal them.</p>

<h3>Pricing context</h3>
<p>Ballpark ranges for common job types are published on our <a href="/pricing/">pricing guide</a>. Every property is different — access, debris volume, structure size, and disposal distance all move the number. The guide helps set expectations; your written estimate reflects the actual site.</p>
<p>Combining scopes in one mobilization often saves money. If you need a mobile home removed and the lot cleared afterward, or a shed demolished plus stumps excavated, mention both when you contact us so we can plan one equipment trip instead of two.</p>

<h3>Why property owners call the owners directly</h3>
<p>Breaking Ground was founded in 2024 by Guy and Andrew McMillen, but Andrew has operated heavy equipment since 1975. That field experience shows up in how we sequence teardown, protect driveways and fences when possible, and leave a pad or cleared footprint that matches what you told us you needed.</p>
<p>You will see real project photography throughout this site — not stock excavator clips. We prefer honest scopes over oversized promises. If you want a straight answer about whether your gate is wide enough, whether a permit is likely, or whether grinding vs. excavation is the right stump approach, call us.</p>

<div class="faq">
  <details open><summary>Do you offer free estimates?</summary><p>Yes. Estimates are free. Final pricing is confirmed in a written scope before work begins.</p></details>
  <details><summary>Can I text photos instead of using the form?</summary><p>Yes. Text photos and your city to <a href="tel:{PHONE_TEL}">{esc(PHONE)}</a>. Include gate width, overhead lines, and structure type for the fastest response.</p></details>
  <details><summary>How soon will you call back?</summary><p>During business hours we aim for same-day response. After storms or on heavy schedule weeks, allow 24–48 hours — we respond to every serious inquiry.</p></details>
  <details><summary>Do you handle permits?</summary><p>Permit requirements vary by jurisdiction and structure. We evaluate each project and coordinate required permitting based on the scope of work.</p></details>
  <details><summary>Are you a general contractor?</summary><p>No. We provide demolition, structure removal, land clearing, and related site services as an owner-operated equipment company.</p></details>
</div>
"""


# ── Page generators ───────────────────────────────────────────────


def build_home() -> None:
    tiles = "".join(
        f"""
        <a class="service-tile reveal" href="{esc(s['path'])}">
          {img_responsive(s['heroImage'], "", sizes=TILE_SIZES)}
          <div class="service-tile__body">
            <h3>{esc(s['navLabel'])}</h3>
            <p>{esc(s['meta'][:110])}…</p>
          </div>
        </a>"""
        for s in SERVICES[:6]
    )
    projects = "".join(
        f"""
        <article class="project-card reveal">
          <a href="{esc(p['path'])}">{img_responsive(p['image'], p['h1'], sizes=CARD_SIZES)}</a>
          <div class="project-card__body">
            <p class="project-meta">{esc(p['city'])} · {esc(p['service'])}</p>
            <h3><a href="{esc(p['path'])}">{esc(p['h1'])}</a></h3>
            <p>{esc(p['summary'])}</p>
          </div>
        </article>"""
        for p in PROJECTS[:4]
    )
    html_out = (
        head(
            f"{SHORT} | Mobile Home Demolition & Land Services in Central Florida",
            "Owner-operated mobile home demolition, shed removal, land clearing, and site work based in Kathleen, FL. Free estimates.",
            "/",
            breadcrumbs=[("Home", "/")],
            lcp_preload=LCP_HERO,
        )
        + f"""
  <section class="hero-stage">
    <div class="hero">
      <div class="hero-slides" aria-hidden="true">
        <div class="hero-slide active">
          {img_responsive(LCP_HERO, "Breaking Ground Land Services and Demolition — Guy and Andrew with excavator and dump trucks", sizes=HERO_SIZES, loading="eager", fetchpriority="high", klass="hero-slide-bg ken-burns hero-lcp-img", width=2400, height=1799)}
        </div>
        <div class="hero-slide">
          <div class="hero-slide-bg ken-burns" data-bg="{esc(best_webp('/assets/images/hero/IMG_8286-scaled.jpg'))}"></div>
        </div>
        <div class="hero-slide">
          <div class="hero-slide-bg ken-burns" data-bg="{esc(best_webp('/assets/images/hero/IMG_9083-scaled.jpg'))}"></div>
        </div>
      </div>
      <div class="hero__overlay"></div>
      <div class="hero__inner">
        <div class="hero__copy">
          <p class="hero-eyebrow">Kathleen · Lakeland · Central Florida</p>
          <h1>Breaking Ground</h1>
          <p class="hero-lead">Mobile home demolition, light structure removal, and land services — father-and-son owned, equipment ready.</p>
          <div class="hero__actions">
            <a class="btn btn-primary" href="/contact/">Request Free Estimate</a>
            <a class="btn btn-ghost" href="tel:{PHONE_TEL}">{esc(PHONE)}</a>
          </div>
        </div>
        <aside class="hero-card" aria-label="Request a free estimate">
          <p class="hero-card__eyebrow">Free Estimate</p>
          <h2 class="hero-card__title">Talk to the owners</h2>
          <p class="hero-card__note">Tell us about the structure or lot — we’ll follow up by phone or text.</p>
          {estimate_form_hero()}
        </aside>
      </div>
    </div>
  </section>
  <section class="section-pad">
    <div class="container split">
      <div class="reveal">
        <p class="section-eyebrow">Owner Operated</p>
        <h2>Demolition-first site work for Florida lots</h2>
        <div class="prose">
          <p>Breaking Ground Land Services and Demolition LLC clears the obstacles standing between you and usable land — starting with mobile homes, sheds, and light structures, then finishing with haul-off, clearing, and grading support when the job calls for it.</p>
          <p>Based in Kathleen and serving Central Florida, with larger demolition jobs considered statewide by scope.</p>
        </div>
        <ul class="feature-list">
          <li><span class="mark">01</span><span>Priority: mobile home &amp; light structure demolition</span></li>
          <li><span class="mark">02</span><span>Father-and-son crew — talk directly to the owners</span></li>
          <li><span class="mark">03</span><span>Real project photos from Polk County &amp; beyond</span></li>
        </ul>
      </div>
      <div class="media-stage reveal">{img_responsive("/assets/images/projects/IMG_8345-scaled.jpg", "Demolition and site work in progress", sizes=PAGE_HERO_SIZES)}</div>
    </div>
  </section>
  <section class="section-pad section-pad--muted">
    <div class="container">
      <p class="section-eyebrow">Services</p>
      <h2>What we take on</h2>
      <div class="service-grid">{tiles}</div>
      <div class="project-case__actions" style="margin-top:1.5rem;">
        <a class="btn btn-dark" href="/services/">View all services</a>
        <a class="btn btn-primary" href="/mobile-home-demolition/">Mobile Home Demolition</a>
      </div>
    </div>
  </section>
  {local_trust_section()}
  <section class="section-pad">
    <div class="container">
      <p class="section-eyebrow">Projects</p>
      <h2>Recent work</h2>
      <div class="project-grid">{projects}</div>
      <div class="project-case__actions" style="margin-top:1.5rem;">
        <a class="btn btn-dark" href="/projects/">Full project gallery</a>
        <a class="btn btn-primary" href="/areas/lakeland-fl/">Lakeland service area</a>
      </div>
      {related_links("/")}
    </div>
  </section>
"""
        + cta_band(
            "Ready to clear the structure or the lot?",
            "Tell us about your mobile home, shed, or land clearing project. Free estimates for Central Florida and statewide-by-scope jobs.",
            "Mobile Home Demolition",
        )
        + foot()
    )
    write("index.html", html_out)


def build_about() -> None:
    about_photo = "/assets/images/brand/guy-and-andrew-glasses.jpg"
    body = f"""
{page_hero("About Breaking Ground", crumb([("Home","/"),("About","/about/")]), about_photo, "Father-and-son. Equipment-driven. Built in 2024 on decades of field experience.")}
<section class="section-pad"><div class="container split">
<div class="prose reveal">
<p class="section-eyebrow">Our Story</p>
<h2>Guy &amp; Andrew McMillen</h2>
<p>Guy McMillen started Breaking Ground Land Services and Demolition LLC with his father, Andrew McMillen, in 2024. Guy handles customer-facing operations and project coordination. Andrew brings heavy-equipment experience dating back to 1975, including prior ownership of a tree company and fieldwork involving land clearing, demolition support, underground utilities, and road construction environments.</p>
<p>The company is young. The experience behind the controls is not. We keep claims honest: founded in 2024, backed by decades of equipment work — never “serving Florida since 1975” under this LLC name.</p>
<p>We prioritize mobile home and light-structure demolition, then support land clearing, tree and stump work, grading, and storm cleanup for property owners who want a direct line to the crew.</p>
<div class="stat-row">
<div><strong>2024</strong><span>LLC founded</span></div>
<div><strong>1975</strong><span>Andrew’s equipment start</span></div>
<div><strong>2</strong><span>Owner-operators</span></div>
</div>
</div>
<div class="media-stage reveal">{img_responsive(about_photo, "Guy and Andrew McMillen standing in front of their excavator and haul trucks", sizes=PAGE_HERO_SIZES)}</div>
</div></section>
""" + related_links("/about/") + cta_band("Talk with the owners", "Call or send project photos for a free estimate.", "Demolition")
    write(
        "about/index.html",
        head(
            f"About Us | {SHORT}",
            "Meet Guy and Andrew McMillen — father-and-son owners of Breaking Ground Land Services and Demolition in Kathleen, Florida.",
            "/about/",
            breadcrumbs=[("Home", "/"), ("About", "/about/")],
        )
        + body
        + foot(),
    )


def build_contact() -> None:
    faq_schema = {
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": "Do you offer free estimates?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Yes. Estimates are free. Final pricing is confirmed in a written scope before work begins.",
                },
            },
            {
                "@type": "Question",
                "name": "Can I text photos instead of using the form?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"Yes. Text photos and your city to {PHONE}. Include gate width, overhead lines, and structure type for the fastest response.",
                },
            },
            {
                "@type": "Question",
                "name": "Where does Breaking Ground work?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "We are based in Kathleen, Florida and serve Central Florida routinely, with larger demolition jobs considered statewide by scope.",
                },
            },
        ],
    }
    body = f"""
{page_hero("Request an Estimate", crumb([("Home","/"),("Contact","/contact/")]), "/assets/images/hero/IMG_9083-scaled.jpg")}
<section class="section-pad contact-page">
  <div class="container split split--contact">
    <div class="prose reveal">{contact_body()}{related_links("/contact/")}</div>
    <div class="form-card form-card--sticky reveal reveal--fade">
      <h3>Quick estimate</h3>
      <p class="service-aside__note">Five fields — Guy or Andrew will follow up by phone or text.</p>
      {estimate_form_contact()}
    </div>
  </div>
</section>
""" + cta_band(
        "Prefer to talk it through?",
        "Call with photos ready — we can often ballpark demolition and clearing jobs in one conversation.",
        "Mobile Home Demolition",
    )
    write(
        "contact/index.html",
        head(
            f"Contact & Free Estimate | {SHORT}",
            f"Request a free demolition or land-services estimate from Breaking Ground in Kathleen, FL. Call {PHONE}, email {EMAIL}, or send project details online.",
            "/contact/",
            breadcrumbs=[("Home", "/"), ("Contact", "/contact/")],
            extra_schema=[faq_schema],
        )
        + body
        + foot(),
    )


def build_services_hub() -> None:
    cards = "".join(
        f'<a class="service-tile reveal" href="{esc(s["path"])}">{img_responsive(s["heroImage"], "", sizes=TILE_SIZES)}<div class="service-tile__body"><h3>{esc(s["navLabel"])}</h3><p>{esc(s["meta"][:120])}…</p></div></a>'
        for s in SERVICES
    )
    body = f"""
{page_hero("Services", crumb([("Home","/"),("Services","/services/")]), "/assets/images/projects/IMG_8495-scaled.jpg", "Demolition first — clearing and site work when the lot needs more.")}
<section class="section-pad"><div class="container"><div class="service-grid">{cards}</div>{related_links("/services/")}</div></section>
""" + cta_band("Not sure which service fits?", "Describe the property and we will help scope it.", "Demolition")
    write(
        "services/index.html",
        head(
            f"Demolition & Land Services | {SHORT}",
            "Mobile home demolition, shed removal, land clearing, stump excavation, and storm cleanup in Central Florida.",
            "/services/",
            breadcrumbs=[("Home", "/"), ("Services", "/services/")],
        )
        + body
        + foot(),
    )


def _split_article_sections(article_html: str) -> tuple[str, list[tuple[str, str]]]:
    """Split article HTML into intro + [(heading_html_block, body_html), ...]."""
    return _split_on_heading(article_html, "h2")


def _split_on_heading(article_html: str, tag: str = "h2") -> tuple[str, list[tuple[str, str]]]:
    """Split HTML into intro + [(heading_block, body), ...] on the given heading tag."""
    import re

    parts = re.split(rf"(?=<{tag}\b)", article_html.strip(), flags=re.I)
    intro = parts[0].strip() if parts else ""
    sections: list[tuple[str, str]] = []
    for part in parts[1:]:
        part = part.strip()
        if not part:
            continue
        m = re.match(rf"(<{tag}\b[^>]*>.*?</{tag}>)(.*)", part, flags=re.I | re.S)
        if not m:
            sections.append(("", part))
            continue
        sections.append((m.group(1).strip(), m.group(2).strip()))
    return intro, sections


def _service_media(svc: dict) -> tuple[str, str, list[dict], list[dict]]:
    """
    Build featured media + photo queue for a service page.
    Returns (featured_src, featured_caption, mirror_photos, leftover_photos).
    When preferOwnGallery is set (or an explicit gallery exists), use services.json
    photos so service pages are not flooded by unrelated project galleries.
    """
    related = [p for p in PROJECTS if p.get("servicePath") == svc["path"]]
    featured = ""
    featured_caption = svc.get("h1") or svc.get("navLabel") or "Project photo"
    items: list[dict] = []
    seen: set[str] = set()
    prefer_own = bool(svc.get("preferOwnGallery") or svc.get("gallery"))

    def push(src: str, caption: str) -> None:
        src = (src or "").strip()
        if not src or src in seen:
            return
        if "before-process-after-" in Path(src).name and featured and src != featured:
            # Keep composite as featured only; don't also mirror it mid-page.
            return
        seen.add(src)
        items.append({"src": src, "caption": caption or featured_caption})

    if not prefer_own:
        for p in related:
            composite = p.get("composite") or ""
            if composite and not featured:
                featured = composite
                featured_caption = (
                    p.get("compositeCaption")
                    or f"Before / process / after — {p.get('h1') or p.get('navLabel')}"
                )
                seen.add(composite)
            elif not featured and p.get("image"):
                featured = p["image"]
                featured_caption = p.get("h1") or featured_caption
                seen.add(featured)
            for g in p.get("gallery") or [{"src": img, "caption": p["h1"]} for img in p.get("images", [])]:
                push(str(g.get("src") or ""), str(g.get("caption") or p.get("h1") or ""))

    for g in svc.get("gallery") or []:
        if isinstance(g, str):
            push(g, featured_caption)
        else:
            push(str(g.get("src") or ""), str(g.get("caption") or featured_caption))

    if not featured:
        featured = str(svc.get("featuredImage") or svc.get("heroImage") or OG)
        if featured not in seen:
            seen.add(featured)

    # Prefer non-composite gallery items for mirrors; keep order.
    mirror_candidates = [
        item
        for item in items
        if "before-process-after-" not in Path(item.get("src") or "").name
    ]
    if not mirror_candidates and featured:
        mirror_candidates = [{"src": featured, "caption": featured_caption}]

    return featured, featured_caption, mirror_candidates, []


def _service_checks(svc: dict) -> list[str]:
    """Sidebar checklist bullets per service."""
    slug = svc["slug"]
    common = [
        "Free estimate with photos",
        "Written scope before work starts",
        "Owner-operated crew — talk to Guy or Andrew",
        "Haul-off and lot cleanup included in scope",
    ]
    extras = {
        "mobile-home-demolition": [
            "Singlewide & doublewide removals",
            "Utility disconnect coordination",
            "Permit guidance by city/county",
            "Pad ready for rebuild or sale",
        ],
        "shed-barn-removal": [
            "Sheds, barns, carports, lean-tos",
            "Tight-yard access planning",
            "Concrete pad removal available as add-on",
            "Debris hauled — footprint cleaned",
        ],
        "demolition": [
            "Mobile homes & light structures",
            "Outbuildings and storm-damaged units",
            "Debris staging and disposal",
            "Honest scope — no overselling",
        ],
        "land-clearing": [
            "Residential & light-commercial lots",
            "Brush, undergrowth, fence lines",
            "Build-site vegetation removal",
            "Debris haul-off options",
        ],
        "tree-removal": [
            "Equipment-assisted tree removal",
            "Storm-fallen tree cleanup",
            "Log and brush haul-off",
            "Honest referral when climbing/crane needed",
        ],
        "stump-removal": [
            "Full stump & root excavation",
            "Beyond grinding — roots come out",
            "Backfill expectations in writing",
            "Haul-off of stump material",
        ],
        "pond-drainage": [
            "Pond cleanup & excavation support",
            "Ditch / swale earthwork",
            "Permit awareness for water features",
            "Clear inclusions vs. engineering limits",
        ],
        "grading-site-preparation": [
            "Rough grade after demo or clearing",
            "Fill placement & pad shaping",
            "Driveway / access prep support",
            "Drainage away from future pads",
        ],
        "storm-debris-cleanup": [
            "Limb, tree, and yard debris haul-off",
            "Post-storm priority when photos arrive early",
            "Equipment on site — not just hand crews",
            "Central Florida storm response",
        ],
    }
    return extras.get(slug, []) + common


def _checklist_html(items: list[str], *, klass: str = "check-list") -> str:
    lis = "".join(f"<li>{esc(item)}</li>" for item in items)
    return f'<ul class="{klass}">{lis}</ul>'


def build_service_pages() -> None:
    # Reload services so gallery edits in this session apply when run via importlib.
    global SERVICES
    SERVICES = json.loads((DATA / "services.json").read_text(encoding="utf-8"))

    for s in SERVICES:
        faq_schema = {
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": "Do you offer free estimates?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Yes. Estimates are free and informational until confirmed in writing.",
                    },
                },
                {
                    "@type": "Question",
                    "name": f"Do you provide {s['navLabel']} in Central Florida?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": f"Yes. Breaking Ground provides {s['navLabel']} from our Kathleen base across Central Florida, with larger jobs considered statewide by scope.",
                    },
                },
            ],
        }
        service_schema = {
            "@type": "Service",
            "name": s["navLabel"],
            "provider": {"@id": f"{DOMAIN}/#business"},
            "areaServed": "Florida",
            "url": DOMAIN + s["path"],
            "description": s["meta"],
        }

        featured, featured_caption, photo_queue, _ = _service_media(s)
        body_html = service_body(s)
        faq_html = ""
        related_html = related_links(s["path"])
        if '<div class="faq">' in body_html:
            story_html, faq_html = body_html.split('<div class="faq">', 1)
            faq_html = '<div class="faq">' + faq_html
        else:
            story_html = body_html

        intro, sections = _split_on_heading(story_html, "h3")

        # Lead photo: first gallery item (already correct for demo pages)
        lead = photo_queue[0] if photo_queue else {"src": featured, "caption": featured_caption}
        vault_limit = int(s.get("vaultLimit") or 6)
        rest_photos = photo_queue[1 : 1 + vault_limit] if len(photo_queue) > 1 else []

        lead_figure = (
            f'<figure class="service-lead-photo">'
            f'{img_responsive(lead["src"], lead.get("caption") or s["h1"], sizes=HERO_SIZES, loading="eager", width=1200, height=675)}'
            f'<figcaption>{esc(lead.get("caption") or featured_caption)}</figcaption>'
            f"</figure>"
        )

        section_cards = []
        for heading, body in sections:
            # Convert bare <ul> inside section to check-list when it's a feature list
            body_styled = body.replace("<ul>", '<ul class="check-list">', 1) if "<ul>" in body else body
            section_cards.append(
                f'<article class="service-panel">'
                f'{heading.replace("<h3", "<h2").replace("</h3>", "</h2>")}'
                f'<div class="prose">{body_styled}</div>'
                f"</article>"
            )

        photos_block = ""
        if rest_photos:
            shots = "".join(
                f'<figure class="service-shot">'
                f'{img_responsive(item["src"], item.get("caption") or s["h1"], sizes=CARD_SIZES)}'
                f'<figcaption>{esc(item.get("caption") or "Job photo")}</figcaption>'
                f"</figure>"
                for item in rest_photos
            )
            photos_block = f"""
        <section class="service-panel service-panel--photos" aria-label="{esc(s['navLabel'])} project photos">
          <h2>Real job photos</h2>
          <p class="service-panel__lead">Proof from Breaking Ground sites — structures coming down, pads cleaned, equipment on the ground.</p>
          <div class="service-shot-grid">{shots}</div>
        </section>"""

        comparison_block = ""
        comparison_gallery = s.get("comparisonGallery") or []
        if comparison_gallery:
            cmp_shots = "".join(
                f'<figure class="service-shot">'
                f'{img_responsive(item["src"], item.get("caption") or "Stump grinding example", sizes=CARD_SIZES)}'
                f'<figcaption>{esc(item.get("caption") or "Stump grinding example")}</figcaption>'
                f"</figure>"
                for item in comparison_gallery
            )
            comparison_block = f"""
        <section class="service-panel service-panel--photos" aria-label="Stump grinding vs stump removal">
          <h2>Why full stump removal beats grinding alone</h2>
          <p class="service-panel__lead">These photos show what stump grinding companies typically leave behind — wood chips, leftover roots, and a hole that is not a finished yard. Breaking Ground excavates the stump and root mass, hauls it away, and backfills to a usable grade. We show grinding results here so you do not mistake them for our finished work.</p>
          <div class="service-shot-grid">{cmp_shots}</div>
          <p class="service-panel__lead" style="margin-top:1rem;">Want the excavation approach instead? See our <a href="/projects/stump-removal-portfolio/">stump removal projects</a> and <a href="/projects/wanes-stump/">large stump excavation</a> pages.</p>
        </section>"""

        checks = _service_checks(s)
        aside_checks = _checklist_html(checks[:6], klass="check-list check-list--aside")
        checks_card = f"""
      <aside class="service-aside__card service-aside__card--checks" aria-label="Why call Breaking Ground">
        <h3>Why call us</h3>
        {aside_checks}
        <a class="btn btn-primary" href="tel:{PHONE_TEL}" style="width:100%;margin-top:0.75rem;">Call {esc(PHONE)}</a>
      </aside>"""

        photos_row = ""
        if photos_block or comparison_block:
            photos_row = f"""
  <div class="container service-photos-row">
    {photos_block}
    {comparison_block}
    {checks_card}
  </div>"""
        else:
            photos_row = f"""
  <div class="container service-photos-row service-photos-row--checks-only">
    {checks_card}
  </div>"""

        related_projects = [p for p in PROJECTS if p.get("servicePath") == s["path"]]
        project_cta = "".join(
            f'<a class="btn btn-dark" href="{esc(p["path"])}">{esc(p.get("navLabel") or p["h1"])}</a>'
            for p in related_projects[:2]
        )

        body = f"""
{page_hero(s["h1"], crumb([("Home","/"),("Services","/services/"),(s["navLabel"], s["path"])]), with_media=False)}
<section class="section-pad service-page">
  <div class="container service-layout">
    <div class="service-main">
      <article class="service-panel service-panel--intro">
        <p class="section-eyebrow">{esc(s.get("eyebrow") or s["navLabel"])} · Central Florida</p>
        <div class="prose">{intro}</div>
        {lead_figure}
        <div class="service-panel__actions">
          <a class="btn btn-primary" href="/contact/">Request a {esc(s["navLabel"].lower())} estimate</a>
          <a class="btn btn-dark" href="tel:{PHONE_TEL}">Call {esc(PHONE)}</a>
        </div>
      </article>
      <article class="service-panel">
        <h2>What’s included on a typical job</h2>
        <p class="service-panel__lead">Clear scope up front — so you know what the estimate covers before we mobilize.</p>
        {_checklist_html(checks)}
      </article>
      {"".join(section_cards)}
    </div>
    <aside class="service-aside" aria-label="Estimate form">
      <div class="service-aside__card form-card form-card--sticky">
        <h3>Free estimate</h3>
        <p class="service-aside__note">Tell us about the structure or lot — Guy or Andrew will follow up.</p>
        {estimate_form_area("", s["navLabel"])}
      </div>
    </aside>
  </div>
  {photos_row}
  <div class="container service-tail">
    <div class="service-panel">
      <div class="service-panel__actions">
        <a class="btn btn-primary" href="/contact/">Request a {esc(s["navLabel"].lower())} estimate</a>
        <a class="btn btn-dark" href="/projects/">See project gallery</a>
        {project_cta}
      </div>
      {faq_html}
      {related_html}
    </div>
  </div>
</section>
""" + cta_band(
            f"Get a {s['navLabel'].lower()} estimate",
            "Share photos and your city for a faster response.",
            s["navLabel"],
        )
        write(
            f"{s['slug']}/index.html",
            head(
                s["title"],
                s["meta"],
                s["path"],
                og_image=featured or s["heroImage"],
                breadcrumbs=[("Home", "/"), ("Services", "/services/"), (s["navLabel"], s["path"])],
                extra_schema=[service_schema, faq_schema],
            )
            + body
            + foot(),
        )


def _gallery_buckets(gallery_items: list[dict]) -> list[dict]:
    """Order gallery as before → process → after, preserving relative order within each stage."""

    def stage(item: dict) -> int:
        caption = (item.get("caption") or "").lower()
        src = Path(item.get("src") or "").name.lower()
        blob = f"{caption} {src}"
        if blob.startswith("before") or " before" in f" {blob}":
            return 0
        if blob.startswith("after") or " after" in f" {blob}":
            return 2
        return 1

    indexed = list(enumerate(gallery_items))
    indexed.sort(key=lambda pair: (stage(pair[1]), pair[0]))
    return [item for _, item in indexed]


def _mirror_figure(item: dict, fallback_alt: str) -> str:
    caption = item.get("caption") or fallback_alt
    return (
        f'<figure class="project-mirror__media">'
        f'{img_responsive(item["src"], caption, sizes=PAGE_HERO_SIZES)}'
        f'<figcaption>{esc(caption)}</figcaption>'
        f"</figure>"
    )


def build_projects() -> None:
    global PROJECTS
    PROJECTS = json.loads((DATA / "projects.json").read_text(encoding="utf-8"))
    cards = "".join(
        f"""<article class="project-card reveal"><a href="{esc(p['path'])}">{img_responsive(p.get('composite') or p['image'], p['h1'], sizes=CARD_SIZES)}</a>
        <div class="project-card__body"><p class="project-meta">{esc(p['city'])} · {esc(p['service'])}</p>
        <h3><a href="{esc(p['path'])}">{esc(p['h1'])}</a></h3><p>{esc(p['summary'])}</p></div></article>"""
        for p in PROJECTS
    )
    write(
        "projects/index.html",
        head(
            f"Project Gallery | {SHORT}",
            "Before-and-after land clearing, stump excavation, tree removal, storm cleanup, and pond projects across Central Florida.",
            "/projects/",
            breadcrumbs=[("Home", "/"), ("Projects", "/projects/")],
        )
        + page_hero("Projects", crumb([("Home", "/"), ("Projects", "/projects/")]), PROJECTS[0].get("composite") or PROJECTS[0]["image"])
        + f'<section class="section-pad"><div class="container"><div class="project-grid">{cards}</div>{related_links("/projects/")}</div></section>'
        + cta_band("Have a similar property?", "Send photos for a free estimate.")
        + foot(),
    )
    articles_dir = DATA / "project-articles"
    import re

    seo_heading_re = re.compile(
        r"Local SEO|Search topics|Florida Trends|Google Trends interest",
        re.I,
    )
    for p in PROJECTS:
        gallery_items = list(
            p.get("gallery")
            or [{"src": img, "caption": p["h1"]} for img in p.get("images", [p["image"]])]
        )
        # Skip embedding the composite file itself if it sneaks into gallery
        gallery_items = [
            item
            for item in gallery_items
            if "before-process-after-" not in Path(item.get("src") or "").name
            and "grinding-vs-removal" not in Path(item.get("src") or "").name
        ]
        # Prefer author-intended order; only bucket when no explicit gallery order
        if not p.get("gallery"):
            gallery_items = _gallery_buckets(gallery_items)
        article_path = articles_dir / f"{p['slug']}.html"
        article_html = article_path.read_text(encoding="utf-8") if article_path.is_file() else (
            f"<p>{esc(p['summary'])}</p><h3>Challenge</h3><p>{esc(p['challenge'])}</p>"
        )
        article_html = rewrite_html_images(article_html)
        intro, sections = _split_article_sections(article_html)
        main_sections: list[tuple[str, str]] = []
        seo_sections: list[tuple[str, str]] = []
        for heading, body in sections:
            blob = f"{heading} {body}"
            if seo_heading_re.search(blob):
                seo_sections.append((heading, body))
            else:
                main_sections.append((heading, body))

        hero_src = p.get("composite") or p["image"]
        composite_blurb = esc(
            p.get("compositeCaption")
            or f"Before / process / after composite for {p.get('navLabel') or p['h1']} with numbered frames."
        )

        photo_queue = list(gallery_items)
        mirror_blocks: list[str] = []

        # Images already placed via article <figure> tags should not also appear as
        # auto-paired mirror photos later on the page.
        embedded_srcs = {
            m.group(1)
            for m in re.finditer(r'<img[^>]+src=["\']([^"\']+)["\']', article_html, flags=re.I)
        }

        def _src_key(src: str) -> str:
            return Path(src or "").name.lower()

        embedded_names = {_src_key(s) for s in embedded_srcs}
        photo_queue = [
            item for item in photo_queue if _src_key(item.get("src") or "") not in embedded_names
        ]

        # Lead mirror: first before/process shot beside opening copy
        if intro and photo_queue:
            lead_photo = photo_queue.pop(0)
            mirror_blocks.append(
                f'<div class="project-mirror">'
                f"{_mirror_figure(lead_photo, p['h1'])}"
                f'<div class="prose project-mirror__copy">{intro}</div>'
                f"</div>"
            )
            intro = ""
        elif intro:
            mirror_blocks.append(f'<div class="prose project-case__intro">{intro}</div>')

        for idx, (heading, body) in enumerate(main_sections):
            has_embedded = "<figure" in body.lower() or "<img" in body.lower()
            flip = " project-mirror--flip" if idx % 2 == 1 else ""
            if has_embedded:
                # Pull the first figure into the media column so the card stays a
                # normal two-column mirror (avoids empty grid track / white space).
                figures = re.findall(r"<figure\b[^>]*>.*?</figure>", body, flags=re.I | re.S)
                body_rest = body
                media_html = ""
                if figures:
                    first = figures[0]
                    body_rest = body.replace(first, "", 1)
                    if 'class="' in first[:80].lower():
                        media_html = re.sub(
                            r'(<figure\b[^>]*class=")([^"]*)(")',
                            r'\1\2 project-mirror__media\3',
                            first,
                            count=1,
                            flags=re.I,
                        )
                    else:
                        media_html = re.sub(
                            r"<figure\b",
                            '<figure class="project-mirror__media"',
                            first,
                            count=1,
                            flags=re.I,
                        )
                copy = f"{heading}{body_rest}"
                if media_html:
                    mirror_blocks.append(
                        f'<div class="project-mirror{flip}">'
                        f"{media_html}"
                        f'<div class="prose project-mirror__copy">{copy}</div>'
                        f"</div>"
                    )
                else:
                    mirror_blocks.append(
                        f'<div class="prose project-case__section">{copy}</div>'
                    )
            else:
                photo = photo_queue.pop(0) if photo_queue else None
                copy = f"{heading}{body}"
                if photo:
                    mirror_blocks.append(
                        f'<div class="project-mirror{flip}">'
                        f"{_mirror_figure(photo, p['h1'])}"
                        f'<div class="prose project-mirror__copy">{copy}</div>'
                        f"</div>"
                    )
                else:
                    mirror_blocks.append(f'<div class="prose project-case__section">{copy}</div>')

        youtube_block = ""
        if p.get("youtubeUrl"):
            label = esc(p.get("youtubeLabel") or "Watch the job on YouTube")
            youtube_block = f"""
    <section class="project-more" aria-label="Job video">
      <h2 class="project-gallery-title">See this stump removal on video</h2>
      <p class="project-meta">Even after we cut over half of the stump off, it still weighed almost 5 tons by the time we hauled it to the landfill.</p>
      <p><a class="btn btn-primary" href="{esc(p['youtubeUrl'])}" target="_blank" rel="noopener noreferrer">{label}</a></p>
    </section>"""

        comparison_block = ""
        if p.get("comparisonComposite"):
            comparison_block = f"""
    <section class="project-more" aria-label="Stump grinding vs stump removal">
      <h2 class="project-gallery-title">Stump grinding vs stump removal</h2>
      <p class="project-meta">Grinding leaves roots and chips in the ground. Full excavation pulls the mass, hauls it away, and leaves a hole you can backfill for a usable yard.</p>
      <figure class="project-composite">
        {img_responsive(p['comparisonComposite'], "Stump grinding versus stump removal comparison", sizes=HERO_SIZES, width=1600, height=900)}
        <figcaption>Left: typical stump grinding leftovers. Right: Breaking Ground excavation and haul-off results.</figcaption>
      </figure>
    </section>"""

        leftovers = "".join(
            f'<figure class="project-shot">'
            f'{img_responsive(item["src"], item.get("caption") or p["h1"], sizes=CARD_SIZES)}'
            f'<figcaption><span class="project-shot__label">{esc(item.get("caption") or "")}</span></figcaption>'
            f"</figure>"
            for item in photo_queue
        )
        more_gallery = ""
        if leftovers:
            more_gallery = f"""
    <section class="project-more" aria-label="Additional process photos">
      <h2 class="project-gallery-title">More process photos</h2>
      <p class="project-meta">Additional angles and steps from this job — captions follow each filename.</p>
      <div class="project-more__grid">{leftovers}</div>
    </section>"""

        seo_html = ""
        if seo_sections:
            seo_parts = "".join(
                f'<div class="prose project-case__section">{heading}{body}</div>'
                for heading, body in seo_sections
            )
            seo_html = f"""
    <section class="project-more project-seo-notes" aria-label="Additional search topics">
      <h2 class="project-gallery-title">Additional search topics</h2>
      <p class="project-meta">Reference notes for owners comparing related Florida service searches.</p>
      {seo_parts}
    </section>"""

        body = f"""
{page_hero(p["h1"], crumb([("Home","/"),("Projects","/projects/"),(p["h1"], p["path"])]), with_media=False)}
<section class="section-pad project-case">
  <div class="container">
    <figure class="project-composite">
      {img_responsive(hero_src, f"{p['h1']} before process after composite", sizes=HERO_SIZES, width=1600, height=900)}
      <figcaption>{composite_blurb}</figcaption>
    </figure>
    <div class="project-case__story">
      {"".join(mirror_blocks)}
    </div>
    {youtube_block}
    {comparison_block}
    {more_gallery}
    {seo_html}
    <div class="project-case__cta prose">
      <div class="project-case__actions">
        <a class="btn btn-primary" href="/contact/">Request a similar estimate</a>
        <a class="btn btn-dark" href="{esc(p["servicePath"])}">{esc(p["service"])} service</a>
      </div>
      {related_links(p["path"])}
    </div>
  </div>
</section>
"""
        write(
            f"projects/{p['slug']}/index.html",
            head(
                p["title"],
                p["meta"],
                p["path"],
                og_image=hero_src,
                breadcrumbs=[("Home", "/"), ("Projects", "/projects/"), (p["h1"], p["path"])],
            )
            + body
            + foot(),
        )


def build_pricing() -> None:
    body = f"""
{page_hero("Pricing Guide", crumb([("Home","/"),("Pricing","/pricing/")]), "/assets/images/projects/IMG_8495-scaled.jpg", "Ballpark ranges for planning — every job needs a written estimate.")}
<section class="section-pad"><div class="container prose policy-wrap">
<p>These ranges reflect typical Central Florida residential and light-commercial work in 2026. Access, disposal fees, permits, hazardous materials, and attachments can move a project up or down. <strong>Nothing on this page is a bid.</strong></p>
<table class="price-table">
<thead><tr><th>Service</th><th>Typical planning range</th><th>Notes</th></tr></thead>
<tbody>
<tr><td>Mobile home demolition (singlewide)</td><td>$3,000 – $6,500</td><td>Access, foundation, attachments vary</td></tr>
<tr><td>Mobile home demolition (doublewide)</td><td>$5,000 – $11,000</td><td>Multi-section and site constraints add cost</td></tr>
<tr><td>Shed / small outbuilding removal</td><td>$800 – $3,500</td><td>Size, concrete, haul distance</td></tr>
<tr><td>Barn / larger outbuilding</td><td>$2,500 – $8,000+</td><td>Quoted after walk-through</td></tr>
<tr><td>Stump excavation (per stump)</td><td>$250 – $1,200+</td><td>Diameter and root mass drive price</td></tr>
<tr><td>Residential land clearing</td><td>$2,000 – $8,000+/lot</td><td>Density, acreage, haul-off</td></tr>
<tr><td>Storm debris cleanup</td><td>Hourly or project bid</td><td>Volume and disposal fees</td></tr>
</tbody>
</table>
<p class="price-note">Disposal, landfill, and permit fees may be pass-through items. Asbestos or regulated materials are excluded and require specialty contractors if discovered.</p>
<h2>What we need for an accurate estimate</h2>
<ul>
<li>Address or city and gate/access notes</li>
<li>Photos of the structure or lot</li>
<li>Singlewide / doublewide / shed dimensions if known</li>
<li>Whether utilities are disconnected</li>
<li>Your end goal (rebuild, sell, clean up)</li>
</ul>
</div></section>
""" + related_links("/pricing/") + cta_band("Get your written estimate", "Free to request — binding only when confirmed in writing.")
    write(
        "pricing/index.html",
        head(
            f"Pricing Guide | {SHORT}",
            "Planning ranges for mobile home demolition, shed removal, stump excavation, and land clearing in Central Florida.",
            "/pricing/",
            breadcrumbs=[("Home", "/"), ("Pricing", "/pricing/")],
        )
        + body
        + foot(),
    )


def build_policies() -> None:
    policies = [
        (
            "privacy-policy",
            "Privacy Policy",
            f"""
<p>This Privacy Policy describes how {LEGAL} (“we,” “us”) collects and uses information through {DOMAIN}.</p>
<h2>Information we collect</h2>
<p>When you submit an estimate form or email us, we may collect your name, phone number, email address, job location, project details, and any photos you upload. We also receive standard server and analytics data such as IP address and pages visited if analytics tools are enabled.</p>
<h2>How we use information</h2>
<p>We use contact details to respond to estimate requests, schedule work, and communicate about projects. We do not sell personal information.</p>
<h2>Form processing</h2>
<p>Estimate forms may be processed by Formspree or a similar form provider acting as a processor on our behalf.</p>
<h2>Sharing</h2>
<p>We may share information with service providers who help us operate the website or deliver services (for example, email delivery). We may disclose information if required by law.</p>
<h2>Data retention</h2>
<p>We retain inquiry and project communications as needed for business and legal purposes.</p>
<h2>Contact</h2>
<p>Questions: <a href="mailto:{EMAIL}">{EMAIL}</a> or {PHONE}.</p>
""",
        ),
        (
            "terms-of-service",
            "Terms of Service",
            f"""
<p>These Terms of Service govern use of {DOMAIN}, operated by {LEGAL}.</p>
<h2>Website information is not a contract</h2>
<p>Content on this site is for general information about our demolition, clearing, and site services. It is <strong>not</strong> a binding contract, bid, warranty, or permit approval unless confirmed in a written estimate or signed agreement for a specific project.</p>
<h2>Estimates</h2>
<p>Free estimates are informational. Final pricing, scope, timelines, disposal fees, and responsibilities are confirmed in writing for each project.</p>
<h2>Services and limitations</h2>
<p>We provide smaller demolition and structure removal (including mobile homes, sheds, and similar light structures), land clearing, tree and stump work, grading support, and related site services. We are not marketing ourselves as a licensed general contractor for unrestricted building demolition. Permit requirements vary by jurisdiction.</p>
<h2>Hazardous materials</h2>
<p>We do not perform asbestos abatement. If regulated materials are identified or reasonably suspected, work may stop until qualified specialty contractors address them.</p>
<h2>Payment</h2>
<p>Payment terms, deposits, and progress payments are stated in the written agreement for each job. See also our <a href="/payment-deposit-policy/">Payment &amp; Deposit Policy</a>.</p>
<h2>Limitation of liability</h2>
<p>To the fullest extent permitted by Florida law, we are not liable for indirect or consequential damages arising from website use. Project liability is governed by the written service agreement, not these website terms.</p>
<p><em>These website terms are not a substitute for an attorney-reviewed construction contract.</em></p>
""",
        ),
        (
            "payment-deposit-policy",
            "Payment & Deposit Policy",
            f"""
<p>This policy explains how {LEGAL} typically handles deposits and payments. Specific terms in a written project agreement control if they differ.</p>
<h2>Estimates vs. invoices</h2>
<p>Website ranges and verbal discussions are not invoices. Work proceeds under a written scope and payment schedule.</p>
<h2>Deposits</h2>
<p>Projects may require a commencement deposit before mobilization. Deposits secure schedule and cover early costs such as permitting coordination, disposal arrangements, and crew allocation. Deposit amounts and refund conditions (if any) are stated in writing.</p>
<h2>Progress and final payment</h2>
<p>Larger jobs may use progress payments tied to milestones (for example, structure down, debris hauled, final grade). Final payment is due upon completion of the written scope unless otherwise agreed.</p>
<h2>Nonpayment</h2>
<p>We may suspend or stop work if payments are late under the agreement. You remain responsible for work performed, mobilization, disposal fees incurred, and permitted charges under Florida law.</p>
<h2>Change orders</h2>
<p>Extra work outside the written scope requires a change order and may require additional payment before that work proceeds.</p>
<h2>Disposal and third-party fees</h2>
<p>Landfill, transfer station, and certain permit fees may be billed as pass-through costs when disclosed in the estimate.</p>
<h2>Disputes</h2>
<p>Contact us promptly at {PHONE} or {EMAIL} to resolve billing questions. Keeping communication open prevents most payment disputes.</p>
""",
        ),
        (
            "image-use-policy",
            "Image Use Policy",
            f"""
<p>Photographs and videos on {DOMAIN} show real projects associated with {LEGAL} unless otherwise noted.</p>
<h2>Our use</h2>
<p>We may photograph job sites for documentation, safety, training, and marketing — including this website and social profiles — unless a property owner objects in writing before work begins.</p>
<h2>Your privacy</h2>
<p>We avoid publishing faces of non-employees and personal documents when practical. Address-level details may be generalized (city/county) on public pages.</p>
<h2>Third-party use</h2>
<p>Images are owned by us or used with permission. You may not scrape, republish, or commercially reuse site images without written permission.</p>
<h2>Requests</h2>
<p>To request removal of a project photo, email {EMAIL} with the page URL.</p>
""",
        ),
    ]
    for slug, title, content in policies:
        path = f"/{slug}/"
        write(
            f"{slug}/index.html",
            head(
                f"{title} | {SHORT}",
                f"{title} for {LEGAL}.",
                path,
                breadcrumbs=[("Home", "/"), (title, path)],
            )
            + page_hero(title, crumb([("Home", "/"), (title, path)]), OG)
            + f'<section class="section-pad"><div class="container prose policy-wrap">{content}</div></section>'
            + foot(),
        )


def build_service_areas() -> None:
    areas = AREAS["areas"]
    tier_a = [a for a in areas if a["tier"] == "A"]
    tier_b = [a for a in areas if a["tier"] == "B"]

    def links(items: list) -> str:
        return "".join(
            f'<a href="/areas/{esc(a["slug"])}/">{esc(a["shortName"])}</a>' for a in items
        )

    hub = f"""
{page_hero("Service Areas", crumb([("Home","/"),("Service Areas","/service-areas/")]), "/assets/images/projects/IMG_0249-scaled.jpg", AREAS["coverageDisclaimer"])}
<section class="section-pad"><div class="container">
<p class="section-eyebrow">Tier A — Local Core</p>
<h2>Kathleen, Lakeland &amp; nearby</h2>
<div class="area-grid">{links(tier_a)}</div>
<p class="section-eyebrow" style="margin-top:2.5rem;">Tier B — Statewide by Scope</p>
<h2>Mobile home &amp; light demolition focus</h2>
<div class="area-grid">{links(tier_b)}</div>
{related_links("/service-areas/")}
</div></section>
""" + cta_band("Working outside this list?", "Larger demolition jobs may still qualify — tell us the city.")
    write(
        "service-areas/index.html",
        head(
            f"Florida Service Areas | {SHORT}",
            "Based in Kathleen serving Central Florida; larger mobile home demolition and site jobs considered statewide by scope.",
            "/service-areas/",
            breadcrumbs=[("Home", "/"), ("Service Areas", "/service-areas/")],
        )
        + hub
        + foot(),
    )

    for a in areas:
        short = a["shortName"]
        angle = a.get("angle", "full")
        if angle == "demo":
            title = f"Mobile Home Demolition in {short}, FL | {SHORT}"
            h1 = f"Mobile Home & Light Demolition in {short}"
            meta = f"Mobile home demolition and light structure removal in {short}, {a['county']}. Owner-operated Breaking Ground — free estimates."
        else:
            title = f"Demolition & Land Services in {short}, FL | {SHORT}"
            h1 = f"Demolition & Land Services in {short}"
            meta = f"Mobile home demolition, shed removal, land clearing, and stump work in {short}, FL. Call {PHONE}."
        hero_img = a.get("heroImage") or "/assets/images/projects/IMG_8286-scaled.jpg"
        credit = a.get("heroImageCredit") or {}
        lic = (credit.get("license") or "").strip()
        credit_line = "Photo via Wikimedia Commons"
        if lic:
            credit_line = f"Photo via Wikimedia Commons ({lic})"
        body_figure = f"""
<figure class="area-local-shot">
  {img_responsive(hero_img, f"{short}, Florida", sizes=HERO_SIZES, width=1600, height=900)}
  <figcaption><strong>{esc(short)}, Florida</strong> — local landmark / area photo. {esc(credit_line)}.</figcaption>
</figure>
"""
        body = f"""
{page_hero(
    h1,
    crumb([("Home","/"),("Service Areas","/service-areas/"),(short, f"/areas/{a['slug']}/")]),
    hero_img,
    meta,
    image_alt=f"{short}, Florida",
    image_credit=credit_line,
)}
<section class="section-pad"><div class="container split split--area">
<div class="form-card form-card--sticky reveal"><h3>Estimate for {esc(short)}</h3>{estimate_form_area(short, "Mobile Home Demolition")}</div>
<div class="prose reveal">{body_figure}{area_body(a)}{related_links(f"/areas/{a['slug']}/")}</div>
</div></section>
"""
        write(
            f"areas/{a['slug']}/index.html",
            head(
                title,
                meta,
                f"/areas/{a['slug']}/",
                og_image=hero_img,
                breadcrumbs=[("Home", "/"), ("Service Areas", "/service-areas/"), (short, f"/areas/{a['slug']}/")],
                extra_schema=[
                    {
                        "@type": "Service",
                        "name": f"Demolition services in {short}",
                        "provider": {"@id": f"{DOMAIN}/#business"},
                        "areaServed": short + ", FL",
                        "url": f"{DOMAIN}/areas/{a['slug']}/",
                    }
                ],
            )
            + body
            + foot(),
        )


def build_thank_you_404() -> None:
    write(
        "thank-you/index.html",
        head(
            f"Thank You | {SHORT}",
            "We received your estimate request.",
            "/thank-you/",
            breadcrumbs=[("Home", "/"), ("Thank You", "/thank-you/")],
        )
        + page_hero("Thank you", crumb([("Home", "/"), ("Thank You", "/thank-you/")]), OG, "We received your request and will respond soon.")
        + f'<section class="section-pad"><div class="container prose"><p>If it is urgent, call <a href="tel:{PHONE_TEL}">{esc(PHONE)}</a>.</p><p><a href="/">Return home</a></p></div></section>'
        + foot(),
    )
    write(
        "404.html",
        head("Page Not Found | " + SHORT, "The page you requested was not found.", "/", breadcrumbs=[("Home", "/")])
        + page_hero("Page not found", crumb([("Home", "/")]), OG)
        + '<section class="section-pad"><div class="container"><p><a class="btn btn-primary" href="/">Go home</a> <a class="btn btn-dark" href="/contact/">Contact us</a></p></div></section>'
        + foot(),
    )


def build_redirects() -> None:
    redirects = {
        "landscaping/index.html": "/pond-drainage/",
        "posts/index.html": "/projects/",
        "brooksville-land-clearing/index.html": "/projects/shawns-clearing/",
        "hurricane-clean-up/index.html": "/projects/",
        "8-16-2024-better-than-stump-grinding/index.html": "/projects/stump-removal-portfolio/",
        "stump-removal-in-lakeland/index.html": "/projects/stump-removal-portfolio/",
        "12-30-25-shed-removal-near-me/index.html": "/projects/",
        "how-to-dig-a-pond/index.html": "/projects/bills-pond/",
        # Old featured project slugs
        "projects/brooksville-land-clearing/index.html": "/projects/shawns-clearing/",
        "projects/lakeland-stump-excavation/index.html": "/projects/stump-removal-portfolio/",
        "projects/shed-removal/index.html": "/projects/",
        "projects/hurricane-cleanup/index.html": "/projects/",
        "projects/lakeland-highlands-tree-removal/index.html": "/projects/dawns-job/",
        "projects/pond-earthwork-support/index.html": "/projects/bills-pond/",
    }
    for p in PROJECTS:
        for legacy in p.get("legacyUrls", []):
            legacy = legacy.strip("/")
            if not legacy:
                continue
            redirects[f"{legacy}/index.html"] = p["path"]
    for rel, dest in redirects.items():
        write(
            rel,
            f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8" />
<title>Redirecting…</title>
<link rel="canonical" href="{DOMAIN}{dest}" />
<meta http-equiv="refresh" content="0;url={dest}" />
<script>location.replace("{dest}");</script>
</head><body><p>Moved to <a href="{dest}">{dest}</a>.</p></body></html>
""",
        )


def build_robots_llms() -> None:
    write(
        "robots.txt",
        f"""User-agent: *
Allow: /

Sitemap: {DOMAIN}/sitemap.xml
""",
    )
    write(
        "llms.txt",
        f"""# {NAME}
> Owner-operated mobile home demolition, light structure removal, land clearing, and site work based in Kathleen, Florida.

Contact: {PHONE} | {EMAIL}
Site: {DOMAIN}

## Primary services
- [Mobile home demolition]({DOMAIN}/mobile-home-demolition/)
- [Demolition]({DOMAIN}/demolition/)
- [Land clearing]({DOMAIN}/land-clearing/)
- [Stump removal]({DOMAIN}/stump-removal/)
- [Tree removal]({DOMAIN}/tree-removal/)
- [Storm cleanup]({DOMAIN}/storm-debris-cleanup/)

## Key pages
- [Request a free estimate]({DOMAIN}/contact/)
- [About Guy and Andrew]({DOMAIN}/about/)
- [Project gallery]({DOMAIN}/projects/)
- [Service areas]({DOMAIN}/service-areas/)

## Notes
- Founded 2024 (not a GC marketing unrestricted building demolition)
- Central Florida core; statewide by scope for larger jobs
""",
    )


def build_sitemap() -> None:
    urls = [
        "/",
        "/about/",
        "/contact/",
        "/services/",
        "/projects/",
        "/pricing/",
        "/service-areas/",
        "/privacy-policy/",
        "/terms-of-service/",
        "/payment-deposit-policy/",
        "/image-use-policy/",
        "/thank-you/",
    ]
    urls += [s["path"] for s in SERVICES]
    urls += [p["path"] for p in PROJECTS]
    urls += [f"/areas/{a['slug']}/" for a in AREAS["areas"]]
    body = '<?xml version="1.0" encoding="UTF-8"?>\n'
    body += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        pri = "1.0" if u == "/" else ("0.9" if u.count("/") <= 2 else "0.7")
        body += f"  <url><loc>{DOMAIN}{u}</loc><lastmod>{TODAY}</lastmod><changefreq>monthly</changefreq><priority>{pri}</priority></url>\n"
    body += "</urlset>\n"
    write("sitemap.xml", body)
    return urls


def build_docs() -> None:
    urls = build_sitemap()
    site_urls = f"""# SITE-URLS — Breaking Ground

Domain: {DOMAIN}
Generated: {TODAY}

## Preserved WordPress canonicals
- `/` → home
- `/about/`
- `/contact/`
- `/demolition/`
- `/land-clearing/`
- `/tree-removal/`
- `/stump-removal/`

## Redirect map (HTML refresh + canonical)
| Old | New |
|-----|-----|
| `/landscaping/` | `/pond-drainage/` |
| `/posts/` | `/projects/` |
| `/brooksville-land-clearing/` | `/projects/brooksville-land-clearing/` |
| `/hurricane-clean-up/` | `/projects/hurricane-cleanup/` |
| `/8-16-2024-better-than-stump-grinding/` | `/projects/lakeland-stump-excavation/` |
| `/stump-removal-in-lakeland/` | `/projects/lakeland-stump-excavation/` |
| `/12-30-25-shed-removal-near-me/` | `/projects/shed-removal/` |
| `/how-to-dig-a-pond/` | `/projects/pond-earthwork-support/` |

Prefer Cloudflare 301s at DNS cutover when available.

## Indexable URL count
{len(urls)} URLs in sitemap.xml

## DNS cutover
Change only website A/CNAME. Preserve MX, SPF, DKIM, DMARC for Zoho email.
"""
    write("SITE-URLS.md", site_urls)

    imgs = sorted((ROOT / "assets" / "images").rglob("*"))
    lines = ["# IMAGE-INVENTORY", "", "Downloaded from breakinggroundlsad.com WordPress media.", ""]
    for p in imgs:
        if p.is_file():
            lines.append(f"- `{p.relative_to(ROOT).as_posix()}` ({p.stat().st_size // 1024} KB)")
    write("IMAGE-INVENTORY.md", "\n".join(lines) + "\n")

    write(
        "LAUNCH-CHECKLIST.md",
        f"""# Launch Checklist — {SHORT}

## Before DNS cutover
- [ ] Replace Formspree ID in `formspree.json` and `data/site.json`, then re-run `python scripts/build_site.py`
- [ ] Confirm Zoho email `contact@breakinggroundlsad.com` receives Formspree notifications
- [ ] Client approves staging site on GitHub Pages
- [ ] Document current DNS (especially MX/SPF/DKIM/DMARC)

## DNS cutover
- [ ] Point only A/CNAME/AAAA for the website to GitHub Pages
- [ ] Do **not** replace the entire DNS zone blindly
- [ ] Preserve email records

## After cutover
- [ ] Confirm SSL
- [ ] Test contact form end-to-end
- [ ] Verify preserved URLs: /demolition/, /land-clearing/, /tree-removal/, /stump-removal/, /about/, /contact/
- [ ] Verify redirects from legacy post URLs
- [ ] Submit sitemap in Google Search Console
- [ ] Update Google Business Profile website link (client-owned)

## Out of scope reminders
No CRM, GBP automation, or dynamic review widgets in Phase 1.
""",
    )


def apply_base_to_chrome() -> None:
    """Rewrite root-absolute paths in shared chrome for project Pages.

    Idempotent: strips any existing siteBase prefix first, then applies once.
    """
    import re

    for name in ("header.html", "footer.html"):
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        # Normalize previously prefixed paths back to root-absolute
        if BASE:
            text = re.sub(rf'(?:{re.escape(BASE)})+/', '/', text)
            text = text.replace('href="/', f'href="{BASE}/')
            text = text.replace('src="/', f'src="{BASE}/')
        else:
            # Custom-domain mode: ensure chrome is root-absolute, not project-prefixed
            text = re.sub(r'(?:/breakinggroundlsad-website)+/', '/', text)
        path.write_text(text, encoding="utf-8")
        print("rewrote", name)


def main() -> None:
    apply_base_to_chrome()
    build_home()
    build_about()
    build_contact()
    build_services_hub()
    build_service_pages()
    build_projects()
    build_pricing()
    build_policies()
    build_service_areas()
    build_thank_you_404()
    build_redirects()
    build_robots_llms()
    build_docs()
    print("DONE")
    if BASE:
        print(f"Preview base: {BASE}/ -> https://nicholasjknight.github.io{BASE}/")


if __name__ == "__main__":
    main()
