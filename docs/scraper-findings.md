# Scraper findings for indicator extraction

## Objective

Document which indicators are available in the saved live HTML examples so we can later implement a reliable scraper for each data source.

## Sources reviewed

1. `live html web page examples/WEGE3 - WEG ON_ cotação e indicadores _ Status Invest.html`
2. `live html web page examples/Medical Properties Trust, Inc. (MPT) Stock Price, News, Quote & History - Yahoo Finance.html`

## Findings by source

### 1) Status Invest (WEGE3)

This page contains explicit indicator names and a structured payload that is easier to parse than relying on visible text alone.

Observed keys and labels:

- `p_l` → P/L
- `p_vp` → P/VP
- `dy` → Dividend Yield
- `margemliquida` / `margem_liquida` → Margem Líquida / Profit Margin
- `receitas_cagr5` → 5-year revenue CAGR
- `lucros_cagr5` → 5-year earnings CAGR
- Other comparable financial metrics and hidden JSON-like values were also found in the page payload

Important observations:

- The page includes visible headings such as `P/L` and `P/VP`.
- It also includes data attributes such as `data-key="margemliquida"` and `data-name="P/VP"`.
- There is a hidden/inlined JSON-type indicator payload containing the actual values, which is the preferred extraction strategy for a scraper.

Recommended extraction method:

- Prefer parsing the hidden indicator payload or structured data-attributes instead of plain text scraping.
- Use the stable keys (`p_l`, `p_vp`, `dy`, `margemliquida`, `receitas_cagr5`, `lucros_cagr5`) as canonical field names in the scraper mapping layer.

### 2) Yahoo Finance (MPT)

This page is much more dynamic and heavy on JavaScript. It still contains embedded structured data, but extraction is less straightforward than the Status Invest page.

Observed / likely keys found in or implied by the page payload:

- `trailingPE`
- `forwardPE`
- `dividendYield`
- `profitMargins`
- `priceToBook`
- `pegRatio`

Additional notes:

- This page appears to hydrate values from embedded JSON or script data rather than purely from visible DOM text.
- The static file is large and JS-driven, which means direct CSS selectors are less reliable than targeting server-rendered JSON structures when available.
- FFO (Funds From Operations) is not clearly visible in the sample static HTML preview. For REITs specifically, FFO may not be present in the same data block as the main valuation metrics and may require a secondary page or another source.

Recommended extraction method:

- Parse the embedded JSON/script objects rather than reading the rendered page visually.
- For Yahoo, prefer keys like `trailingPE`, `dividendYield`, `profitMargins`, and `priceToBook` when mapping to the project metric model.
- For FFO/REIT-specific metrics, use a fallback source if needed.

## Indicator mapping by class

### Valuation / price multiples

- `p_l` / `trailingPE` / `forwardPE`
- `p_vp` / `priceToBook`

### Yield / profitability

- `dy` / `dividendYield`
- `margemliquida` / `profitMargins`

### Growth

- `receitas_cagr5`
- `lucros_cagr5`

### REIT-specific / optional metrics

- `ffo` (if available from a fallback source)

## Recommended implementation approach for the scraper

1. Build a source adapter per website:
   - `statusinvest`: parse JSON/data-attributes and map keys directly.
   - `yahoo_finance`: parse script/embedded JSON and map to normalized metric keys.

2. Normalize values before saving:
   - Convert percentages like `15,58%` and `2,40%` to numeric decimal values.
   - Strip currency symbols and locale separators where needed.

3. Standardize metric keys in the app:
   - Example canonical names:
     - `p_l`
     - `p_vp`
     - `dy`
     - `margem_liquida`
     - `receitas_cagr5`
     - `lucros_cagr5`
     - `profit_margins`
     - `trailing_pe`
     - `price_to_book`
     - `dividend_yield`

4. Save to the time-series model (`MetricHistory`) with timestamp and source metadata.

## Conclusion

The Status Invest example is the clearest source for the required indicator fields and should be implemented first. The Yahoo Finance example is valid for broader valuation metrics but will require a more resilient embedded-data parsing approach and may need a fallback for REIT-specific values like FFO.
