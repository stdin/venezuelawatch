# Phase 25 Plan 02: P1-P4 Severity & Composite Scoring Summary

**Replaced SEV1-5 with industry-standard P1-P4 severity and implemented explainable 5-component risk scoring**

## Accomplishments

- Implemented P1-P4 severity classifier with deterministic auto-triggers (coup, nationalization, 10+ fatalities, oil disruption, sanctions keywords)
- Created composite risk scorer with 5 components: magnitude (30%), tone (20%), velocity (20%), attention (15%), persistence (15%)
- Added confidence modifier (0.5-1.0) based on source diversity (40%), source credibility (30%), and corroboration (30%)
- Implemented severity floor enforcement (P1 events minimum score 70, P2 minimum 50)
- Built category sub-scores calculation with severity weighting (P1=4x, P2=3x, P3=2x, P4=1x) and event count boost (up to 20% for 10+ events)
- Created daily composite scoring with **Venezuela-tuned weights** (ENERGY 18%, REGULATORY 15% vs generic 10%/12%)
- Added P1 event boost to daily composite (minimum 70, up to 25% increase for 5+ P1 events)

## Files Created/Modified

- `backend/data_pipeline/services/severity_classifier.py` - P1-P4 classifier with auto-triggers
- `backend/data_pipeline/services/composite_risk_scorer.py` - 5-component scoring engine
- `backend/data_pipeline/services/category_scoring.py` - Sub-scores and daily composite with Venezuela-tuned weights

## Decisions Made

- **Auto-triggers are deterministic (no LLM)** for P1 reliability — pattern matching on event types (COUP, NATIONALIZATION), CAMEO codes (192-195, 1031), regex keywords (coup attempt, sanctions imposed, oil export halt, pdvsa seize), fatality counts (10+), oil disruption (category=ENERGY, commodities=OIL, direction=NEGATIVE, magnitude_norm>0.8)

- **Venezuela-tuned weights** reflect oil dependence and sanctions risk (documented in CategoryScoring constants):
  - ENERGY: 18% (vs 10% generic) — oil is Venezuela's economic lifeline
  - REGULATORY: 15% (vs 12% generic) — sanctions are make-or-break for investors
  - CONFLICT: 11% (vs 12% generic) — normalized violence requires adjusted thresholds
  - TRADE: 10% (vs 12% generic), ENVIRONMENTAL: 2% (vs 5% generic) — reduced to balance
  - POLITICAL: 14%, ECONOMIC: 14% — slightly reduced from generic 15%
  - Weights sum to exactly 1.00

- **Velocity component uses rolling stats** (empty dict initially, defaults to z-score with mean=0.5, std=0.2) — full rolling window calculation deferred to Phase 26+ when we have historical data

- **Persistence component uses metadata.persistence_days** (initially 1) — Phase 21 spike tracking can populate this field for consecutive-day event sequences

- **Corroboration score uses metadata.corroboration_score** (default 0.5) — cross-source matching deferred to Phase 26+ for multi-source event correlation

- **Severity floor enforcement** ensures critical events have appropriate scores even if components are low (P1≥70 prevents false negatives)

- **P1 boost to composite** ensures any critical event elevates daily risk (minimum 70) and multiple P1 events compound concern (5% boost per P1, capped at 5 events = 25% total boost)

- **SEV1-5 strings deprecated** but not removed (ImpactClassifier can remain for backward compatibility if needed, but new code should use SeverityClassifier)

- **Explainability built-in**: CompositeRiskScorer returns component contributions (magnitude_contrib, tone_contrib, etc.) so analysts can understand why a score is high/low

## Issues Encountered

None

## Next Step

Phase 25 complete. Ready for Phase 26 (GKG theme population, entity relationship graphs, event lineage tracking) and Phase 27+ (rolling window stats, persistence spike detection, corroboration scoring from multi-source analysis).

---

## Technical Notes

**SeverityClassifier** (backend/data_pipeline/services/severity_classifier.py:23-165):
- P1 auto-triggers:
  - Event types: COUP, COUP_ATTEMPT, NATIONALIZATION, EXPROPRIATION, SOVEREIGN_DEFAULT, MILITARY_INTERVENTION, HEAD_OF_STATE_REMOVED, OIL_EXPORT_HALT
  - CAMEO codes: 192 (ethnic cleansing), 193 (bombing), 194 (WMD), 195 (assassinate), 1031 (coup d'état)
  - Keywords: coup, nationalize, expropriate, sovereign default, sanctions announced/imposed, oil export halt, pdvsa seize/shutdown
  - Fatality threshold: 10+
  - Oil disruption: ENERGY + OIL commodity + NEGATIVE + magnitude_norm > 0.8
- P2 triggers: 1-9 fatalities, major policy shift (POLITICAL/REGULATORY + magnitude_norm > 0.7 + NEGATIVE), economic shock (>10% change), regional violence (CONFLICT + magnitude_norm > 0.5 + admin1 present)
- P3 triggers: moderate impact (0.3-0.7 magnitude_norm), protests without violence, minor regulatory (magnitude_norm ≤ 0.5)
- P4: everything else (low impact, informational)

**CompositeRiskScorer** (backend/data_pipeline/services/composite_risk_scorer.py:22-160):
- Component weights: magnitude 30%, tone 20%, velocity 20%, attention 15%, persistence 15%
- Velocity calculation: z_score = (magnitude_norm - category_avg) / category_std, then sigmoid(z_score)
- Attention calculation: min(num_sources / 10, 1.0)
- Persistence calculation: min(persistence_days / 7, 1.0)
- Confidence modifier: 0.5 + 0.5 * (0.4 * source_diversity + 0.3 * source_credibility + 0.3 * corroboration)
- Final score: base_score * confidence_mod, then apply severity floors (P1≥70, P2≥50)
- Returns dict with risk_score + component contributions for explainability

**CategoryScoring** (backend/data_pipeline/services/category_scoring.py:24-165):
- Severity weights: P1=4, P2=3, P3=2, P4=1 (P1 events have 4x impact on category scores)
- Event count boost: up to 20% for 10+ events (boosted_score = weighted_avg * (1 + 0.2 * min(event_count/10, 1.0)))
- Venezuela-tuned weights (sum to 1.00):
  - score_energy: 0.18 (highest)
  - score_regulatory: 0.15 (2nd highest)
  - score_political: 0.14
  - score_economic: 0.14
  - score_conflict: 0.11
  - score_trade: 0.10
  - score_infrastructure: 0.07
  - score_social: 0.05
  - score_healthcare: 0.04
  - score_environmental: 0.02
- P1 boost: if p1_count > 0, composite = max(composite, 70) * (1 + 0.05 * min(p1_count, 5))

**Verification tests passed:**
- P1 auto-triggers (fatalities, oil disruption, coup keyword)
- P2/P3/P4 thresholds
- 5-component scoring with correct weights (30/20/20/15/15)
- Confidence modifier (0.5-1.0 range)
- Severity floors (P1≥70, P2≥50)
- Category sub-scores with severity weighting
- Venezuela-tuned weights sum to 1.0
- P1 boost to daily composite
