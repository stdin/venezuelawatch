# Venezuela Risk Signal Platform — System Design

## 1. Overview

A premium data signal platform providing real-time risk intelligence on Venezuela for commodity traders and investors. The system ingests heterogeneous data sources, normalizes them into a canonical event model, assigns severity and risk scores, and delivers signals via API, dashboard, alerts, and reports.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA SOURCES                                   │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────┬───────┤
│   GDELT     │   ACLED     │ World Bank  │   Google    │ SEC EDGAR   │ FRED  │
│             │             │             │   Trends    │             │       │
├─────────────┴─────────────┴─────────────┴─────────────┴─────────────┴───────┤
│                          UN Comtrade                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          INGESTION LAYER                                    │
│                   (source-specific extractors)                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          RAW STORAGE                                        │
│              (source-native schemas, append-only)                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       NORMALIZATION LAYER                                   │
│              (transform to canonical event model)                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CANONICAL EVENT TABLE                                 │
│                    (unified schema, all sources)                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PROCESSING LAYER                                     │
├─────────────────────────┬───────────────────────────────────────────────────┤
│   SEVERITY ASSIGNMENT   │              SCORING ENGINE                       │
│       (P1-P4)           │    (composite + 10 category sub-scores)           │
└─────────────────────────┴───────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SCORED EVENT TABLE                                  │
│         (event + severity + risk_score + sub_scores)                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
             ┌───────────┐   ┌───────────┐   ┌───────────┐
             │ AGGREGATE │   │   ALERT   │   │   TREND   │
             │  SCORES   │   │  ENGINE   │   │  CALC     │
             │  (daily)  │   │           │   │           │
             └───────────┘   └───────────┘   └───────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          OUTPUT LAYER                                       │
├─────────────────┬─────────────────┬─────────────────┬───────────────────────┤
│      API        │    DASHBOARD    │     ALERTS      │       REPORTS         │
│  (near real-    │  (near real-    │  (near real-    │   (daily/weekly)      │
│     time)       │     time)       │     time)       │                       │
└─────────────────┴─────────────────┴─────────────────┴───────────────────────┘
```

---

## 3. Data Sources

| Source | Data Type | Refresh Rate | Venezuela Filter | Key Fields |
|--------|-----------|--------------|------------------|------------|
| **GDELT** | News events | 15 min | `ActionGeo_CountryCode = 'VE'` | GoldsteinScale, AvgTone, NumSources, NumArticles, CAMEO codes |
| **ACLED** | Conflict events | Daily | `country = 'Venezuela'` | event_type, fatalities, actor1, actor2, location |
| **World Bank** | Macro indicators | Quarterly | `country_code = 'VEN'` | GDP, inflation, FDI, trade balance |
| **Google Trends** | Search interest | Daily | Venezuela-related terms | interest_score (0-100) |
| **SEC EDGAR** | Company filings | Daily | Text search "Venezuela" | filing_type, company, risk_mentions |
| **FRED** | Economic data | Daily/Weekly | Venezuela series | exchange_rate, bond_spreads |
| **UN Comtrade** | Trade flows | Monthly | `reporter/partner = 862` | commodity_code, trade_value, quantity |

---

## 4. Data Model

### 4.1 Raw Tables (source-native)

```sql
-- One table per source, preserving original schema
raw_gdelt
raw_acled
raw_world_bank
raw_google_trends
raw_sec_edgar
raw_fred
raw_un_comtrade
```

### 4.2 Canonical Event Table

```sql
CREATE TABLE canonical_events (
    -- Identity
    event_id            STRING,         -- UUID
    source              STRING,         -- 'gdelt' | 'acled' | 'world_bank' | etc.
    source_event_id     STRING,         -- original ID from source
    
    -- Temporal
    event_timestamp     TIMESTAMP,      -- when event occurred
    ingested_at         TIMESTAMP,      -- when we ingested it
    
    -- Classification
    category            STRING,         -- POLITICAL | CONFLICT | ECONOMIC | TRADE | 
                                        -- REGULATORY | INFRASTRUCTURE | HEALTHCARE |
                                        -- SOCIAL | ENVIRONMENTAL | ENERGY
    subcategory         STRING,         -- finer grain classification
    event_type          STRING,         -- source-specific event type
    
    -- Location
    country_code        STRING,         -- 'VE'
    admin1              STRING,         -- state/province
    admin2              STRING,         -- city/district
    latitude            FLOAT64,
    longitude           FLOAT64,
    
    -- Magnitude
    magnitude_raw       FLOAT64,        -- native value (deaths, %, Goldstein, etc.)
    magnitude_unit      STRING,         -- 'fatalities' | 'percent' | 'goldstein' | 'usd'
    magnitude_norm      FLOAT64,        -- 0-1 normalized
    
    -- Sentiment/Direction
    direction           STRING,         -- POSITIVE | NEGATIVE | NEUTRAL
    tone_raw            FLOAT64,        -- native tone score if available
    tone_norm           FLOAT64,        -- 0-1 normalized (1 = most negative)
    
    -- Confidence
    num_sources         INT64,          -- number of sources reporting
    source_credibility  FLOAT64,        -- 0-1 source tier weight
    confidence          FLOAT64,        -- 0-1 composite confidence
    
    -- Actors
    actor1_name         STRING,
    actor1_type         STRING,         -- GOVERNMENT | MILITARY | REBEL | CIVILIAN | CORPORATE
    actor2_name         STRING,
    actor2_type         STRING,
    
    -- Commodities/Sectors (if applicable)
    commodities         ARRAY<STRING>,  -- ['OIL', 'GOLD', etc.]
    sectors             ARRAY<STRING>,  -- ['ENERGY', 'MINING', etc.]
    
    -- Raw payload
    raw_payload         JSON,           -- original record for traceability
    
    -- Metadata
    created_at          TIMESTAMP,
    updated_at          TIMESTAMP
);
```

### 4.3 Scored Event Table

```sql
CREATE TABLE scored_events (
    -- Foreign key
    event_id            STRING,
    
    -- Severity
    severity            STRING,         -- P1 | P2 | P3 | P4
    severity_reason     STRING,         -- why this severity was assigned
    severity_auto       BOOLEAN,        -- true if auto-P1 trigger
    
    -- Risk Score
    risk_score          FLOAT64,        -- 0-100 composite
    
    -- Category Sub-Scores (0-100 each)
    score_political     FLOAT64,
    score_conflict      FLOAT64,
    score_economic      FLOAT64,
    score_trade         FLOAT64,
    score_regulatory    FLOAT64,
    score_infrastructure FLOAT64,
    score_healthcare    FLOAT64,
    score_social        FLOAT64,
    score_environmental FLOAT64,
    score_energy        FLOAT64,
    
    -- Score Components (for explainability)
    magnitude_contrib   FLOAT64,
    tone_contrib        FLOAT64,
    velocity_contrib    FLOAT64,
    attention_contrib   FLOAT64,
    persistence_contrib FLOAT64,
    confidence_mod      FLOAT64,
    
    -- Metadata
    scored_at           TIMESTAMP
);
```

### 4.4 Aggregate Tables

```sql
-- Daily aggregates for dashboard/reports
CREATE TABLE daily_risk_summary (
    date                DATE,
    
    -- Composite
    risk_score          FLOAT64,        -- daily composite (0-100)
    risk_score_change   FLOAT64,        -- vs. previous day
    risk_trend          STRING,         -- RISING | FALLING | STABLE
    
    -- Category sub-scores
    score_political     FLOAT64,
    score_conflict      FLOAT64,
    score_economic      FLOAT64,
    score_trade         FLOAT64,
    score_regulatory    FLOAT64,
    score_infrastructure FLOAT64,
    score_healthcare    FLOAT64,
    score_social        FLOAT64,
    score_environmental FLOAT64,
    score_energy        FLOAT64,
    
    -- Event counts
    total_events        INT64,
    p1_events           INT64,
    p2_events           INT64,
    p3_events           INT64,
    p4_events           INT64,
    
    -- Trend indicators
    velocity_7d         FLOAT64,        -- 7-day velocity
    velocity_30d        FLOAT64,        -- 30-day velocity
    
    -- Metadata
    created_at          TIMESTAMP
);

