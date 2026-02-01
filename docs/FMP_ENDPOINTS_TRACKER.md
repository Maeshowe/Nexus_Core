# FMP Endpoints Tracker

> **Projekt:** OmniData Nexus Core - FMP Extension
> **Összesen:** 189 endpoint
> **Státusz:** 13 EXISTING | 0 IN_PROGRESS | 176 TODO

---

## Jelmagyarázat

| Státusz | Jelentés |
|---------|----------|
| `EXISTING` | Már implementálva v1.2.0-ban |
| `TODO` | Még nem kezdődött |
| `IN_PROGRESS` | Fejlesztés alatt |
| `DONE` | Kész, tesztelve |
| `BLOCKED` | Blokkolva (függőség/probléma) |

| Tier | Jelentés |
|------|----------|
| `FREE` | Ingyenes tier-ben elérhető |
| `PREMIUM` | Fizetős csomag szükséges |

---

## 3.1 Search & Directory

**Branch:** `feature/fmp-search`
**Modul:** `src/data_loader/providers/fmp/search.py`
**Endpoints:** 12

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.1.01 | `search-symbol` | Ticker keresés szimbólum alapján | FREE | TODO | `feature/fmp-search` |
| 3.1.02 | `search-name` | Keresés cégnév alapján | FREE | TODO | `feature/fmp-search` |
| 3.1.03 | `search-cik` | Keresés CIK szám alapján | FREE | TODO | `feature/fmp-search` |
| 3.1.04 | `search-cusip` | Keresés CUSIP alapján | FREE | TODO | `feature/fmp-search` |
| 3.1.05 | `search-isin` | Keresés ISIN alapján | FREE | TODO | `feature/fmp-search` |
| 3.1.06 | `company-screener` | Stock screener (szűrő) | FREE | TODO | `feature/fmp-search` |
| 3.1.07 | `stock-list` | Összes ticker lista | FREE | TODO | `feature/fmp-search` |
| 3.1.08 | `etf-list` | ETF lista | FREE | TODO | `feature/fmp-search` |
| 3.1.09 | `available-exchanges` | Elérhető tőzsdék | FREE | TODO | `feature/fmp-search` |
| 3.1.10 | `available-sectors` | Szektorok listája | FREE | TODO | `feature/fmp-search` |
| 3.1.11 | `available-industries` | Iparágak listája | FREE | TODO | `feature/fmp-search` |
| 3.1.12 | `available-countries` | Országok listája | FREE | TODO | `feature/fmp-search` |

---

## 3.2 Company Information

**Branch:** `feature/fmp-company`
**Modul:** `src/data_loader/providers/fmp/company.py`
**Endpoints:** 13

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.2.01 | `profile` | Cég profil (részletes) | FREE | **EXISTING** | - |
| 3.2.02 | `profile-cik` | Profil CIK alapján | FREE | TODO | `feature/fmp-company` |
| 3.2.03 | `company-notes` | Cég jegyzetek | FREE | TODO | `feature/fmp-company` |
| 3.2.04 | `stock-peers` | Versenytársak | FREE | TODO | `feature/fmp-company` |
| 3.2.05 | `delisted-companies` | Kivezetett cégek | FREE | TODO | `feature/fmp-company` |
| 3.2.06 | `employee-count` | Alkalmazottak száma | FREE | TODO | `feature/fmp-company` |
| 3.2.07 | `historical-employee-count` | Historikus alkalmazotti létszám | FREE | TODO | `feature/fmp-company` |
| 3.2.08 | `market-capitalization` | Piaci kapitalizáció | FREE | TODO | `feature/fmp-company` |
| 3.2.09 | `historical-market-cap` | Historikus market cap | FREE | TODO | `feature/fmp-company` |
| 3.2.10 | `shares-float` | Free float adatok | FREE | TODO | `feature/fmp-company` |
| 3.2.11 | `mergers-acquisitions` | M&A tranzakciók | FREE | TODO | `feature/fmp-company` |
| 3.2.12 | `key-executives` | Vezetőség | FREE | TODO | `feature/fmp-company` |
| 3.2.13 | `executive-compensation` | Vezetői kompenzáció | FREE | TODO | `feature/fmp-company` |

