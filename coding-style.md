# Notebook coding style: detailed

How notebooks in this folder are written (established with `product_sales_dataset.ipynb`).
The goal in one sentence: **someone reading a cell for the first time understands every
line without guessing.**

## 1. Markdown: brief and straight to the point

- Each section gets a numbered heading (`## 3 - Daily product sales`) and at most 1 to 3
  lines of text.
- The text says only what the section does and any non-obvious decision
  ("the export's rows are in insert order rather than date order, so select by mask
  instead of slice").
- No long explanations, no tutorials, no restating what the code already shows.
- Notes about caveats or expectations go in one short quote block if truly needed.

**Do:**
```markdown
## 5 - Resample prices to daily + derived margins
Linear interpolation in time between recorded price changes, per product and channel;
dates before the first / after the last change take the nearest one.
```

**Don't:** three paragraphs describing what interpolation is.

## 2. Full words in names, no invented abbreviations

- Variables, functions, and columns use complete words: `customer_index`,
  `active_products`, `train_features`, `build_category_tree`, `sample_prices_at_products`.
- Never invent shorthand: no `cust_idx`, `df2`, `tmp`, `res`, `prd`, `mk_tree`.
- A **well-known acronym is allowed when it is the preferred, recognized term**:
  SKU, API, CSV, JSON, UTC, ISO. Prefer the full word whenever a full word is just as
  natural (`quantity` rather than `qty`, `category` rather than `cat`).
- Conventional import aliases are fine because they are universal: `np`, `pd`, `plt`.
  Everything else is imported by full name (`import requests`, `import sqlalchemy`,
  `import lightgbm`).
- Config constants are UPPER_CASE and self-describing: `CATEGORY_DEPTH`,
  `MAX_RETURN_RATE`, `PRICE_CHANNELS`, `START_DATE`.

## 3. One to three operations per line

- A line may do one, two, at most three things. If a line is doing more, split it and
  name the intermediate results.
- Creating more variables is explicitly fine. Variables are documentation.
- No deeply nested calls; the reader must never have to mentally unwind
  `f(g(h(x)[0]).y.z(...))`.
- Method chains: keep to 2 or 3 short links, otherwise break the chain across named steps.
- Comments only where the code cannot speak for itself (a unit, a data quirk, an index
  convention), placed at the end of the line or just above it, one line long.

**Do:**
```python
table = price_rows.pivot(index="date", columns="product_id", values=channel)
full_index = table.index.union(daily_dates)
table = table.reindex(full_index)
table = table.interpolate(method="time", limit_direction="both")
```

**Don't:**
```python
table = price_rows.pivot(index="date", columns="product_id", values=channel).reindex(
    price_rows.pivot(index="date", columns="product_id", values=channel).index.union(
        daily_dates)).interpolate(method="time", limit_direction="both")
```

## 4. Config-driven: change a knob, re-run from the top

- One setup cell holds every knob: date range, aggregation level, quality filter, column
  list, segment list with roles. Everything downstream derives from these, and nothing is
  hardcoded twice.
- Time ranges and resolutions are dynamic: two weeks or two months, daily or weekly must
  work by editing only the constant.
- Derived values (window length in days, sampling step) are computed from the knobs in the
  same cell, with a `print` showing the effective values.
- Secrets and credentials load from the repository's ignored secrets folder, never inline.

## 5. Show every data source

- After each collection step, print a one-line summary with concrete numbers:
  `"North region: 855,120 rows (336 days x 2545 products)"`.
- Follow each data source with a quick plot (distribution, time series, sample table) and,
  where useful, a small `.describe()` table. The data must be seen rather than assumed.
- Plots scale with the config (for example one panel per segment via `len(SEGMENTS)`), so
  adding a segment never breaks the figure.

## 6. General structure

- Numbered sections, one concern per section: entities → grouping → primary source →
  secondary sources → joining → features → split → model → evaluation → importance.
- Functions are small, take explicit arguments, and carry a one-line docstring stating what
  they return.
- Prefer a package that already solves the problem over manual work (`category_encoders`
  over a hand-rolled mapping loop); install it in the pip cell.
- Alternative paths (for example a second training strategy) live in their own clearly
  marked cell with a note saying "run this instead of the cell above".