-- Rolling windows for trend calculation
CREATE TABLE rolling_metrics (
    date                DATE,
    window_days         INT64,          -- 7, 14, 30, 90
    
    avg_risk_score      FLOAT64,
    stddev_risk_score   FLOAT64,
    avg_event_count     FLOAT64,
    stddev_event_count  FLOAT64,
    
    -- Per category
    avg_score_political FLOAT64,
    -- ... (repeat for all 10 categories)
    
    created_at          TIMESTAMP
);
```

---

## 5. Normalization Layer

### 5.1 Category Mapping

```python
CATEGORY_MAP = {
    # GDELT CAMEO root codes → Category
    "gdelt": {
        "01": "POLITICAL",      # Make public statement
        "02": "POLITICAL",      # Appeal
        "03": "POLITICAL",      # Express intent to cooperate
        "04": "POLITICAL",      # Consult
        "05": "POLITICAL",      # Diplomatic cooperation
        "06": "ECONOMIC",       # Material cooperation
        "07": "ECONOMIC",       # Provide aid
        "08": "POLITICAL",      # Yield
        "09": "POLITICAL",      # Investigate
        "10": "POLITICAL",      # Demand
        "11": "POLITICAL",      # Disapprove
        "12": "POLITICAL",      # Reject
        "13": "CONFLICT",       # Threaten
        "14": "CONFLICT",       # Protest
        "15": "REGULATORY",     # Exhibit force posture
        "16": "ECONOMIC",       # Reduce relations
        "17": "CONFLICT",       # Coerce
        "18": "CONFLICT",       # Assault
        "19": "CONFLICT",       # Fight
        "20": "CONFLICT",       # Use unconventional mass violence
    },
    
    # ACLED event types → Category
    "acled": {
        "Battles": "CONFLICT",
        "Explosions/Remote violence": "CONFLICT",
        "Violence against civilians": "CONFLICT",
        "Protests": "SOCIAL",
        "Riots": "CONFLICT",
        "Strategic developments": "POLITICAL",
    },
    
    # World Bank indicators → Category
    "world_bank": {
        "NY.GDP": "ECONOMIC",
        "FP.CPI": "ECONOMIC",
        "BX.KLT": "ECONOMIC",       # FDI
        "NE.EXP": "TRADE",
        "NE.IMP": "TRADE",
        "SH.": "HEALTHCARE",
        "EG.": "ENERGY",
    },
    
    # Google Trends terms → Category
    "google_trends": {
        "venezuela sanctions": "REGULATORY",
        "venezuela oil": "ENERGY",
        "venezuela crisis": "POLITICAL",
        "venezuela inflation": "ECONOMIC",
        "venezuela protests": "SOCIAL",
        "pdvsa": "ENERGY",
        "maduro": "POLITICAL",
        "guaido": "POLITICAL",
    },
    
    # SEC filing risk terms → Category
    "sec_edgar": {
        "sanction": "REGULATORY",
        "nationalization": "REGULATORY",
        "expropriation": "REGULATORY",
        "currency": "ECONOMIC",
        "hyperinflation": "ECONOMIC",
        "oil": "ENERGY",
        "pdvsa": "ENERGY",
    },
    
    # FRED series → Category
    "fred": {
        "EXVZUS": "ECONOMIC",       # Exchange rate
        "VENEZUEL": "ECONOMIC",     # Various indicators
    },
    
    # UN Comtrade → Category
    "un_comtrade": {
        "27": "ENERGY",             # Mineral fuels, oils (includes crude oil)
        "71": "TRADE",              # Precious stones, metals
        "26": "TRADE",              # Ores, slag, ash
        "default": "TRADE",
    },
}
```

### 5.2 Source-Specific Normalizers

```python
def normalize_gdelt(row: dict) -> dict:
    """Transform GDELT event to canonical schema."""
    cameo_root = row["EventCode"][:2]
    goldstein = row["GoldsteinScale"]  # -10 to +10
    
    return {
        "event_id": generate_uuid(),
        "source": "gdelt",
        "source_event_id": row["GLOBALEVENTID"],
        "event_timestamp": parse_gdelt_date(row["SQLDATE"]),
        "category": CATEGORY_MAP["gdelt"].get(cameo_root, "POLITICAL"),
        "subcategory": row["EventCode"],
        "event_type": row["EventCode"],
        "country_code": "VE",
        "admin1": row.get("ActionGeo_ADM1Code"),
        "latitude": row.get("ActionGeo_Lat"),
        "longitude": row.get("ActionGeo_Long"),
        "magnitude_raw": goldstein,
        "magnitude_unit": "goldstein",
        "magnitude_norm": (goldstein + 10) / 20,  # → 0-1
        "direction": "NEGATIVE" if goldstein < -2 else ("POSITIVE" if goldstein > 2 else "NEUTRAL"),
        "tone_raw": row["AvgTone"],
        "tone_norm": min(max((row["AvgTone"] * -1 + 10) / 20, 0), 1),  # invert: negative tone → higher
        "num_sources": row["NumSources"],
        "source_credibility": 0.7,  # baseline for GDELT
        "confidence": min(row["NumSources"] / 10, 1.0) * 0.7,
        "actor1_name": row.get("Actor1Name"),
        "actor1_type": classify_actor(row.get("Actor1Type1Code")),
        "actor2_name": row.get("Actor2Name"),
        "actor2_type": classify_actor(row.get("Actor2Type1Code")),
        "commodities": extract_commodities_from_cameo(row["EventCode"]),
        "sectors": extract_sectors_from_cameo(row["EventCode"]),
        "raw_payload": row,
    }


