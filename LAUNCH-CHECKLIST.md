# Launch Checklist — Breaking Ground

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
- [x] Confirm SSL
- [ ] Test contact form end-to-end
- [x] Verify preserved URLs: /demolition/, /land-clearing/, /tree-removal/, /stump-removal/, /about/, /contact/
- [ ] Verify redirects from legacy post URLs
- [x] Submit sitemap in Google Search Console (verified 2026-08-06 audit)
- [ ] Update Google Business Profile website link (client-owned)
- [ ] **Client-owned Cloudflare/email** (out of website scope): disable Email Address Obfuscation if mailto 404s; headers optional
- [x] Bing Webmaster sitemap + URL batch submitted 2026-08-06
- [x] IndexNow key file live at `/0e914d9815b99d4daab617a77b50ccac.txt`
- [ ] Continue GSC Request Indexing for money pages when daily quota resets

## Out of scope reminders
One-time static GitHub Pages build. No ongoing Cloudflare/email ownership, CRM, GBP automation, or analytics install unless separately scoped.

## Audit snapshot (2026-08-06)
- GSC: low traffic post-cutover; several important URLs not indexed yet
- PSI mobile sample: about 90 / contact 87 / services 81 / projects 84
- Schema / axe / GEO `llms.txt` + `ai.txt`: healthy
