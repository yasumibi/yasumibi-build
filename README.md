# yasumibi-build

旅の料金サイト [YASUMIBI](https://yasumibi.com/) を作るプログラム。楽天トラベルAPIの料金から、宿ごとの「神日（その月でいちばん安い日）」とランキングを作り、静的サイトとして公開する。

## しくみ
- `tools/` … サイトを作るプログラム（Python）
- `.github/workflows/daily.yml` … 毎日2:17（日本時間）に料金を取り直し、サイトを作り直して公開
- `.github/workflows/research.yml` … エリアを足すときの候補調査（楽天の全件 → 口コミ・評価・2食付きで絞る）
- `.github/workflows/publish.yml` … サイトの作り直しと公開

データ（料金・宿情報）は非公開のリポジトリにあり、Actions が `data/` に取り込んで使う。公開サイトは別リポジトリ（Cloudflare Pages）。

## 料金の取り方
- 大人2名・1室・1泊2食付きプランの最安（2名合計・税込）
- 楽天APIは1秒に1回以下。45日先までは毎日、90日先までは3日に1回、それより先は週1回取り直す。新しい宿・まだ取っていない日付は必ず取る
- 掲載期間は「今月（残り2週間未満なら来月）から6か月」で自動的に進む
- エリアごとに分け、1回250軒までのまとまりで順番に取る

## 必要な Secrets
- `RAKUTEN_APP_ID`, `RAKUTEN_ACCESS_KEY` … 楽天ウェブサービス
- `SITE_PUSH_TOKEN` … 公開サイトとデータのリポジトリに書き込める Fine-grained token