---

## 3.3 Quotes

**Branch:** `feature/fmp-quotes`
**Modul:** `src/data_loader/providers/fmp/quotes.py`
**Endpoints:** 13

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.3.01 | `quote` | Teljes quote | FREE | **EXISTING** | - |
| 3.3.02 | `quote-short` | Rövid quote | FREE | TODO | `feature/fmp-quotes` |
| 3.3.03 | `aftermarket-trade` | After-hours kereskedés | FREE | TODO | `feature/fmp-quotes` |
| 3.3.04 | `aftermarket-quote` | After-hours quote | FREE | TODO | `feature/fmp-quotes` |
| 3.3.05 | `stock-price-change` | Árváltozás (napi/heti/havi) | FREE | TODO | `feature/fmp-quotes` |
| 3.3.06 | `batch-quote` | Batch quotes (több ticker) | FREE | TODO | `feature/fmp-quotes` |
| 3.3.07 | `batch-exchange-quote` | Teljes tőzsde quotes | FREE | TODO | `feature/fmp-quotes` |
| 3.3.08 | `batch-mutualfund-quotes` | Mutual fund quotes | FREE | TODO | `feature/fmp-quotes` |
| 3.3.09 | `batch-etf-quotes` | ETF quotes | FREE | TODO | `feature/fmp-quotes` |
| 3.3.10 | `batch-commodity-quotes` | Commodity quotes | FREE | TODO | `feature/fmp-quotes` |
| 3.3.11 | `batch-crypto-quotes` | Crypto quotes | FREE | TODO | `feature/fmp-quotes` |
| 3.3.12 | `batch-forex-quotes` | Forex quotes | FREE | TODO | `feature/fmp-quotes` |
| 3.3.13 | `batch-index-quotes` | Index quotes | FREE | TODO | `feature/fmp-quotes` |

---

## 3.4 Financial Statements

**Branch:** `feature/fmp-financials`
**Modul:** `src/data_loader/providers/fmp/financials.py`
**Endpoints:** 22

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.4.01 | `income-statement` | Eredménykimutatás | FREE | **EXISTING** | - |
| 3.4.02 | `balance-sheet-statement` | Mérleg | FREE | **EXISTING** | - |
| 3.4.03 | `cash-flow-statement` | Cash flow | FREE | **EXISTING** | - |
| 3.4.04 | `income-statement-ttm` | TTM eredménykimutatás | FREE | TODO | `feature/fmp-financials` |
| 3.4.05 | `balance-sheet-statement-ttm` | TTM mérleg | FREE | TODO | `feature/fmp-financials` |
| 3.4.06 | `cash-flow-statement-ttm` | TTM cash flow | FREE | TODO | `feature/fmp-financials` |
| 3.4.07 | `key-metrics` | Kulcs mutatók | FREE | **EXISTING** | - |
| 3.4.08 | `ratios` | Pénzügyi ráták (150+) | FREE | **EXISTING** | - |
| 3.4.09 | `key-metrics-ttm` | TTM kulcs mutatók | FREE | TODO | `feature/fmp-financials` |
| 3.4.10 | `ratios-ttm` | TTM ráták | FREE | TODO | `feature/fmp-financials` |
| 3.4.11 | `financial-scores` | Pénzügyi pontszámok (Altman Z, Piotroski) | FREE | TODO | `feature/fmp-financials` |
| 3.4.12 | `owner-earnings` | Owner earnings | FREE | TODO | `feature/fmp-financials` |
| 3.4.13 | `enterprise-values` | Enterprise value | FREE | TODO | `feature/fmp-financials` |
| 3.4.14 | `income-statement-growth` | Növekedési mutatók | FREE | TODO | `feature/fmp-financials` |
| 3.4.15 | `balance-sheet-statement-growth` | Mérleg növekedés | FREE | TODO | `feature/fmp-financials` |
| 3.4.16 | `cash-flow-statement-growth` | CF növekedés | FREE | TODO | `feature/fmp-financials` |
| 3.4.17 | `revenue-product-segmentation` | Bevétel termék szerint | FREE | TODO | `feature/fmp-financials` |
| 3.4.18 | `revenue-geographic-segmentation` | Bevétel földrajz szerint | FREE | TODO | `feature/fmp-financials` |
| 3.4.19 | `income-statement-as-reported` | SEC formátumban | FREE | TODO | `feature/fmp-financials` |
| 3.4.20 | `balance-sheet-statement-as-reported` | SEC formátumban | FREE | TODO | `feature/fmp-financials` |
| 3.4.21 | `cash-flow-statement-as-reported` | SEC formátumban | FREE | TODO | `feature/fmp-financials` |
| 3.4.22 | `financial-statement-full-as-reported` | Teljes SEC statement | FREE | TODO | `feature/fmp-financials` |

