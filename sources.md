# Afghan Security — Source List

Curated July 2026. Review every few months — outlets in exile change domains often, and X/Substack handles shift.

## News agencies & outlets with RSS (mainstream + regional)

| Source | RSS URL | Notes |
|---|---|---|
| Khaama Press | https://www.khaama.com/feed/ | Kabul-based, English, broad daily coverage incl. security |
| Pajhwok Afghan News | https://pajhwok.com/feed/ | Afghanistan's largest independent wire service |
| Ariana News | https://ariananews.af/feed/ | Widely watched independent Afghan outlet |
| TOLOnews | https://tolonews.com/rss.xml (verify — check site footer) | Afghanistan's first 24h news channel |
| Daily Outlook Afghanistan | https://outlookafghanistan.net/feed (verify) | English-language independent |
| Afghanistan Sun | https://feeds.afghanistansun.com/rss | Regional + international angle |
| Al Jazeera — Afghanistan tag | https://www.aljazeera.com/xml/rss/all.xml (filter by tag) | Strong cross-border/Pakistan coverage |
| BBC — Afghanistan | http://feeds.bbci.co.uk/news/world/asia/rss.xml (filter) | Filter for Afghanistan-tagged items |
| Reuters — Afghanistan | via reuters.com/world/asia-pacific (no public RSS; use web_search or a paid feed aggregator) | |
| RFE/RL Gandhara (Radio Azadi) | https://gandhara.rferl.org/api/zrqiteuuir | US-funded, strong security/insurgency beat |

## Exiled independent Afghan media (post-2021, security/rights focused)

Good news: all of these turned out to run on WordPress once checked directly, which usually means a working (if unadvertised) `/feed` RSS endpoint. The digest script tries the feed first and falls back to scraping the listing page if that fails — see README for details.

| Outlet | English site | Feed to try | Fallback listing page |
|---|---|---|---|
| Hasht-e Subh / 8AM Media | 8am.media/eng | 8am.media/eng/feed | 8am.media/eng/category/afghanistan-news/ |
| Etilaatroz (English arm: KabulNow) | kabulnow.com | kabulnow.com/feed | kabulnow.com/category/news/ |
| Rukhshana Media | rukhshana.com/en | rukhshana.com/en/feed | rukhshana.com/en/ |
| Zan Times | zantimes.com | zantimes.com/feed | zantimes.com/ |
| Afghanistan Analysts Network | afghanistan-analysts.org/en | afghanistan-analysts.org/en/feed/ | afghanistan-analysts.org/en/ |
| PAYK Investigative Journalism Center | payk.net | not verified — check manually | payk.net |

Note: Etilaat Roz's Dari-language site (etilaatroz.com) is the original outlet; KabulNow is its dedicated English-language sister site — use KabulNow for an English-language digest.

## Institutional / monitoring bodies (high signal-to-noise for "security" specifically)

| Source | Feed / URL |
|---|---|
| UNAMA (UN Mission in Afghanistan) | unama.unmissions.org — press releases, no clean RSS; check periodically |
| UN Security Council Report — Afghanistan | securitycouncilreport.org/monthly-forecast (monthly, high quality) |
| Afghan Witness (Centre for Information Resilience) | info-res.org/afghan-witness — OSINT verification of security incidents, has a newsletter |
| ACLED (Armed Conflict Location & Event Data) | acleddata.com — Afghanistan dashboard, has RSS/API |
| Institute for the Study of War | understandingwar.org — periodic Afghanistan updates |
| CSIS | csis.org/regions/asia/afghanistan |
| International Crisis Group | crisisgroup.org/asia/south-asia/afghanistan — has RSS |
| Middle East Institute — Taliban Leadership Tracker | talibantracker.mei.edu |
| Stimson Center South Asia Program | stimson.org |
| EU Institute for Security Studies | iss.europa.eu |

## Individual creators / analysts worth following directly

- **Lynne O'Donnell** — "Project Taliban" on Substack (lynneodonnell.substack.com) — veteran AP/FP correspondent, security and jihadist-network focus
- **Jane Ferguson** — war correspondent, formerly PBS NewsHour, now independent (Noosphere) — Afghanistan/withdrawal coverage
- **Afghan Analyst** (@AfghanAnalyst2 on X) — anonymous but well-sourced running commentary on Taliban/NRF/ISKP dynamics
- **Amira Jadoon** (Clemson) — ISKP researcher, publishes via Stimson/academic channels, active on X
- **Andrew Mines** — co-author of ISKP research, George Washington University Program on Extremism
- **Bill Roggio** — Long War Journal / FDD, tracks Taliban/AQ/ISKP incidents closely, has RSS: https://www.longwarjournal.org/feed

## Suggested keyword filter set (for narrowing broad feeds to "security")

```
Taliban, ISKP, ISIS-K, Islamic State Khorasan, al-Qaeda, TTP, Tehrik-i-Taliban,
NRF, National Resistance Front, Haqqani, suicide bombing, airstrike, insurgency,
border clash, Durand Line, Panjshir, terrorism, militant, security forces,
UNAMA, sanctions, arms, insurgent, extremist, jihadist
```