def normalize_acled(row: dict) -> dict:
    """Transform ACLED event to canonical schema."""
    fatalities = row.get("fatalities", 0)
    
    return {
        "event_id": generate_uuid(),
        "source": "acled",
        "source_event_id": row["data_id"],
        "event_timestamp": parse_acled_date(row["event_date"]),
        "category": CATEGORY_MAP["acled"].get(row["event_type"], "CONFLICT"),
        "subcategory": row.get("sub_event_type"),
        "event_type": row["event_type"],
        "country_code": "VE",
        "admin1": row.get("admin1"),
        "admin2": row.get("admin2"),
        "latitude": row.get("latitude"),
        "longitude": row.get("longitude"),
        "magnitude_raw": fatalities,
        "magnitude_unit": "fatalities",
        "magnitude_norm": sigmoid_norm(fatalities, k=0.3),  # ~10 fatalities → 0.95
        "direction": "NEGATIVE",
        "tone_raw": None,
        "tone_norm": 0.8 if fatalities > 0 else 0.5,
        "num_sources": row.get("source_count", 1),
        "source_credibility": 0.9,  # ACLED is curated
        "confidence": 0.9,
        "actor1_name": row.get("actor1"),
        "actor1_type": classify_acled_actor(row.get("actor1")),
        "actor2_name": row.get("actor2"),
        "actor2_type": classify_acled_actor(row.get("actor2")),
        "commodities": [],
        "sectors": [],
        "raw_payload": row,
    }


def normalize_world_bank(row: dict) -> dict:
    """Transform World Bank indicator to canonical schema."""
    value = row["value"]
    prev_value = row.get("prev_value", value)
    pct_change = ((value - prev_value) / prev_value * 100) if prev_value else 0
    
    # Determine direction based on indicator type
    indicator = row["indicator_code"]
    negative_is_bad = indicator.startswith(("FP.CPI", "SL.UEM"))  # inflation, unemployment
    
    if negative_is_bad:
        direction = "NEGATIVE" if pct_change > 0 else "POSITIVE"
    else:
        direction = "POSITIVE" if pct_change > 0 else "NEGATIVE"
    
    return {
        "event_id": generate_uuid(),
        "source": "world_bank",
        "source_event_id": f"{indicator}_{row['year']}",
        "event_timestamp": date_from_year(row["year"]),
        "category": categorize_wb_indicator(indicator),
        "subcategory": indicator,
        "event_type": "INDICATOR_UPDATE",
        "country_code": "VE",
        "admin1": None,
        "latitude": None,
        "longitude": None,
        "magnitude_raw": pct_change,
        "magnitude_unit": "percent_change",
        "magnitude_norm": min(abs(pct_change) / 50, 1.0),  # 50% change = 1.0
        "direction": direction,
        "tone_raw": None,
        "tone_norm": 0.5,  # neutral for data
        "num_sources": 1,
        "source_credibility": 0.95,
        "confidence": 0.95,
        "actor1_name": None,
        "actor1_type": None,
        "actor2_name": None,
        "actor2_type": None,
        "commodities": [],
        "sectors": [],
        "raw_payload": row,
    }


