YASUMIBI（ヤスミビ）は「休み日」と「安い日」の掛け言葉。休みを自分で調整できるカップルに向けて、宿の料金を実際に調べ、泊まるならこの日、を出すブランドです。サイトは旅の雑誌のように静かで上品に、動画はネットのノリ全開で。この二面性がブランドの芯です。

## Two voices

YASUMIBI has two registers. Never mix them on one surface.

| | Site (yasumibi.com) | Video (TikTok) |
| --- | --- | --- |
| Role | 信頼される情報源 | 止めて、笑わせて、保存させる |
| Tone | 雑誌の編集部。静か、断定、短文 | ドパガキ系。勢い、ネットスラング、ツッコミ |
| Example | 「1月6日(水)泊は、5軒中4軒がその宿の最安値でした。」 | 「1/6、神日確定。」「この日泊まれたら優勝」 |
| Type | `headline` (mincho), `body`, `price` | `shout`, `price-xl`, `hotel-name` |
| Color | `paper`, `ink`, `pine`, data colors | footage + `paper-raised` panels + `marker` stamps |

### Video copy rules (the hype layer)

- Use the house vocabulary, every video: **神日**（その宿の最安日）, **優勝**（この日に泊まれば勝ち）, **バグ価格**（ありえない安さ）, **〜しか勝たん**, **ぶっ壊れ**（コスパ）, **今月のバグ宿**（シリーズ名）.
- One slang word per panel. The number always stays exact: 「バグ価格 ¥45,540」, never 「激安」 without a figure.
- Slang never replaces the data. Every claim on screen comes from the 楽天トラベル data of the date shown in the disclaimer.
- Set slang in `shout` on a `marker` stamp; set prices in `price-xl`; set hotel names in `hotel-name` (mincho). Hotel names are never joked about.
- No emoji in video text. No mascots or characters.

### Site copy rules

- 敬体ではなく常体の短文。「〜でした」「〜です」は可、感嘆符は使わない。
- Name things the way travelers search: エリア名 → 価格帯 → 宿名 → 日付.
- Always state the condition under a price: `caption` 「大人2名・1室・1泊2食付きの最安プラン（税込）」 and the 調べた日.
- The one allowed hype word on the site is the **神日** badge on a hotel's cheapest date, so video viewers recognise it when they land.
- PR表記 at the top of every page: 「PR／本ページは楽天アフィリエイトを利用しています」.

## Visual foundations

- **One color, one meaning** (2026-10-21). Ground is white `paper`, frame and text are `ink`.
  - `ink` (black): text, rules, labels, links, and the booking button (`rakuten-cta`).
  - `data-cheap` (green): 安い only — 神日, the lowest price, cheap cells.
  - `marker` (yellow): おトク only — the 神日 badge, the 楽天カード band, the おトク tab.
  - `data-high` (true red): 高い only — expensive prices and expensive cells (on `data-high-tint`). Never a button.
- **Calendars**: only the 神日 cell is a strong fill. Other tiers are light tints (`data-near`, `data-warm`, `data-high-tint`), sold out is striped `data-sold` with 満室, so the cheapest day stands out at a glance.
- **Price data**: tiers stay relative to each hotel's own lowest price (≤ +0%, +15%, +35%, above). Every color state also carries a word or badge.
- **Type** (readability first, 2026-10-21): the brand lives in the logo, colors, layout and data, not in typefaces. Archivo is used only for the wordmark (`wordmark`) and for every price and number (`display`: width 100%, weight 800, tabular numerals). All Japanese text — headlines, hotel names, body, labels — uses the device's standard gothic (Hiragino Sans on iPhone, Noto Sans JP on Android): headings weight 800, body 400, no letter-spacing. No mincho, no uppercase Latin eyebrows (write 料金マップ, not PRICE MAP). Minimum text size 13px on the site; muted text stays at 4.5:1 or better.
- **Spacing**: phone gutter `space-4`, sections `space-12` apart. Calendar cells sit `space-1` apart.
- **Radii**: editorial and square by default (`radius-none`). `radius-sm` only on calendar cells and badges, `radius-pill` only on filter tabs and date chips.
- **Shadows**: none on the site except `shadow-sheet` on the sticky booking sheet. In video, flat pages have no shadows; text over footage takes `shadow-title` (titles) or a soft text shadow (small lines).
- **Focus**: a 2px solid `pine` ring with 2px offset on every interactive element.
- **Imagery**: bright, clean footage and photos of the actual area (箱根なら紅葉・芦ノ湖・ロープウェイ). Never images from a different area, never dark or moody grading, never AI-generated animals or people.

## Logo

The logo is the word **YASUMIBI** set in `wordmark`: Archivo 900, width 118%, uppercase, tight tracking, stretched to the full content width like a magazine masthead. It sits at the top of every cover and every closing page. Under it runs a 3px rule with 休み日を、安い日に。 on the left and ¥ PRICE MAGAZINE on the right. Inside pages carry a small running head: YASUMIBI left, `No.001 / P.02` right, over a 3px rule. Never outline, gradient, italicise or recolor the wordmark except white on footage or `pine`, and `ink` on `paper`.

## Magazine format (video and site)

Every video is one issue. The site's feature pages reuse the same parts.

- **Cover (first frame)**: full-bleed bright footage. Top: issue number left (`No.001`), month right (`JANUARY 2027`), masthead, tagline rule. Then a `marker` label 特集, the feature title in `cover-title` with `shadow-title`, two or three cover lines on the right with a `display` numeral in `marker` above each, and one round `marker` seal. Keep the lower 35% free of text for the TikTok interface.
- **Inside pages**: alternate flat pages and footage pages. Flat pages are `paper` (ink text) or `pine` (white text). Footage pages put the subject's name large in mincho with `shadow-title`, and slide a `paper` sheet up from the bottom for numbers.
- **Numbers**: prices in `display` (Archivo 800, width 100%, tabular numerals), cheap in `data-cheap`, expensive in `data-high`. Comparisons are two columns split by a 3px `ink` rule, never boxed cards.
- **Emphasis**: a `marker` highlighter swept under one phrase per page (the hype word). At most one tilted stamp per video, used for the 神日 reveal.
- **Closing page**: `pine`, masthead again, the save line in hype voice (保存しないと、普通に損。) and a `paper` bar pointing to the profile link.
- **Disclaimer**: the data date and conditions sit at y≈1460px on every page, white on footage or `pine`, `ink-muted` on `paper`.

## Iconography

No icon set yet. Use words and numerals instead of icons (「満室」「土」「最安」). Arrows in links are the text glyph →.