---

## 3.5 Charts

**Branch:** `feature/fmp-charts`
**Modul:** `src/data_loader/providers/fmp/charts.py`
**Endpoints:** 10

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.5.01 | `historical-price-eod/light` | Egyszerű EOD chart | FREE | TODO | `feature/fmp-charts` |
| 3.5.02 | `historical-price-eod/full` | Teljes EOD chart (OHLCV) | FREE | **EXISTING** | - |
| 3.5.03 | `historical-price-eod/non-split-adjusted` | Nem korrigált | FREE | TODO | `feature/fmp-charts` |
| 3.5.04 | `historical-price-eod/dividend-adjusted` | Osztalék korrigált | FREE | TODO | `feature/fmp-charts` |
| 3.5.05 | `historical-chart/1min` | 1 perces intraday | PREMIUM | TODO | `feature/fmp-charts` |
| 3.5.06 | `historical-chart/5min` | 5 perces intraday | PREMIUM | TODO | `feature/fmp-charts` |
| 3.5.07 | `historical-chart/15min` | 15 perces intraday | PREMIUM | TODO | `feature/fmp-charts` |
| 3.5.08 | `historical-chart/30min` | 30 perces intraday | PREMIUM | TODO | `feature/fmp-charts` |
| 3.5.09 | `historical-chart/1hour` | 1 órás intraday | PREMIUM | TODO | `feature/fmp-charts` |
| 3.5.10 | `historical-chart/4hour` | 4 órás intraday | PREMIUM | TODO | `feature/fmp-charts` |

---

## 3.6 Economics

**Branch:** `feature/fmp-economics`
**Modul:** `src/data_loader/providers/fmp/economics.py`
**Endpoints:** 4

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.6.01 | `treasury-rates` | Treasury hozamok | FREE | TODO | `feature/fmp-economics` |
| 3.6.02 | `economic-indicators` | Gazdasági indikátorok (GDP, stb.) | FREE | TODO | `feature/fmp-economics` |
| 3.6.03 | `economic-calendar` | Gazdasági naptár | FREE | TODO | `feature/fmp-economics` |
| 3.6.04 | `market-risk-premium` | Piaci kockázati prémium | FREE | TODO | `feature/fmp-economics` |

---

## 3.7 Calendars & Events

