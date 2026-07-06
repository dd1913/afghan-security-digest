# Afghan Security Weekly Digest

Automated weekly (Monday, 07:00 GMT) digest of Afghan security news, pulled from
RSS feeds, filtered by keyword, optionally summarized with Claude, and published
as a static site.

## Files

- `sources.md` — curated list of RSS feeds, exiled/independent Afghan outlets,
  monitoring bodies, and individual analysts/creators worth tracking. Review and
  prune/expand this as feeds break or new voices emerge.
- `generate_digest.py` — the pipeline: fetch → filter (last 7 days + keyword
  match) → summarize → render `index.html`.
- `.github/workflows/weekly-digest.yml` — GitHub Actions workflow that runs the
  script every Monday 07:00 GMT and publishes the result to GitHub Pages.

## How to actually deploy this (one-time setup, ~10 minutes)

1. **Create a GitHub repo** (e.g. `afghan-security-weekly`) and push these files
   to it.
2. **Enable GitHub Pages**: repo Settings → Pages → Source → "GitHub Actions".
3. **(Optional) Add an Anthropic API key** for AI-written summaries instead of
   raw feed excerpts: repo Settings → Secrets and variables → Actions → New
   repository secret → name it `ANTHROPIC_API_KEY`. Without this, the digest
   still works — it just uses the original feed's own summary text, trimmed.
4. That's it. The workflow fires automatically every Monday at 07:00 GMT. Your
   site will be live at `https://<your-username>.github.io/afghan-security-weekly/`.
   If you own a custom domain, add a `CNAME` file with your domain name and
   point its DNS at GitHub Pages (GitHub's docs walk through this).

## Why this approach

I can't run a persistent background job myself — I only exist within this chat
session, so I can't be the thing that fires every Monday forever. GitHub Actions
is a free, reliable way to get real weekly automation without you needing to
run or pay for a server. If you'd rather use a different scheduler (a cron job
on your own machine/VPS, Zapier, an AWS Lambda + EventBridge rule), the same
`generate_digest.py` script drops in — only the trigger mechanism changes.

## Tuning it

- **Add/remove feeds**: edit the `FEEDS` list in `generate_digest.py` — check
  `sources.md` for candidates, but confirm each RSS URL actually resolves
  before adding it (some Afghan outlets rotate domains for safety reasons).
- **Adjust keyword filter**: edit `KEYWORDS` — broader keywords catch more
  noise, narrower ones may miss slow-building stories.
- **Change lookback window or schedule**: `DAYS_LOOKBACK` in the script and the
  `cron` line in the workflow file.

## Scraping fallback for exiled outlets

8AM Media, KabulNow (Etilaatroz's English arm), Rukhshana Media, Zan Times, and
the Afghanistan Analysts Network all turned out to run on WordPress once I
checked their actual page structure — which usually means a working `/feed`
endpoint exists even though it's not linked anywhere obvious. So the script
now does this for each of them:

1. **Try the site's RSS feed first** (e.g. `8am.media/eng/feed`).
2. **If that fails or returns nothing**, fall back to scraping the article
   listing page directly with BeautifulSoup, using generic WordPress markup
   patterns (`<article>` blocks with a heading link inside).

Three honest caveats on the scraping fallback:

- **It's less reliable than RSS by nature.** Every WordPress theme lays out
  its listing pages slightly differently, so the generic parser may return
  fewer results — or occasionally miss a site entirely — if a theme uses an
  unusual structure. Check the Actions log after the first few runs (each
  source logs whether it used its feed or fell back to scraping) and refine
  the selectors in `scrape_listing_page()` for any source that's coming back
  empty.
- **No reliable publish dates from scraping**, so those items skip the 7-day
  filter and just reflect "what's currently on the listing page" — fine for
  a weekly digest, but worth knowing.
- **Some sites may still block automated requests** even with a realistic
  browser User-Agent (Cloudflare and similar bot-protection can be aggressive,
  especially for smaller under-resourced newsrooms trying to protect
  themselves from Taliban surveillance, which sometimes has the side effect
  of blocking legitimate scrapers too). If a source consistently fails, that's
  worth respecting rather than trying to force — consider subscribing to
  their actual newsletter (several offer one) as the human-in-the-loop
  substitute for that source.

One more thing worth keeping in mind generally: run this respectfully. The
script waits a second between requests to these smaller sites, and only pulls
headlines/links/short excerpts rather than full article text — both to stay
within reasonable scraping etiquette and because reproducing full articles
would raise copyright concerns. The digest should always link back to the
original source rather than substitute for reading it.