def normalize_google_trends(row: dict) -> dict:
    """Transform Google Trends data to canonical schema."""
    interest = row["interest"]  # 0-100
    baseline = row.get("baseline_interest", 25)
    spike_ratio = interest / baseline if baseline > 0 else 1
    
    return {
        "event_id": generate_uuid(),
        "source": "google_trends",
        "source_event_id": f"{row['term']}_{row['date']}",
        "event_timestamp": row["date"],
        "category": CATEGORY_MAP["google_trends"].get(row["term"].lower(), "POLITICAL"),
        "subcategory": row["term"],
        "event_type": "SEARCH_SPIKE" if spike_ratio > 2 else "SEARCH_LEVEL",
        "country_code": "VE",
        "admin1": None,
        "latitude": None,
        "longitude": None,
        "magnitude_raw": interest,
        "magnitude_unit": "interest_score",
        "magnitude_norm": interest / 100,
        "direction": "NEGATIVE",  # assume elevated attention = concern
        "tone_raw": None,
        "tone_norm": min(spike_ratio / 5, 1.0),  # 5x spike = max concern
        "num_sources": 1,
        "source_credibility": 0.8,
        "confidence": 0.8,
        "actor1_name": None,
        "actor1_type": None,
        "actor2_name": None,
        "actor2_type": None,
        "commodities": extract_commodities_from_term(row["term"]),
        "sectors": extract_sectors_from_term(row["term"]),
        "raw_payload": row,
    }


def normalize_sec_edgar(row: dict) -> dict:
    """Transform SEC filing to canonical schema."""
    mention_count = row.get("venezuela_mentions", 1)
    risk_language_score = row.get("risk_language_score", 0.5)
    
    return {
        "event_id": generate_uuid(),
        "source": "sec_edgar",
        "source_event_id": row["accession_number"],
        "event_timestamp": row["filing_date"],
        "category": categorize_sec_content(row.get("context_text", "")),
        "subcategory": row["filing_type"],
        "event_type": row["filing_type"],
        "country_code": "VE",
        "admin1": None,
        "latitude": None,
        "longitude": None,
        "magnitude_raw": mention_count,
        "magnitude_unit": "mentions",
        "magnitude_norm": min(mention_count / 20, 1.0),
        "direction": "NEGATIVE" if risk_language_score > 0.5 else "NEUTRAL",
        "tone_raw": risk_language_score,
        "tone_norm": risk_language_score,
        "num_sources": 1,
        "source_credibility": 0.95,
        "confidence": 0.9,
        "actor1_name": row.get("company_name"),
        "actor1_type": "CORPORATE",
        "actor2_name": None,
        "actor2_type": None,
        "commodities": extract_commodities_from_text(row.get("context_text", "")),
        "sectors": [row.get("sic_sector", "UNKNOWN")],
        "raw_payload": row,
    }


def normalize_fred(row: dict) -> dict:
    """Transform FRED economic data to canonical schema."""
    value = row["value"]
    prev_value = row.get("prev_value", value)
    pct_change = ((value - prev_value) / prev_value * 100) if prev_value else 0
    
    return {
        "event_id": generate_uuid(),
        "source": "fred",
        "source_event_id": f"{row['series_id']}_{row['date']}",
        "event_timestamp": row["date"],
        "category": "ECONOMIC",
        "subcategory": row["series_id"],
        "event_type": "INDICATOR_UPDATE",
        "country_code": "VE",
        "admin1": None,
        "latitude": None,
        "longitude": None,
        "magnitude_raw": pct_change,
        "magnitude_unit": "percent_change",
        "magnitude_norm": min(abs(pct_change) / 20, 1.0),
        "direction": "NEGATIVE" if pct_change < 0 else "POSITIVE",
        "tone_raw": None,
        "tone_norm": 0.5,
        "num_sources": 1,
        "source_credibility": 0.95,
        "confidence": 0.95,
        "actor1_name": None,
        "actor1_type": None,
        "actor2_name": None,
        "actor2_type": None,
        "commodities": [],
        "sectors": [],
        "raw_payload": row,
    }


def normalize_un_comtrade(row: dict) -> dict:
    """Transform UN Comtrade data to canonical schema."""
    trade_value = row["trade_value"]
    prev_value = row.get("prev_period_value", trade_value)
    pct_change = ((trade_value - prev_value) / prev_value * 100) if prev_value else 0
    
    commodity_code = str(row["commodity_code"])[:2]
    category = CATEGORY_MAP["un_comtrade"].get(commodity_code, "TRADE")
    
    return {
        "event_id": generate_uuid(),
        "source": "un_comtrade",
        "source_event_id": f"{row['commodity_code']}_{row['period']}_{row['flow']}",
        "event_timestamp": period_to_date(row["period"]),
        "category": category,
        "subcategory": row["commodity_code"],
        "event_type": row["flow"],  # Import or Export
        "country_code": "VE",
        "admin1": None,
        "latitude": None,
        "longitude": None,
        "magnitude_raw": pct_change,
        "magnitude_unit": "percent_change",
        "magnitude_norm": min(abs(pct_change) / 50, 1.0),
        "direction": "POSITIVE" if pct_change > 0 else "NEGATIVE",
        "tone_raw": None,
        "tone_norm": 0.5,
        "num_sources": 1,
        "source_credibility": 0.9,
        "confidence": 0.9,
        "actor1_name": None,
        "actor1_type": None,
        "actor2_name": None,
        "actor2_type": None,
        "commodities": [map_hs_to_commodity(commodity_code)],
        "sectors": [map_hs_to_sector(commodity_code)],
        "raw_payload": row,
    }