**Branch:** `feature/fmp-calendars`
**Modul:** `src/data_loader/providers/fmp/calendars.py`
**Endpoints:** 9

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.7.01 | `dividends` | Osztalék (ticker alapján) | FREE | **EXISTING** | - |
| 3.7.02 | `dividends-calendar` | Osztalék naptár | FREE | TODO | `feature/fmp-calendars` |
| 3.7.03 | `earnings` | Earnings (ticker alapján) | FREE | **EXISTING** | - |
| 3.7.04 | `earnings-calendar` | Earnings naptár | FREE | TODO | `feature/fmp-calendars` |
| 3.7.05 | `ipos-calendar` | IPO naptár | FREE | TODO | `feature/fmp-calendars` |
| 3.7.06 | `ipos-disclosure` | IPO disclosure-ök | FREE | TODO | `feature/fmp-calendars` |
| 3.7.07 | `ipos-prospectus` | IPO prospektusok | FREE | TODO | `feature/fmp-calendars` |
| 3.7.08 | `splits` | Stock splitek | FREE | **EXISTING** | - |
| 3.7.09 | `splits-calendar` | Split naptár | FREE | TODO | `feature/fmp-calendars` |

---

## 3.8 Earnings Transcripts

**Branch:** `feature/fmp-transcripts`
**Modul:** `src/data_loader/providers/fmp/transcripts.py`
**Endpoints:** 4

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.8.01 | `earning-call-transcript` | Earnings call átirat | FREE | TODO | `feature/fmp-transcripts` |
| 3.8.02 | `earning-call-transcript-latest` | Legújabb átiratok | FREE | TODO | `feature/fmp-transcripts` |
| 3.8.03 | `earning-call-transcript-dates` | Elérhető dátumok | FREE | TODO | `feature/fmp-transcripts` |
| 3.8.04 | `earnings-transcript-list` | Elérhető ticker-ek | FREE | TODO | `feature/fmp-transcripts` |

---

## 3.9 News

**Branch:** `feature/fmp-news`
**Modul:** `src/data_loader/providers/fmp/news.py`
**Endpoints:** 9

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.9.01 | `fmp-articles` | FMP saját cikkek | FREE | TODO | `feature/fmp-news` |
| 3.9.02 | `news/general-latest` | Általános hírek | FREE | TODO | `feature/fmp-news` |
| 3.9.03 | `news/press-releases-latest` | Sajtóközlemények | FREE | TODO | `feature/fmp-news` |
| 3.9.04 | `news/stock-latest` | Részvény hírek | FREE | TODO | `feature/fmp-news` |
| 3.9.05 | `news/crypto-latest` | Crypto hírek | FREE | TODO | `feature/fmp-news` |
| 3.9.06 | `news/forex-latest` | Forex hírek | FREE | TODO | `feature/fmp-news` |
| 3.9.07 | `news/stock` | Keresés ticker alapján | FREE | TODO | `feature/fmp-news` |
| 3.9.08 | `news/crypto` | Keresés crypto alapján | FREE | TODO | `feature/fmp-news` |
| 3.9.09 | `news/forex` | Keresés forex alapján | FREE | TODO | `feature/fmp-news` |

---

## 3.10 Institutional Ownership (Form 13F)

**Branch:** `feature/fmp-institutional`
**Modul:** `src/data_loader/providers/fmp/institutional.py`
**Endpoints:** 7

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.10.01 | `institutional-ownership/latest` | Legújabb 13F filings | FREE | TODO | `feature/fmp-institutional` |
| 3.10.02 | `institutional-ownership/extract` | Filing részletek | FREE | TODO | `feature/fmp-institutional` |
| 3.10.03 | `institutional-ownership/dates` | 13F dátumok | FREE | TODO | `feature/fmp-institutional` |
| 3.10.04 | `institutional-ownership/holder-performance-summary` | Holder teljesítmény | FREE | TODO | `feature/fmp-institutional` |
| 3.10.05 | `institutional-ownership/holder-industry-breakdown` | Iparági bontás | FREE | TODO | `feature/fmp-institutional` |
| 3.10.06 | `institutional-ownership/symbol-positions-summary` | Pozíció összefoglaló | FREE | TODO | `feature/fmp-institutional` |
| 3.10.07 | `institutional-ownership/industry-summary` | Iparági összefoglaló | FREE | TODO | `feature/fmp-institutional` |

---

## 3.11 Analyst

