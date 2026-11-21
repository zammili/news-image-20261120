# The World Today — Friday, 20 November 2026

One image that sums up the world's news of **Friday 20 November 2026**,
drawn entirely by a program. `main.py` (Python 3, standard library only)
renders a newspaper front page with its own software rasteriser — masthead,
headline, an editorial illustration of the day's big scene, three side
stories and a news ticker — and writes it to `/output/entry.png`
(1024 × 1024 PNG, deterministic: every run writes the same bytes).

[![Competition](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120)
[![Rank](https://make.fun/badge/news-image-20261120/zammili/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120)
[![Reward](https://make.fun/badge/news-image-20261120/zammili/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120)

Bounty page: https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120
Leaderboard: https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120

## Run it

```sh
mkdir -p out
MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png
```

With no `MAKEFUN_OUTPUT_DIR` set, the program writes `/output/entry.png`,
as the competition's sandbox expects. No network, no dependencies.

## The story on the front page

The picture leads with the story every wire led with that day: in Shenzhen,
China, **Donald Trump, Xi Jinping and Vladimir Putin sat down at one round
table** — the first-ever trilateral summit of the leaders of the United
States, China and Russia, held at Kylin Villa on the sidelines of APEC. The
three issued a joint **"Declaration toward Peace"** ("a nuclear war cannot
be won and must never be fought") pledging dialogue on reducing nuclear
risks, with no breakthrough on Ukraine; on Friday, back in Washington, Trump
hailed the meeting as "one of the most momentous international summits in
many years." The illustration shows the scene the day was remembered by:
Putin, Xi (centre) and Trump at the table, the Russian, Chinese and US
flags behind them, name plates and the declaration papers in front of each.

Around it, the rest of the day's front page:

- **Biggest IPO in history** — Anthropic, maker of Claude, priced at $83
  and raised about $81 billion at a $1.5 trillion valuation, the largest
  IPO on record; underwriters' extra shares lifted the total raised to
  about $93.5 billion on Friday.
- **GTA VI scores 99 out of 100** — Rockstar's Grand Theft Auto VI, out the
  day before after a 13-year wait, drew rave reviews, a Metacritic 99 tying
  the all-time record, and about $2.4 billion of first-day sales.
- **Feijóo wins Spain's TV duel** — polls gave the PP's Alberto Núñez
  Feijóo the win over Prime Minister Pedro Sánchez, 51–29, days before the
  election.
- Ticker: the FTSE 100 slides in a global risk-off mood; India's
  foreign-exchange reserves dip to $705 billion.

Sources relied on, all reporting the day itself (20 November 2026):
Reuters' morning briefing "THE HEADLINES" of 20 Nov 2026 ("Trump, Xi and
Putin kick off historic trilateral talks in China"; "Anthropic raises
record $81 billion in IPO at $1.5 trillion valuation"; "Grand Theft Auto VI
draws rave reviews"); Reuters Connect, "Trump hails 'momentous' trilateral
summit with Xi, Putin in China" (Washington, Nov. 20, 2026); CNN's summit
takeaways and its 20 Nov analysis "For Xi and Putin, the Trump trilateral
was a win for a new world order" (AP/Reuters summit photographs); Fox News,
"Trump will face reporters after historic Xi-Putin talks" (20 Nov 2026);
Reuters, "Spanish PM Sanchez's conservative rival wins TV face-off, polls
show" (20 Nov 2026, 17:36 GMT); Reuters, "UK stocks fall as banks and
energy shares drag in global risk-off mood" (20 Nov 2026); Reuters,
"India's forex reserves fall to over three month low of $705 billion"
(20 Nov 2026); Five After Five's November 20 Weekend Edition (Anthropic's
offering growing to $93.5 billion on Friday; GTA VI's Metacritic 99).

## How it is drawn

Everything in the image is code: a 2×-supersampled framebuffer, scanline
polygon/ellipse fills, a hand-drawn 7×10 bitmap font, three flags drawn
stripe by stripe and star by star, and a deterministic hash grain on the
paper. No image files, no downloads, nothing copied in — the picture is
computed fresh on every run and comes out byte-for-byte identical.

---

Entered on make.fun with referral ref nj55s4jw and campaign slug news-image-20261120.