```

---

## 6. Severity Assignment

### 6.1 P1 Auto-Triggers (Immediate)

These events are automatically P1 regardless of other factors:

```python
P1_AUTO_TRIGGERS = {
    # Event type patterns
    "event_types": [
        "COUP",
        "COUP_ATTEMPT", 
        "NATIONALIZATION",
        "EXPROPRIATION",
        "SOVEREIGN_DEFAULT",
        "MILITARY_INTERVENTION",
        "HEAD_OF_STATE_REMOVED",
        "OIL_EXPORT_HALT",
    ],
    
    # CAMEO codes (GDELT)
    "cameo_codes": [
        "192",  # Engage in ethnic cleansing
        "193",  # Conduct suicide, car, or other non-military bombing
        "194",  # Use weapons of mass destruction
        "195",  # Assassinate
        "1031", # Coup d'etat
    ],
    
    # Keyword patterns (for text-based sources)
    "keywords": [
        r"coup\s+(attempt|d'état)?",
        r"nationali[sz](e|ation)",
        r"expropriate?",
        r"sovereign\s+default",
        r"sanctions?\s+(announced|imposed)",
        r"oil\s+export\s+(halt|stop|ban)",
        r"pdvsa\s+(seize|shutdown|halt)",
    ],
    
    # Thresholds
    "fatality_threshold": 10,
}
```

### 6.2 Severity Classification Logic

```python
def assign_severity(event: dict) -> tuple[str, str]:
    """
    Assign severity (P1-P4) to a canonical event.
    Returns (severity, reason).
    """
    
    # ============ P1: CRITICAL ============
    # Auto-triggers
    if matches_auto_trigger(event):
        return "P1", f"Auto-trigger: {get_trigger_reason(event)}"
    
    # 10+ fatalities
    if event["magnitude_unit"] == "fatalities" and event["magnitude_raw"] >= 10:
        return "P1", f"High fatalities: {event['magnitude_raw']}"
    
    # Direct oil/export disruption with high confidence
    if (event["category"] == "ENERGY" and 
        "OIL" in event.get("commodities", []) and
        event["direction"] == "NEGATIVE" and
        event["magnitude_norm"] > 0.8):
        return "P1", "Major oil/energy disruption"
    
    # ============ P2: HIGH ============
    # 1-9 fatalities
    if event["magnitude_unit"] == "fatalities" and 1 <= event["magnitude_raw"] < 10:
        return "P2", f"Fatalities: {event['magnitude_raw']}"
    
    # Major policy shift
    if (event["category"] in ["POLITICAL", "REGULATORY"] and
        event["magnitude_norm"] > 0.7 and
        event["direction"] == "NEGATIVE"):
        return "P2", "Significant policy/regulatory event"
    
    # Currency/economic shock
    if (event["category"] == "ECONOMIC" and
        event["magnitude_unit"] == "percent_change" and
        abs(event["magnitude_raw"]) > 10):
        return "P2", f"Major economic shift: {event['magnitude_raw']:.1f}%"
    
    # Regional violence/protests
    if (event["category"] == "CONFLICT" and
        event["magnitude_norm"] > 0.5 and
        event["admin1"] is not None):
        return "P2", "Significant regional conflict event"
    
    # ============ P3: MODERATE ============
    # Moderate impact, contained
    if (event["direction"] == "NEGATIVE" and
        0.3 < event["magnitude_norm"] <= 0.7):
        return "P3", "Moderate negative event"
    
    # Protests without violence
    if (event["event_type"] in ["Protests", "PROTEST"] and
        event.get("magnitude_raw", 0) == 0):
        return "P3", "Protest activity (no casualties)"
    
    # Minor regulatory changes
    if (event["category"] == "REGULATORY" and
        event["magnitude_norm"] <= 0.5):
        return "P3", "Minor regulatory event"
    
    # ============ P4: LOW ============
    # Everything else
    return "P4", "Low impact / informational"
```

### 6.3 Severity Summary

| Severity | Criteria | Examples |
|----------|----------|----------|
| **P1** | Auto-triggers, 10+ fatalities, direct oil disruption | Coup, nationalization, PDVSA shutdown, mass casualty event |
| **P2** | 1-9 fatalities, major policy shift, >10% economic swing, regional violence | Protests with deaths, currency devaluation, senior official resignation |
| **P3** | Moderate impact (0.3-0.7 norm), no fatalities, contained | Routine protests, minor policy changes, infrastructure outage |
| **P4** | Low impact (<0.3 norm), informational | Political speeches, diplomatic meetings, routine data releases |

---

## 7. Scoring Engine

### 7.1 Event-Level Risk Score

```python
def calculate_risk_score(event: dict, rolling_stats: dict) -> dict:
    """
    Calculate risk score (0-100) for a single event.
    Returns dict with score and all components.
    """
    
    # ============ COMPONENT SCORES (0-1 each) ============
    
    # Magnitude (30% weight)
    magnitude_norm = event["magnitude_norm"]
    
    # Tone (20% weight) 
    tone_norm = event["tone_norm"]
    
    # Velocity (20% weight)
    # Compare current value to rolling average
    category = event["category"]
    rolling_avg = rolling_stats.get(f"{category}_avg", 0.5)
    rolling_std = rolling_stats.get(f"{category}_std", 0.2)
    
    if rolling_std > 0:
        z_score = (magnitude_norm - rolling_avg) / rolling_std
        velocity_norm = sigmoid(z_score, k=1.0)
    else:
        velocity_norm = 0.5
    
    # Attention (15% weight)
    # Based on number of sources / articles
    attention_norm = min(event.get("num_sources", 1) / 10, 1.0)
    
    # Persistence (15% weight)
    # Based on consecutive days with elevated signals (populated by aggregation layer)
    persistence_days = event.get("persistence_days", 1)
    persistence_norm = min(persistence_days / 7, 1.0)  # 7+ days = max
    
    # ============ BASE SCORE ============
    base_score = (
        0.30 * magnitude_norm +
        0.20 * tone_norm +
        0.20 * velocity_norm +
        0.15 * attention_norm +
        0.15 * persistence_norm
    ) * 100
    
    # ============ CONFIDENCE MODIFIER ============
    # Range: 0.5 to 1.0
    source_diversity = min(event.get("num_sources", 1) / 5, 1.0)
    source_credibility = event.get("source_credibility", 0.7)
    corroboration = event.get("corroboration_score", 0.5)  # from cross-source matching
    
    confidence_mod = 0.5 + 0.5 * (
        0.4 * source_diversity +
        0.3 * source_credibility +
        0.3 * corroboration
    )
    
    # ============ FINAL SCORE ============
    risk_score = base_score * confidence_mod
    
    # Severity floor: P1 events have minimum score of 70
    severity = event.get("severity", "P4")
    if severity == "P1":
        risk_score = max(risk_score, 70)
    elif severity == "P2":
        risk_score = max(risk_score, 50)
    
    return {
        "risk_score": round(risk_score, 1),
        "magnitude_contrib": round(magnitude_norm * 30, 1),
        "tone_contrib": round(tone_norm * 20, 1),
        "velocity_contrib": round(velocity_norm * 20, 1),
        "attention_contrib": round(attention_norm * 15, 1),
        "persistence_contrib": round(persistence_norm * 15, 1),
        "confidence_mod": round(confidence_mod, 3),
        "base_score": round(base_score, 1),
    }