**Branch:** `feature/fmp-analyst`
**Modul:** `src/data_loader/providers/fmp/analyst.py`
**Endpoints:** 8

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.11.01 | `analyst-estimates` | Elemzői becslések | FREE | **EXISTING** | - |
| 3.11.02 | `ratings-snapshot` | Rating pillanatkép | FREE | TODO | `feature/fmp-analyst` |
| 3.11.03 | `ratings-historical` | Historikus ratingek | FREE | TODO | `feature/fmp-analyst` |
| 3.11.04 | `price-target-summary` | Árcél összefoglaló | FREE | TODO | `feature/fmp-analyst` |
| 3.11.05 | `price-target-consensus` | Árcél konszenzus | FREE | **EXISTING** | - |
| 3.11.06 | `grades` | Elemzői értékelések | FREE | TODO | `feature/fmp-analyst` |
| 3.11.07 | `grades-historical` | Historikus értékelések | FREE | TODO | `feature/fmp-analyst` |
| 3.11.08 | `grades-consensus` | Értékelés konszenzus | FREE | TODO | `feature/fmp-analyst` |

---

## 3.12 Market Performance

**Branch:** `feature/fmp-performance`
**Modul:** `src/data_loader/providers/fmp/performance.py`
**Endpoints:** 9

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.12.01 | `sector-performance-snapshot` | Szektor teljesítmény | FREE | TODO | `feature/fmp-performance` |
| 3.12.02 | `industry-performance-snapshot` | Iparági teljesítmény | FREE | TODO | `feature/fmp-performance` |
| 3.12.03 | `historical-sector-performance` | Historikus szektor | FREE | TODO | `feature/fmp-performance` |
| 3.12.04 | `historical-industry-performance` | Historikus iparág | FREE | TODO | `feature/fmp-performance` |
| 3.12.05 | `sector-pe-snapshot` | Szektor P/E | FREE | TODO | `feature/fmp-performance` |
| 3.12.06 | `industry-pe-snapshot` | Iparági P/E | FREE | TODO | `feature/fmp-performance` |
| 3.12.07 | `biggest-gainers` | Legnagyobb nyertesek | FREE | TODO | `feature/fmp-performance` |
| 3.12.08 | `biggest-losers` | Legnagyobb vesztesek | FREE | TODO | `feature/fmp-performance` |
| 3.12.09 | `most-actives` | Legaktívabb részvények | FREE | TODO | `feature/fmp-performance` |

---

## 3.13 Technical Indicators

**Branch:** `feature/fmp-technical`
**Modul:** `src/data_loader/providers/fmp/technical.py`
**Endpoints:** 9

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.13.01 | `technical-indicators/sma` | SMA | FREE | TODO | `feature/fmp-technical` |
| 3.13.02 | `technical-indicators/ema` | EMA | FREE | TODO | `feature/fmp-technical` |
| 3.13.03 | `technical-indicators/wma` | WMA | FREE | TODO | `feature/fmp-technical` |
| 3.13.04 | `technical-indicators/dema` | DEMA | FREE | TODO | `feature/fmp-technical` |
| 3.13.05 | `technical-indicators/tema` | TEMA | FREE | TODO | `feature/fmp-technical` |
| 3.13.06 | `technical-indicators/rsi` | RSI | FREE | TODO | `feature/fmp-technical` |
| 3.13.07 | `technical-indicators/standarddeviation` | Standard Deviation | FREE | TODO | `feature/fmp-technical` |
| 3.13.08 | `technical-indicators/williams` | Williams %R | FREE | TODO | `feature/fmp-technical` |
| 3.13.09 | `technical-indicators/adx` | ADX | FREE | TODO | `feature/fmp-technical` |

---

## 3.14 ETF & Mutual Funds

