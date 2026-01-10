# Phase 23 Context: Intelligence Pipeline Rebuild

**Phase:** 23 - Intelligence Pipeline Rebuild
**Milestone:** v1.3 GDELT Intelligence
**Date:** 2026-01-10

## Vision

Redesign the intelligence pipeline to use a **hybrid scoring system** that combines GDELT's quantitative signals with LLM's qualitative analysis for more accurate risk assessment and severity classification.

### Core Approach

**Hybrid Scoring = Weighted Average of GDELT + LLM**

- **GDELT provides base quantitative score (0-100)**: Using tone, Goldstein scale, GKG themes, and theme intensity
- **LLM adds qualitative context and nuance**: Evaluates scope, duration, and impact for final assessment
- **Weighted combination**: Configurable weights (e.g., 70% LLM + 30% GDELT) to produce final score
- **LLM sees GDELT score**: LLM is provided with the computed GDELT score and can agree/disagree/refine its assessment

## Key Decisions

### 1. Scoring Methodology

**Primary Goal:** More accurate scoring by combining quantitative + qualitative approaches

**GDELT Quantitative Score (0-100):**
- **All four signals are weighted** (selected in priority order):
  1. **Goldstein scale** (-10 to +10): Event cooperation/conflict score
  2. **GKG themes**: Presence of CRISIS, PROTEST, CONFLICT themes
  3. **Theme intensity**: Count/frequency of high-risk themes
  4. **Tone (avg_tone)** (-100 to +100): GDELT's sentiment analysis

**Formula approach:** Standard methodology acceptable (user open to best practices)

### 2. Conflict Resolution

**When GDELT and LLM disagree:**
- Use **weighted average** approach
- Configurable weights (e.g., 70% LLM, 30% GDELT)
- No human review flagging or override logic needed

### 3. Severity Classification

**GDELT's role in SEV1-5 rating:**
- GDELT themes (CRISIS/PROTEST/CONFLICT) **indicate potential severity**
- LLM still evaluates scope/duration/impact for **final SEV1-5 classification**
- GDELT signals inform but don't determine severity

### 4. Score Computation Strategy

**Hybrid approach:**
- **Store base score at ingestion**: Calculate and save GDELT score when events first processed
- **Allow dynamic recalculation**: Enable admin/testing to recompute scores without full reprocessing
- Supports formula tweaking and experimentation

### 5. LLM Processing Strategy

**Process all events:**
- LLM analyzes **every event** regardless of GDELT score
- Most accurate approach (prioritize accuracy over cost optimization)
- No threshold filtering or tiered processing

### 6. Code Organization

**GDELT scoring logic location:**
- Implement **in intelligence pipeline** (not in GdeltAdapter)
- Calculate GDELT score during LLM analysis phase
- Not computed at ingestion time

### 7. Data Persistence

**Store only final combined score:**
- No separate storage of GDELT quantitative score
- No separate storage of LLM qualitative score
- No detailed scoring breakdown
- Only persist **final weighted average result**

### 8. LLM Context Awareness

**LLM prompt includes GDELT score:**
- Provide GDELT score to LLM during analysis
- LLM can see quantitative signals and computed score
- Enables LLM to agree/disagree/refine assessment based on data

### 9. Migration Strategy

**Replace immediately:**
- Switch all events to hybrid scoring
- Retire old LLM-only pipeline
- No parallel comparison period
- No gradual rollout or feature flags

### 10. Testing & Validation

**No pre-deployment validation needed:**
- Trust implementation and deploy
- No manual spot checks required
- No historical comparison with old scores
- No edge case testing before deployment

### 11. Output Format

**Update risk_score + severity:**
- Store final weighted score in existing `risk_score` field (0-100)
- Derive and update `severity` field (SEV1-5) from score ranges
- No new fields or detailed analysis objects

## Scope

### In Scope (Backend Only)
- GDELT quantitative scoring formula (tone + Goldstein + themes + theme intensity)
- Weighted combination logic for hybrid score
- Modified LLM prompt to include GDELT score
- Intelligence pipeline refactoring to compute GDELT score during analysis
- Update risk_score and severity fields with hybrid results
- Immediate replacement of old LLM-only pipeline

### Out of Scope
- Frontend changes
- Detailed score breakdowns or audit trails
- Comparison/validation with historical scores
- Gradual rollout or A/B testing infrastructure
- Threshold-based processing optimization
- Human review workflows for conflicting assessments

## Technical Constraints

1. **All events processed by LLM**: No filtering or sampling
2. **Scoring in intelligence pipeline**: Not in GdeltAdapter at ingestion
3. **Configurable weights**: Support adjusting GDELT/LLM weight ratio
4. **Dynamic recalculation**: Admin capability to recompute scores
5. **LLM context**: Include GDELT score in analysis prompt

## Success Criteria

- [ ] GDELT quantitative score formula implemented using all 4 signals
- [ ] Weighted average combination produces final 0-100 score
- [ ] LLM prompt includes GDELT score and signals
- [ ] risk_score and severity fields updated for all analyzed events
- [ ] Old LLM-only pipeline fully replaced
- [ ] Admin can dynamically recalculate scores with formula tweaks

## Open Questions

None - all key decisions captured above.

## Next Steps

1. Create detailed plan (23-PLAN.md) breaking down implementation into tasks
2. Consider whether to research GDELT scoring best practices first
3. Execute plan to implement hybrid intelligence pipeline