def sigmoid(x: float, k: float = 1.0) -> float:
    """Sigmoid normalization. Maps any value to 0-1."""
    import math
    return 1 / (1 + math.exp(-k * x))
```

### 7.2 Category Sub-Scores

```python
def calculate_category_subscores(events: list[dict], date: str) -> dict:
    """
    Calculate sub-scores for each of the 10 categories.
    Aggregates all events for a given day.
    """
    
    CATEGORIES = [
        "POLITICAL", "CONFLICT", "ECONOMIC", "TRADE", "REGULATORY",
        "INFRASTRUCTURE", "HEALTHCARE", "SOCIAL", "ENVIRONMENTAL", "ENERGY"
    ]
    
    subscores = {}
    
    for category in CATEGORIES:
        category_events = [e for e in events if e["category"] == category]
        
        if not category_events:
            subscores[f"score_{category.lower()}"] = 0.0
            continue
        
        # Weighted average by severity
        severity_weights = {"P1": 4, "P2": 3, "P3": 2, "P4": 1}
        
        weighted_sum = sum(
            e["risk_score"] * severity_weights.get(e["severity"], 1)
            for e in category_events
        )
        weight_total = sum(
            severity_weights.get(e["severity"], 1)
            for e in category_events
        )
        
        avg_score = weighted_sum / weight_total if weight_total > 0 else 0
        
        # Event count boost (more events = higher concern)
        event_count_factor = min(len(category_events) / 10, 1.0)
        boosted_score = avg_score * (1 + 0.2 * event_count_factor)
        
        subscores[f"score_{category.lower()}"] = min(round(boosted_score, 1), 100)
    
    return subscores
```

### 7.3 Composite Daily Score

```python
def calculate_daily_composite(subscores: dict, events: list[dict]) -> float:
    """
    Calculate daily composite risk score from category sub-scores.
    
    Weights reflect commodity trader / investor priorities.
    """
    
    CATEGORY_WEIGHTS = {
        "score_political": 0.15,
        "score_conflict": 0.12,
        "score_economic": 0.15,
        "score_trade": 0.12,
        "score_regulatory": 0.12,
        "score_infrastructure": 0.08,
        "score_healthcare": 0.05,
        "score_social": 0.06,
        "score_environmental": 0.05,
        "score_energy": 0.10,
    }
    
    weighted_sum = sum(
        subscores.get(cat, 0) * weight
        for cat, weight in CATEGORY_WEIGHTS.items()
    )
    
    # Boost if any P1 events exist
    p1_count = sum(1 for e in events if e.get("severity") == "P1")
    if p1_count > 0:
        weighted_sum = max(weighted_sum, 70)
        weighted_sum *= (1 + 0.05 * min(p1_count, 5))  # up to 25% boost
    
    return min(round(weighted_sum, 1), 100)
```

---

## 8. Trend Calculation

```python
def calculate_trends(current_score: float, rolling_stats: dict) -> dict:
    """
    Calculate trend indicators.
    """
    
    # 7-day velocity
    avg_7d = rolling_stats.get("risk_score_7d_avg", current_score)
    std_7d = rolling_stats.get("risk_score_7d_std", 1)
    velocity_7d = (current_score - avg_7d) / std_7d if std_7d > 0 else 0
    
    # 30-day velocity
    avg_30d = rolling_stats.get("risk_score_30d_avg", current_score)
    std_30d = rolling_stats.get("risk_score_30d_std", 1)
    velocity_30d = (current_score - avg_30d) / std_30d if std_30d > 0 else 0
    
    # Trend direction
    if velocity_7d > 1:
        trend = "RISING_FAST"
    elif velocity_7d > 0.5:
        trend = "RISING"
    elif velocity_7d < -1:
        trend = "FALLING_FAST"
    elif velocity_7d < -0.5:
        trend = "FALLING"
    else:
        trend = "STABLE"
    
    return {
        "velocity_7d": round(velocity_7d, 2),
        "velocity_30d": round(velocity_30d, 2),
        "trend": trend,
        "risk_score_change_1d": round(current_score - rolling_stats.get("risk_score_1d_ago", current_score), 1),
        "risk_score_change_7d": round(current_score - avg_7d, 1),
        "risk_score_change_30d": round(current_score - avg_30d, 1),
    }