**Branch:** `feature/fmp-etf`
**Modul:** `src/data_loader/providers/fmp/etf.py`
**Endpoints:** 7

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.14.01 | `etf/holdings` | ETF holdings | FREE | TODO | `feature/fmp-etf` |
| 3.14.02 | `etf/info` | ETF információ | FREE | TODO | `feature/fmp-etf` |
| 3.14.03 | `etf/country-weightings` | Ország súlyozás | FREE | TODO | `feature/fmp-etf` |
| 3.14.04 | `etf/asset-exposure` | Asset exposure | FREE | TODO | `feature/fmp-etf` |
| 3.14.05 | `etf/sector-weightings` | Szektor súlyozás | FREE | TODO | `feature/fmp-etf` |
| 3.14.06 | `funds/disclosure-holders-latest` | Fund disclosure | FREE | TODO | `feature/fmp-etf` |
| 3.14.07 | `funds/disclosure` | Mutual fund disclosure | FREE | TODO | `feature/fmp-etf` |

---

## 3.15 SEC Filings

**Branch:** `feature/fmp-sec`
**Modul:** `src/data_loader/providers/fmp/sec.py`
**Endpoints:** 7

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.15.01 | `sec-filings-8k` | Legújabb 8-K filings | FREE | TODO | `feature/fmp-sec` |
| 3.15.02 | `sec-filings-financials` | Pénzügyi filings | FREE | TODO | `feature/fmp-sec` |
| 3.15.03 | `sec-filings-search/form-type` | Keresés form típus szerint | FREE | TODO | `feature/fmp-sec` |
| 3.15.04 | `sec-filings-search/symbol` | Keresés ticker szerint | FREE | TODO | `feature/fmp-sec` |
| 3.15.05 | `sec-filings-search/cik` | Keresés CIK szerint | FREE | TODO | `feature/fmp-sec` |
| 3.15.06 | `sec-profile` | SEC profil | FREE | TODO | `feature/fmp-sec` |
| 3.15.07 | `standard-industrial-classification-list` | SIC kódok | FREE | TODO | `feature/fmp-sec` |

---

## 3.16 Insider Trading

**Branch:** `feature/fmp-insider`
**Modul:** `src/data_loader/providers/fmp/insider.py`
**Endpoints:** 6

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.16.01 | `insider-trading/latest` | Legújabb insider trades | FREE | TODO | `feature/fmp-insider` |
| 3.16.02 | `insider-trading/search` | Keresés | FREE | TODO | `feature/fmp-insider` |
| 3.16.03 | `insider-trading/reporting-name` | Keresés név szerint | FREE | TODO | `feature/fmp-insider` |
| 3.16.04 | `insider-trading-transaction-type` | Tranzakció típusok | FREE | TODO | `feature/fmp-insider` |
| 3.16.05 | `insider-trading/statistics` | Statisztikák | FREE | TODO | `feature/fmp-insider` |
| 3.16.06 | `acquisition-of-beneficial-ownership` | Beneficial ownership | FREE | TODO | `feature/fmp-insider` |

---

## 3.17 Indexes

**Branch:** `feature/fmp-indexes`
**Modul:** `src/data_loader/providers/fmp/indexes.py`
**Endpoints:** 7

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.17.01 | `index-list` | Index lista | FREE | TODO | `feature/fmp-indexes` |
| 3.17.02 | `sp500-constituent` | S&P 500 összetevők | FREE | TODO | `feature/fmp-indexes` |
| 3.17.03 | `nasdaq-constituent` | Nasdaq összetevők | FREE | TODO | `feature/fmp-indexes` |
| 3.17.04 | `dowjones-constituent` | Dow Jones összetevők | FREE | TODO | `feature/fmp-indexes` |
| 3.17.05 | `historical-sp500-constituent` | Historikus S&P 500 | FREE | TODO | `feature/fmp-indexes` |
| 3.17.06 | `historical-nasdaq-constituent` | Historikus Nasdaq | FREE | TODO | `feature/fmp-indexes` |
| 3.17.07 | `historical-dowjones-constituent` | Historikus Dow Jones | FREE | TODO | `feature/fmp-indexes` |

---

## 3.18 Forex