```

---

## 9. Alert Engine

### 9.1 Alert Triggers

```python
ALERT_CONFIG = {
    # Threshold breach
    "threshold_breach": {
        "enabled": True,
        "thresholds": [70, 80, 90],  # alert when crossed
        "cooldown_hours": 4,  # don't re-alert for same level
    },
    
    # Velocity spike
    "velocity_spike": {
        "enabled": True,
        "threshold": 15,  # points in 24 hours
        "cooldown_hours": 6,
    },
    
    # Category breakout
    "category_breakout": {
        "enabled": True,
        "threshold": 70,  # any sub-score crosses this
        "cooldown_hours": 4,
    },
    
    # Event type (P1 events)
    "event_type": {
        "enabled": True,
        "severities": ["P1"],
        "cooldown_hours": 1,
    },
    
    # Volume anomaly
    "volume_anomaly": {
        "enabled": True,
        "multiplier": 3.0,  # 3x above rolling average
        "window_days": 7,
        "cooldown_hours": 6,
    },
}


def check_alerts(
    current_state: dict,
    previous_state: dict,
    events: list[dict],
    rolling_stats: dict,
    alert_history: list[dict],
) -> list[dict]:
    """
    Check all alert conditions and return list of triggered alerts.
    """
    
    alerts = []
    now = datetime.utcnow()
    
    # ============ THRESHOLD BREACH ============
    if ALERT_CONFIG["threshold_breach"]["enabled"]:
        for threshold in ALERT_CONFIG["threshold_breach"]["thresholds"]:
            prev_score = previous_state.get("risk_score", 0)
            curr_score = current_state.get("risk_score", 0)
            
            # Crossed upward
            if prev_score < threshold <= curr_score:
                if not in_cooldown(alert_history, "threshold_breach", threshold):
                    alerts.append({
                        "type": "THRESHOLD_BREACH",
                        "severity": "P1" if threshold >= 90 else "P2" if threshold >= 80 else "P3",
                        "title": f"Risk score crossed {threshold}",
                        "message": f"Venezuela risk score is now {curr_score:.1f}, crossing the {threshold} threshold.",
                        "data": {"threshold": threshold, "score": curr_score},
                        "timestamp": now,
                    })
    
    # ============ VELOCITY SPIKE ============
    if ALERT_CONFIG["velocity_spike"]["enabled"]:
        threshold = ALERT_CONFIG["velocity_spike"]["threshold"]
        score_change = current_state.get("risk_score", 0) - previous_state.get("risk_score", 0)
        
        if score_change >= threshold:
            if not in_cooldown(alert_history, "velocity_spike", None):
                alerts.append({
                    "type": "VELOCITY_SPIKE",
                    "severity": "P2",
                    "title": f"Rapid risk increase: +{score_change:.1f} points",
                    "message": f"Venezuela risk score jumped {score_change:.1f} points in the last 24 hours.",
                    "data": {"change": score_change, "score": current_state.get("risk_score")},
                    "timestamp": now,
                })
    
    # ============ CATEGORY BREAKOUT ============
    if ALERT_CONFIG["category_breakout"]["enabled"]:
        threshold = ALERT_CONFIG["category_breakout"]["threshold"]
        
        for key, value in current_state.items():
            if key.startswith("score_") and value >= threshold:
                prev_value = previous_state.get(key, 0)
                if prev_value < threshold:
                    category = key.replace("score_", "").upper()
                    if not in_cooldown(alert_history, "category_breakout", category):
                        alerts.append({
                            "type": "CATEGORY_BREAKOUT",
                            "severity": "P2",
                            "title": f"{category} risk elevated",
                            "message": f"{category} sub-score crossed {threshold}, now at {value:.1f}.",
                            "data": {"category": category, "score": value},
                            "timestamp": now,
                        })
    
    # ============ EVENT TYPE (P1 events) ============
    if ALERT_CONFIG["event_type"]["enabled"]:
        p1_events = [e for e in events if e.get("severity") == "P1"]
        
        for event in p1_events:
            event_key = event.get("event_id")
            if not in_cooldown(alert_history, "event_type", event_key):
                alerts.append({
                    "type": "CRITICAL_EVENT",
                    "severity": "P1",
                    "title": f"Critical event: {event.get('event_type', 'Unknown')}",
                    "message": event.get("severity_reason", "Critical event detected in Venezuela."),
                    "data": {"event_id": event_key, "category": event.get("category")},
                    "timestamp": now,
                })
    
    # ============ VOLUME ANOMALY ============
    if ALERT_CONFIG["volume_anomaly"]["enabled"]:
        multiplier = ALERT_CONFIG["volume_anomaly"]["multiplier"]
        avg_volume = rolling_stats.get("event_count_7d_avg", 10)
        current_volume = len(events)
        
        if current_volume >= avg_volume * multiplier:
            if not in_cooldown(alert_history, "volume_anomaly", None):
                alerts.append({
                    "type": "VOLUME_ANOMALY",
                    "severity": "P3",
                    "title": f"Unusual event volume: {current_volume} events",
                    "message": f"Event volume is {current_volume / avg_volume:.1f}x above the 7-day average.",
                    "data": {"volume": current_volume, "average": avg_volume},
                    "timestamp": now,
                })
    
    return alerts
```

### 9.2 Alert Schema

```sql
CREATE TABLE alerts (
    alert_id        STRING,
    timestamp       TIMESTAMP,
    type            STRING,     -- THRESHOLD_BREACH | VELOCITY_SPIKE | CATEGORY_BREAKOUT | CRITICAL_EVENT | VOLUME_ANOMALY
    severity        STRING,     -- P1 | P2 | P3
    title           STRING,
    message         STRING,
    data            JSON,
    delivered_at    TIMESTAMP,
    delivery_channels ARRAY<STRING>,  -- ['api', 'email', 'sms', 'webhook']
);
```

---

## 10. Output Layer

### 10.1 API Endpoints

```
# Real-time
GET  /v1/risk/current           → Latest composite score + sub-scores + trend
GET  /v1/risk/events            → Recent events (paginated, filterable by severity/category)
GET  /v1/risk/events/{id}       → Single event detail
GET  /v1/alerts                 → Recent alerts (paginated)

# Historical
GET  /v1/risk/history           → Daily scores (date range, default 30 days)
GET  /v1/risk/history/{date}    → Single day detail

# Streaming
WS   /v1/stream/events          → Real-time event stream
WS   /v1/stream/alerts          → Real-time alert stream
```

### 10.2 API Response Examples

```json
// GET /v1/risk/current
{
  "timestamp": "2025-01-10T14:30:00Z",
  "risk_score": 67.3,
  "trend": "RISING",
  "velocity_7d": 1.2,
  "sub_scores": {
    "political": 72.1,
    "conflict": 58.4,
    "economic": 81.2,
    "trade": 54.3,
    "regulatory": 69.0,
    "infrastructure": 45.2,
    "healthcare": 38.1,
    "social": 62.8,
    "environmental": 22.0,
    "energy": 78.5
  },
  "event_summary": {
    "total_24h": 47,
    "p1": 1,
    "p2": 5,
    "p3": 18,
    "p4": 23
  }
}
```

```json
// GET /v1/risk/events?severity=P1,P2&limit=10
{
  "events": [
    {
      "event_id": "abc123",
      "timestamp": "2025-01-10T13:45:00Z",
      "source": "acled",
      "category": "CONFLICT",
      "event_type": "Violence against civilians",
      "severity": "P2",
      "severity_reason": "Fatalities: 3",
      "risk_score": 72.4,
      "location": {
        "country": "VE",
        "admin1": "Zulia",
        "coordinates": [-10.5, 71.6]
      },
      "actors": {
        "actor1": "Police Forces of Venezuela",
        "actor2": "Civilians"
      }
    }
  ],
  "pagination": {
    "total": 156,
    "page": 1,
    "per_page": 10,
    "next_cursor": "xyz789"
  }
}
```

### 10.3 Dashboard Views

| View | Content | Refresh |
|------|---------|---------|
| **Overview** | Composite score gauge, trend sparkline, sub-score heatmap | Real-time |
| **Events** | Filterable event table, map view, timeline | Real-time |
| **Categories** | 10 category cards with scores, trends, top events | Real-time |
| **Alerts** | Alert feed, acknowledgment status | Real-time |
| **Historical** | Time series charts, date range selector, export | On-demand |

### 10.4 Reports

| Report | Frequency | Content |
|--------|-----------|---------|
| **Daily Brief** | Daily 06:00 UTC | Summary, top events, score changes, alerts |
| **Weekly Analysis** | Weekly (Monday) | Trend analysis, category breakdown, notable events, outlook |

---

## 11. Data Flow Summary

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            INGESTION (15 min)                                │
│  GDELT, ACLED, Trends, SEC, FRED, etc. → raw_* tables                        │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          NORMALIZATION (15 min)                              │
│  raw_* → canonical_events (unified schema)                                   │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                       SEVERITY ASSIGNMENT (15 min)                           │
│  canonical_events → assign P1-P4                                             │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            SCORING (15 min)                                  │
│  canonical_events + rolling_stats → scored_events                            │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
             ┌───────────┐   ┌───────────┐   ┌───────────┐
             │ AGGREGATE │   │  ALERTS   │   │  TRENDS   │
             │  (daily)  │   │ (15 min)  │   │ (hourly)  │
             └───────────┘   └───────────┘   └───────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              OUTPUT                                          │
│  API (real-time) | Dashboard (real-time) | Alerts | Reports (daily/weekly)   │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Implementation Phases

| Phase | Scope | Duration |
|-------|-------|----------|
| **Phase 1** | GDELT + ACLED ingestion, canonical model, severity, basic scoring, API | 4-6 weeks |
| **Phase 2** | All data sources, full scoring, alerts, dashboard | 4-6 weeks |
| **Phase 3** | Reports, historical backfill, tuning, production hardening | 2-4 weeks |

---

## Appendix A: CAMEO Code Reference (Venezuela-Relevant)

| Code | Description | Category | Base Severity |
|------|-------------|----------|---------------|
| 14 | Protest | SOCIAL | P3 |
| 145 | Protest violently | CONFLICT | P2 |
| 172 | Impose sanctions | REGULATORY | P1 |
| 173 | Impose trade restrictions | TRADE | P2 |
| 181 | Abduct, hijack | CONFLICT | P2 |
| 182 | Physically assault | CONFLICT | P2 |
| 183 | Conduct strike or boycott | SOCIAL | P3 |
| 193 | Conduct bombing | CONFLICT | P1 |
| 195 | Assassinate | CONFLICT | P1 |

## Appendix B: Google Trends Search Terms

```python
VENEZUELA_SEARCH_TERMS = [
    "venezuela crisis",
    "venezuela sanctions",
    "venezuela oil",
    "pdvsa",
    "maduro",
    "venezuela inflation",
    "venezuela blackout",
    "venezuela protests",
    "venezuela gold",
    "venezuela default",
    "citgo",
    "venezuela military",
]
```