**Branch:** `feature/fmp-forex`
**Modul:** `src/data_loader/providers/fmp/forex.py`
**Endpoints:** 6

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.18.01 | `forex-list` | Forex párok listája | FREE | TODO | `feature/fmp-forex` |
| 3.18.02 | `quote` (forex) | Forex quote | FREE | TODO | `feature/fmp-forex` |
| 3.18.03 | `historical-price-eod/full` (forex) | Historikus FX | FREE | TODO | `feature/fmp-forex` |
| 3.18.04 | `historical-chart/1min` (forex) | 1 perces FX | PREMIUM | TODO | `feature/fmp-forex` |
| 3.18.05 | `historical-chart/5min` (forex) | 5 perces FX | PREMIUM | TODO | `feature/fmp-forex` |
| 3.18.06 | `historical-chart/1hour` (forex) | 1 órás FX | PREMIUM | TODO | `feature/fmp-forex` |

---

## 3.19 Cryptocurrencies

**Branch:** `feature/fmp-crypto`
**Modul:** `src/data_loader/providers/fmp/crypto.py`
**Endpoints:** 6

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.19.01 | `cryptocurrency-list` | Crypto lista | FREE | TODO | `feature/fmp-crypto` |
| 3.19.02 | `quote` (crypto) | Crypto quote | FREE | TODO | `feature/fmp-crypto` |
| 3.19.03 | `historical-price-eod/full` (crypto) | Historikus crypto | FREE | TODO | `feature/fmp-crypto` |
| 3.19.04 | `historical-chart/1min` (crypto) | 1 perces crypto | PREMIUM | TODO | `feature/fmp-crypto` |
| 3.19.05 | `historical-chart/5min` (crypto) | 5 perces crypto | PREMIUM | TODO | `feature/fmp-crypto` |
| 3.19.06 | `historical-chart/1hour` (crypto) | 1 órás crypto | PREMIUM | TODO | `feature/fmp-crypto` |

---

## 3.20 Commodities

**Branch:** `feature/fmp-commodities`
**Modul:** `src/data_loader/providers/fmp/commodities.py`
**Endpoints:** 4

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.20.01 | `commodities-list` | Commodities lista | FREE | TODO | `feature/fmp-commodities` |
| 3.20.02 | `quote` (commodity) | Commodity quote | FREE | TODO | `feature/fmp-commodities` |
| 3.20.03 | `historical-price-eod/full` (commodity) | Historikus commodity | FREE | TODO | `feature/fmp-commodities` |
| 3.20.04 | `historical-chart/1min` (commodity) | 1 perces commodity | PREMIUM | TODO | `feature/fmp-commodities` |

---

## 3.21 Congressional Trading

**Branch:** `feature/fmp-congress`
**Modul:** `src/data_loader/providers/fmp/congress.py`
**Endpoints:** 6

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.21.01 | `senate-latest` | Szenátus kereskedés | FREE | TODO | `feature/fmp-congress` |
| 3.21.02 | `house-latest` | Képviselőház kereskedés | FREE | TODO | `feature/fmp-congress` |
| 3.21.03 | `senate-trades` | Szenátus trades (ticker) | FREE | TODO | `feature/fmp-congress` |
| 3.21.04 | `house-trades` | House trades (ticker) | FREE | TODO | `feature/fmp-congress` |
| 3.21.05 | `senate-trades-by-name` | Keresés név szerint | FREE | TODO | `feature/fmp-congress` |
| 3.21.06 | `house-trades-by-name` | Keresés név szerint | FREE | TODO | `feature/fmp-congress` |

---

## 3.22 ESG

**Branch:** `feature/fmp-esg`
**Modul:** `src/data_loader/providers/fmp/esg.py`
**Endpoints:** 3

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.22.01 | `esg-disclosures` | ESG disclosure-ök | FREE | TODO | `feature/fmp-esg` |
| 3.22.02 | `esg-ratings` | ESG ratingek | FREE | TODO | `feature/fmp-esg` |
| 3.22.03 | `esg-benchmark` | ESG benchmark | FREE | TODO | `feature/fmp-esg` |

---

## 3.23 DCF Valuation

**Branch:** `feature/fmp-dcf`
**Modul:** `src/data_loader/providers/fmp/dcf.py`
**Endpoints:** 4

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.23.01 | `discounted-cash-flow` | DCF értékelés | FREE | TODO | `feature/fmp-dcf` |
| 3.23.02 | `levered-discounted-cash-flow` | Levered DCF | FREE | TODO | `feature/fmp-dcf` |
| 3.23.03 | `custom-discounted-cash-flow` | Egyedi DCF | FREE | TODO | `feature/fmp-dcf` |
| 3.23.04 | `custom-levered-discounted-cash-flow` | Egyedi Levered DCF | FREE | TODO | `feature/fmp-dcf` |

---

## 3.24 Other

**Branch:** `feature/fmp-other`
**Modul:** `src/data_loader/providers/fmp/other.py`
**Endpoints:** 4

| ID | Endpoint | Leírás | Tier | Státusz | Branch |
|----|----------|--------|------|---------|--------|
| 3.24.01 | `commitment-of-traders-report` | COT Report | FREE | TODO | `feature/fmp-other` |
| 3.24.02 | `crowdfunding-offerings` | Crowdfunding | FREE | TODO | `feature/fmp-other` |
| 3.24.03 | `exchange-market-hours` | Piaci órák | FREE | TODO | `feature/fmp-other` |
| 3.24.04 | `holidays-by-exchange` | Tőzsdei szünnapok | FREE | TODO | `feature/fmp-other` |

---

## Összesítés

### Státusz szerint

| Státusz | Szám | Százalék |
|---------|------|----------|
| EXISTING | 13 | 6.9% |
| TODO | 176 | 93.1% |
| IN_PROGRESS | 0 | 0% |
| DONE | 0 | 0% |
| **TOTAL** | **189** | 100% |

### Tier szerint

| Tier | Szám | Százalék |
|------|------|----------|
| FREE | 172 | 91% |
| PREMIUM | 17 | 9% |

### Kategória szerint

| Kategória | Total | Existing | TODO |
|-----------|-------|----------|------|
| 3.1 Search | 12 | 0 | 12 |
| 3.2 Company | 13 | 1 | 12 |
| 3.3 Quotes | 13 | 1 | 12 |
| 3.4 Financials | 22 | 5 | 17 |
| 3.5 Charts | 10 | 1 | 9 |
| 3.6 Economics | 4 | 0 | 4 |
| 3.7 Calendars | 9 | 3 | 6 |
| 3.8 Transcripts | 4 | 0 | 4 |
| 3.9 News | 9 | 0 | 9 |
| 3.10 Institutional | 7 | 0 | 7 |
| 3.11 Analyst | 8 | 2 | 6 |
| 3.12 Performance | 9 | 0 | 9 |
| 3.13 Technical | 9 | 0 | 9 |
| 3.14 ETF | 7 | 0 | 7 |
| 3.15 SEC | 7 | 0 | 7 |
| 3.16 Insider | 6 | 0 | 6 |
| 3.17 Indexes | 7 | 0 | 7 |
| 3.18 Forex | 6 | 0 | 6 |
| 3.19 Crypto | 6 | 0 | 6 |
| 3.20 Commodities | 4 | 0 | 4 |
| 3.21 Congress | 6 | 0 | 6 |
| 3.22 ESG | 3 | 0 | 3 |
| 3.23 DCF | 4 | 0 | 4 |
| 3.24 Other | 4 | 0 | 4 |
| **TOTAL** | **189** | **13** | **176** |

---

## Revision History

| Verzió | Dátum | Változás |
|--------|-------|----------|
| v1.0 | 2026-02-01 | Initial tracker with 189 endpoints |

---

*Kapcsolódó dokumentum: [ACTION_PLAN_FMP.md](ACTION_PLAN_FMP.md)*
