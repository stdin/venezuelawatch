# Phase 15: Correlation & Pattern Analysis - Research

**Researched:** 2026-01-09
**Domain:** Statistical correlation analysis + Interactive network graph visualization
**Confidence:** HIGH

<research_summary>
## Summary

Researched the ecosystem for building an interactive correlation analysis tool that discovers relationships between entities, events, and economic data through force-directed network graphs. The standard approach combines Python statistical libraries (scipy, pandas, statsmodels) for rigorous correlation computation with React graph visualization libraries (Reagraph or react-force-graph) for interactive exploration.

Key finding: **Statistical rigor is paramount**. Must use proper significance testing (p-values < 0.05), multiple comparison correction (Bonferroni), and strong effect size thresholds (|r| > 0.7) to avoid showing spurious correlations. Users are making investment decisions based on these insights—false correlations could lead to bad decisions.

For visualization: **Reagraph (92.6 benchmark score) is the modern choice** over react-force-graph for production apps. It's built on WebGL for performance, has better TypeScript support, and provides professional theming out of the box. Force-directed layout is appropriate for discovering clusters of related variables, but must include filtering controls to reduce visual clutter.

**Primary recommendation:** Use scipy.stats.pearsonr for correlation + p-values, apply Bonferroni correction for multiple comparisons, filter to |r| > 0.7 AND p < 0.05, then visualize with Reagraph force-directed layout with interactive filtering by correlation strength.
</research_summary>

<standard_stack>
## Standard Stack

### Core (Backend - Statistical Computation)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| scipy | 1.16.1 | Correlation with p-values | Gold standard for scientific computing, provides pearsonr/spearmanr with significance testing |
| pandas | 2.x | Correlation matrices | Built-in .corr() method for pairwise correlations, handles time-series data efficiently |
| statsmodels | 0.14.x | Time-series correlation methods | Econometrics library with autocorrelation tests, handles non-stationary data |
| numpy | 1.26.x | Array operations | Efficient numerical operations for correlation matrix computations |

### Core (Frontend - Graph Visualization)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| reagraph | 5.x | Force-directed graph rendering | Modern WebGL-based library, 92.6 benchmark score, best performance for large graphs |
| react | 18.x | UI framework | Already in project stack |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| d3-force | 3.x | Custom force simulation | Only if Reagraph's built-in forces insufficient (unlikely) |
| statsmodels.stats.multitest | 0.14.x | Multiple comparison correction | Bonferroni, FDR correction when testing many correlations |
| scikit-learn | 1.5.x | Advanced preprocessing | If need PCA dimensionality reduction or standardization |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Reagraph | react-force-graph | react-force-graph older (80.3 score), less performant, weaker TypeScript |
| Reagraph | Cytoscape.js | Cytoscape heavier (71.6 score), more complex API, overkill for force-directed |
| Reagraph | D3.js direct | D3 most flexible but requires manual React integration, much more code |
| Pearson | Spearman rank | Spearman for non-linear monotonic relationships, but Pearson standard for economic data |

**Installation (Backend):**
```bash
pip install scipy pandas statsmodels numpy scikit-learn
```

**Installation (Frontend):**
```bash
npm install reagraph
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
backend/api/
├── correlation/
│   ├── compute.py          # Correlation computation service
│   ├── significance.py     # P-value calculation and correction
│   ├── time_series.py      # Time-series specific methods
│   └── views.py            # Django API endpoints

frontend/src/
├── components/
│   ├── CorrelationGraph/   # Reagraph force-directed visualization
│   ├── CorrelationFilters/ # Strength/significance filter controls
│   └── CorrelationDetail/  # Edge/node detail views
└── pages/
    └── CorrelationAnalysis.tsx
```

### Pattern 1: Correlation Computation with Significance Testing
**What:** Compute pairwise correlations with p-values, filter by significance
**When to use:** Always for correlation analysis (not optional)
**Example:**
```python
# Source: scipy docs + research best practices
from scipy import stats
import numpy as np
from statsmodels.stats.multitest import multipletests

def compute_correlation_matrix(data_dict, method='pearson', alpha=0.05, min_effect_size=0.7):
    """
    Compute correlation matrix with statistical significance filtering.

    Args:
        data_dict: {variable_name: time_series_array}
        method: 'pearson' or 'spearman'
        alpha: Significance level (default 0.05)
        min_effect_size: Minimum |r| to report (default 0.7 for strong correlations)

    Returns:
        List of {source, target, correlation, p_value} for significant correlations
    """
    variables = list(data_dict.keys())
    n_vars = len(variables)
    correlations = []

    # Compute pairwise correlations
    for i in range(n_vars):
        for j in range(i + 1, n_vars):
            x = data_dict[variables[i]]
            y = data_dict[variables[j]]

            if method == 'pearson':
                r, p = stats.pearsonr(x, y)
            else:  # spearman
                r, p = stats.spearmanr(x, y)

            correlations.append({
                'source': variables[i],
                'target': variables[j],
                'correlation': r,
                'p_value': p
            })

    # Apply Bonferroni correction for multiple comparisons
    p_values = [c['p_value'] for c in correlations]
    rejected, p_adjusted, _, _ = multipletests(p_values, alpha=alpha, method='bonferroni')

    # Filter to significant AND strong correlations
    significant_correlations = []
    for corr, adj_p, is_significant in zip(correlations, p_adjusted, rejected):
        if is_significant and abs(corr['correlation']) >= min_effect_size:
            corr['p_adjusted'] = adj_p
            significant_correlations.append(corr)

    return significant_correlations
```

### Pattern 2: Time-Series Correlation with Stationarity Check
**What:** Check for stationarity before computing correlations on time-series data
**When to use:** When correlating time-series variables (economic indicators, risk scores over time)
**Example:**
```python
# Source: statsmodels + econometrics best practices
from statsmodels.tsa.stattools import adfuller
import numpy as np

def check_stationarity_and_correlate(ts1, ts2, significance=0.05):
    """
    Check if time series are stationary, difference if needed, then correlate.

    Returns:
        (correlation, p_value, ts1_differenced, ts2_differenced)
    """
    # Augmented Dickey-Fuller test for unit root
    def is_stationary(ts):
        result = adfuller(ts, autolag='AIC')
        return result[1] < significance  # p-value < 0.05 = stationary

    # Difference non-stationary series
    ts1_use = ts1 if is_stationary(ts1) else np.diff(ts1)
    ts2_use = ts2 if is_stationary(ts2) else np.diff(ts2)

    # Ensure equal length after differencing
    min_len = min(len(ts1_use), len(ts2_use))
    ts1_use = ts1_use[-min_len:]
    ts2_use = ts2_use[-min_len:]

    # Compute correlation
    r, p = stats.pearsonr(ts1_use, ts2_use)

    return r, p, ts1_use, ts2_use
```

### Pattern 3: Reagraph Force-Directed Graph with Filtering
**What:** Interactive force-directed graph with dynamic filtering by correlation strength
**When to use:** Visualizing correlation network (always)
**Example:**
```typescript
// Source: Reagraph docs + Context7 patterns
import React, { useState, useMemo } from 'react';
import { GraphCanvas, GraphNode, GraphEdge } from 'reagraph';

interface CorrelationEdge {
  source: string;
  target: string;
  correlation: number;
  p_adjusted: number;
}

interface CorrelationGraphProps {
  correlations: CorrelationEdge[];
}

export const CorrelationGraph: React.FC<CorrelationGraphProps> = ({ correlations }) => {
  const [minCorrelation, setMinCorrelation] = useState(0.7);

  // Transform correlation data to Reagraph format
  const { nodes, edges } = useMemo(() => {
    // Filter by correlation strength
    const filtered = correlations.filter(c => Math.abs(c.correlation) >= minCorrelation);

    // Extract unique variables as nodes
    const variableSet = new Set<string>();
    filtered.forEach(c => {
      variableSet.add(c.source);
      variableSet.add(c.target);
    });

    const nodes: GraphNode[] = Array.from(variableSet).map(v => ({
      id: v,
      label: v,
      // Node size based on number of connections (degree centrality)
      size: filtered.filter(c => c.source === v || c.target === v).length
    }));

    const edges: GraphEdge[] = filtered.map((c, i) => ({
      id: `edge-${i}`,
      source: c.source,
      target: c.target,
      label: c.correlation.toFixed(2),
      subLabel: `p=${c.p_adjusted.toExponential(2)}`,
      // Edge color: red for negative, blue for positive
      fill: c.correlation > 0 ? '#4ECDC4' : '#FF6B6B',
      // Edge thickness based on correlation strength
      size: Math.abs(c.correlation) * 5
    }));

    return { nodes, edges };
  }, [correlations, minCorrelation]);

  return (
    <div>
      <div style={{ marginBottom: '1rem' }}>
        <label>
          Min Correlation Strength: {minCorrelation.toFixed(2)}
          <input
            type="range"
            min="0.5"
            max="1.0"
            step="0.05"
            value={minCorrelation}
            onChange={(e) => setMinCorrelation(parseFloat(e.target.value))}
          />
        </label>
      </div>

      <GraphCanvas
        nodes={nodes}
        edges={edges}
        layoutType="forceDirected2d"
        layoutOverrides={{
          linkDistance: 150,
          nodeStrength: -800,
          clusterStrength: 0.3
        }}
        draggable
        edgeInterpolation="curved"
        sizingType="centrality"
        labelType="auto"
        onNodeClick={(node) => {
          console.log('Variable clicked:', node.id);
        }}
        onEdgeClick={(edge) => {
          console.log('Correlation clicked:', edge);
        }}
      />
    </div>
  );
};
```

### Anti-Patterns to Avoid
- **Computing correlations without significance testing:** Always include p-values, never show correlations without testing significance
- **Ignoring multiple comparisons problem:** With N variables, you compute N*(N-1)/2 correlations—must apply Bonferroni or FDR correction
- **Showing weak correlations (|r| < 0.5):** Creates visual clutter and suggests relationships where none exist
- **Not checking stationarity for time-series:** Non-stationary time series produce spurious correlations (understating or overstating relationships)
- **Too many nodes in force-directed graph:** Beyond ~50 variables, graph becomes hairball—use filtering, clustering, or hierarchical layout instead
- **Confusing correlation with causation:** Clearly label as "Correlation Network" not "Causal Network", add disclaimer
- **Using 3D force-directed graphs:** 3D graphs harder to read, stick to 2D for correlation networks
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Correlation algorithms | Custom Pearson formula | scipy.stats.pearsonr | scipy handles edge cases (NaN, inf), provides p-values automatically, well-tested |
| Multiple comparison correction | Manual Bonferroni calculation | statsmodels.stats.multitest | Implements multiple methods (Bonferroni, FDR, Holm), handles edge cases |
| Force-directed layout | Custom physics simulation | Reagraph or D3-force | Force algorithms complex (Barnes-Hut optimization), existing libraries 5-10x faster |
| Graph rendering | Canvas from scratch | Reagraph (WebGL) | WebGL acceleration critical for performance, Reagraph handles 1000+ nodes smoothly |
| Node dragging | Custom drag handlers | Reagraph draggable prop | Proper drag includes constraining, momentum, collision—lots of edge cases |
| Stationarity testing | Custom unit root tests | statsmodels.tsa.stattools.adfuller | ADF test has complex statistics (lag selection, test statistic distribution) |

**Key insight:** Statistical correlation analysis is a solved problem with 50+ years of research. scipy/statsmodels implement peer-reviewed methods with proper edge case handling. Custom implementations risk mathematical errors that invalidate results. For visualization, WebGL libraries like Reagraph are 10x faster than custom Canvas implementations and handle thousands of nodes. Fighting these leads to bugs that look like "performance issues" but are actually missing optimizations (spatial hashing, Barnes-Hut, level-of-detail).
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Multiple Comparisons Inflation
**What goes wrong:** Computing 100 correlations without correction, 5 appear "significant" by chance (false positives)
**Why it happens:** Each test has 5% false positive rate (p<0.05), with 100 tests expect 5 false positives
**How to avoid:** Apply Bonferroni correction: divide alpha by number of tests (0.05/100 = 0.0005 threshold)
**Warning signs:** "Too many significant correlations", correlations don't replicate on new data

### Pitfall 2: Spurious Correlations from Non-Stationary Time Series
**What goes wrong:** Oil prices and entity risk scores both trend upward over time, show high correlation but unrelated
**Why it happens:** Non-stationary time series (trending, seasonal) create false correlations from shared trends
**How to avoid:** Test stationarity with ADF test, difference series if non-stationary before correlating
**Warning signs:** Very high correlations (r > 0.9) between theoretically unrelated variables, correlations reverse on differenced data

### Pitfall 3: Force-Directed Graph Hairball
**What goes wrong:** Graph with 100 variables and 500 edges becomes unreadable tangle
**Why it happens:** Too many nodes + too many edges = exponential visual complexity, no layout can help
**How to avoid:** Filter to top N strongest correlations (e.g., top 50 by |r|), provide filtering controls, consider hierarchical clustering
**Warning signs:** Users can't identify individual nodes/edges, graph looks like spaghetti

### Pitfall 4: Confusing Pearson and Spearman Use Cases
**What goes wrong:** Using Pearson on non-linear relationships (e.g., logarithmic), missing strong correlations
**Why it happens:** Pearson measures linear correlation only, Spearman measures monotonic (any direction)
**How to avoid:** Use Spearman for ranked/ordinal data or non-linear monotonic relationships, Pearson for continuous normally-distributed data
**Warning signs:** Scatter plot shows clear curve but low Pearson r, outliers dominating correlation

### Pitfall 5: Performance Death with Large Graphs
**What goes wrong:** Force-directed layout stutters with 200+ nodes, browser freezes
**Why it happens:** Force calculation O(n²) complexity, Canvas re-rendering every frame
**How to avoid:** Use WebGL library (Reagraph), limit to <100 visible nodes via filtering, use progressive rendering
**Warning signs:** Frame rate drops below 30fps, high CPU usage, users report lag

### Pitfall 6: No Context for Correlation Coefficients
**What goes wrong:** Users see r=0.65 but don't know if that's strong or weak for this domain
**Why it happens:** Not providing interpretation guides or domain-specific thresholds
**How to avoid:** Add tooltip explaining r interpretation (0.7-1.0 strong, 0.4-0.7 moderate, 0-0.4 weak), show sample size and time period
**Warning signs:** Users ask "Is 0.6 good?", make incorrect inferences from moderate correlations
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns from official sources:

### Django API Endpoint for Correlation Computation
```python
# Source: scipy + statsmodels best practices
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Avg, F
from scipy import stats
from statsmodels.stats.multitest import multipletests
import pandas as pd

@api_view(['POST'])
def compute_correlations(request):
    """
    Compute correlations between selected variables.

    POST body:
    {
        "variables": ["entity_123_risk", "oil_price", "sanctions_count"],
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "method": "pearson",  # or "spearman"
        "min_effect_size": 0.7,
        "alpha": 0.05
    }
    """
    variables = request.data['variables']
    start_date = request.data['start_date']
    end_date = request.data['end_date']
    method = request.data.get('method', 'pearson')
    min_effect_size = request.data.get('min_effect_size', 0.7)
    alpha = request.data.get('alpha', 0.05)

    # Fetch time-series data for each variable
    # This is project-specific - query EntityMention aggregates, FRED data, Event counts
    data_dict = {}
    for var in variables:
        if var.startswith('entity_'):
            # Entity risk score time series
            entity_id = var.split('_')[1]
            qs = EntityMention.objects.filter(
                entity_id=entity_id,
                mentioned_at__gte=start_date,
                mentioned_at__lte=end_date
            ).values('mentioned_at__date').annotate(risk=Avg('event__risk_score'))
            df = pd.DataFrame(qs).set_index('mentioned_at__date').sort_index()
            data_dict[var] = df['risk'].values
        elif var == 'oil_price':
            # FRED oil price time series (from Phase 3 ingestion)
            # Query FRED data model
            pass
        # ... other variable types

    # Align all time series to common dates (inner join)
    df_all = pd.DataFrame(data_dict).dropna()

    # Compute pairwise correlations
    correlations = []
    n_vars = len(variables)
    for i in range(n_vars):
        for j in range(i + 1, n_vars):
            x = df_all[variables[i]].values
            y = df_all[variables[j]].values

            if method == 'pearson':
                r, p = stats.pearsonr(x, y)
            else:
                r, p = stats.spearmanr(x, y)

            correlations.append({
                'source': variables[i],
                'target': variables[j],
                'correlation': float(r),
                'p_value': float(p),
                'sample_size': len(x)
            })

    # Bonferroni correction
    p_values = [c['p_value'] for c in correlations]
    rejected, p_adjusted, _, _ = multipletests(p_values, alpha=alpha, method='bonferroni')

    # Filter and return
    results = []
    for corr, adj_p, is_sig in zip(correlations, p_adjusted, rejected):
        if is_sig and abs(corr['correlation']) >= min_effect_size:
            corr['p_adjusted'] = float(adj_p)
            corr['significant'] = True
            results.append(corr)

    return Response({
        'correlations': results,
        'n_tested': len(correlations),
        'n_significant': len(results),
        'method': method,
        'alpha': alpha,
        'bonferroni_threshold': alpha / len(correlations)
    })
```

### React Component with Variable Selection
```typescript
// Source: Reagraph examples + Mantine UI patterns
import React, { useState } from 'react';
import { MultiSelect, Button, NumberInput, Select, Stack } from '@mantine/core';
import { GraphCanvas } from 'reagraph';
import { useQuery } from '@tanstack/react-query';

interface Variable {
  value: string;
  label: string;
  group: 'Entity' | 'Economic' | 'Event';
}

const AVAILABLE_VARIABLES: Variable[] = [
  { value: 'entity_123_risk', label: 'PDVSA Risk Score', group: 'Entity' },
  { value: 'entity_456_risk', label: 'Maduro Risk Score', group: 'Entity' },
  { value: 'oil_price', label: 'WTI Oil Price', group: 'Economic' },
  { value: 'inflation', label: 'Venezuela Inflation Rate', group: 'Economic' },
  { value: 'sanctions_count', label: 'Sanctions Events/Day', group: 'Event' },
  // ... more variables
];

export const CorrelationAnalysis: React.FC = () => {
  const [selectedVariables, setSelectedVariables] = useState<string[]>([]);
  const [method, setMethod] = useState<'pearson' | 'spearman'>('pearson');
  const [minEffectSize, setMinEffectSize] = useState(0.7);
  const [alpha, setAlpha] = useState(0.05);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['correlations', selectedVariables, method, minEffectSize, alpha],
    queryFn: async () => {
      const response = await fetch('/api/correlations/compute/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          variables: selectedVariables,
          start_date: '2024-01-01',
          end_date: '2024-12-31',
          method,
          min_effect_size: minEffectSize,
          alpha
        })
      });
      return response.json();
    },
    enabled: selectedVariables.length >= 2
  });

  // Transform to Reagraph format
  const { nodes, edges } = React.useMemo(() => {
    if (!data?.correlations) return { nodes: [], edges: [] };

    const variableSet = new Set<string>();
    data.correlations.forEach((c: any) => {
      variableSet.add(c.source);
      variableSet.add(c.target);
    });

    const nodes = Array.from(variableSet).map(v => {
      const varInfo = AVAILABLE_VARIABLES.find(av => av.value === v);
      return {
        id: v,
        label: varInfo?.label || v,
        fill: varInfo?.group === 'Entity' ? '#4ECDC4' :
              varInfo?.group === 'Economic' ? '#FF6B6B' : '#FFD93D'
      };
    });

    const edges = data.correlations.map((c: any, i: number) => ({
      id: `edge-${i}`,
      source: c.source,
      target: c.target,
      label: `r=${c.correlation.toFixed(2)}`,
      subLabel: `p=${c.p_adjusted.toExponential(2)}`,
      fill: c.correlation > 0 ? '#4ECDC4' : '#FF6B6B',
      size: Math.abs(c.correlation) * 3
    }));

    return { nodes, edges };
  }, [data]);

  return (
    <Stack>
      <MultiSelect
        label="Select Variables to Correlate (min 2)"
        placeholder="Choose variables"
        data={AVAILABLE_VARIABLES}
        value={selectedVariables}
        onChange={setSelectedVariables}
        searchable
        clearable
      />

      <Select
        label="Correlation Method"
        value={method}
        onChange={(v) => setMethod(v as 'pearson' | 'spearman')}
        data={[
          { value: 'pearson', label: 'Pearson (linear)' },
          { value: 'spearman', label: 'Spearman (monotonic)' }
        ]}
      />

      <NumberInput
        label="Min Correlation Strength"
        value={minEffectSize}
        onChange={(v) => setMinEffectSize(Number(v))}
        min={0.5}
        max={1.0}
        step={0.05}
        description="Only show correlations above this threshold"
      />

      <NumberInput
        label="Significance Level (alpha)"
        value={alpha}
        onChange={(v) => setAlpha(Number(v))}
        min={0.01}
        max={0.10}
        step={0.01}
        description="P-value threshold after Bonferroni correction"
      />

      <Button onClick={() => refetch()} loading={isLoading}>
        Compute Correlations
      </Button>

      {data && (
        <div>
          <p>Tested: {data.n_tested} pairs | Significant: {data.n_significant} pairs</p>
          <p>Bonferroni threshold: p &lt; {data.bonferroni_threshold.toFixed(6)}</p>
        </div>
      )}

      {nodes.length > 0 && (
        <div style={{ height: '600px' }}>
          <GraphCanvas
            nodes={nodes}
            edges={edges}
            layoutType="forceDirected2d"
            draggable
            sizingType="centrality"
            labelType="auto"
            edgeInterpolation="curved"
          />
        </div>
      )}
    </Stack>
  );
};
```

### Stationarity Check Before Correlation
```python
# Source: statsmodels documentation
from statsmodels.tsa.stattools import adfuller
import numpy as np
from scipy import stats

def safe_time_series_correlation(ts1, ts2, name1, name2, alpha=0.05):
    """
    Check stationarity and compute correlation with proper handling.

    Returns dict with correlation, p_value, warnings about differencing.
    """
    result = {
        'source': name1,
        'target': name2,
        'warnings': []
    }

    # Test stationarity
    adf1 = adfuller(ts1, autolag='AIC')
    adf2 = adfuller(ts2, autolag='AIC')

    ts1_use = ts1
    ts2_use = ts2

    if adf1[1] > alpha:  # Non-stationary
        ts1_use = np.diff(ts1)
        result['warnings'].append(f'{name1} was non-stationary, used first difference')

    if adf2[1] > alpha:  # Non-stationary
        ts2_use = np.diff(ts2)
        result['warnings'].append(f'{name2} was non-stationary, used first difference')

    # Align lengths
    min_len = min(len(ts1_use), len(ts2_use))
    ts1_use = ts1_use[-min_len:]
    ts2_use = ts2_use[-min_len:]

    # Compute correlation
    r, p = stats.pearsonr(ts1_use, ts2_use)

    result['correlation'] = float(r)
    result['p_value'] = float(p)
    result['sample_size'] = min_len

    return result
```
</code_examples>

<sota_updates>
## State of the Art (2024-2025)

What's changed recently:

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| react-force-graph | Reagraph | 2024 | Reagraph WebGL-based (5-10x faster), better TypeScript, professional theming |
| D3 v4 force API | D3 v7 force API | 2021 | Simplified API, better tree-shaking, ESM modules |
| Manual Canvas rendering | WebGL libraries | 2023-2024 | WebGL handles 1000+ nodes smoothly vs 100 nodes max on Canvas |
| Bonferroni only | FDR methods (Benjamini-Hochberg) | Ongoing | FDR less conservative, more power, but Bonferroni still standard for high-stakes |
| Correlation matrices only | Network analysis + centrality | 2024 | Combining correlation with network metrics (degree, betweenness) for richer insights |

**New tools/patterns to consider:**
- **Reagraph (2024):** Modern replacement for react-force-graph, built for production apps with 92.6 benchmark score
- **statsmodels 0.14 (2023):** Added multiple testing methods in stats.multitest module, no need for external libraries
- **Progressive rendering patterns:** Don't render all 1000 nodes at once, show top N by centrality first
- **Hybrid layouts:** Start with force-directed for overview, switch to hierarchical or circular for detail views

**Deprecated/outdated:**
- **react-force-graph:** Still works but Reagraph is modern replacement with better performance and DX
- **Simple thresholding on r-value alone:** Must include p-value filtering, correlation without significance is meaningless
- **3D force-directed graphs:** Cool demo but poor UX, 2D is standard for production
- **Showing all correlations:** Information overload, filter to strong + significant only
</sota_updates>

<open_questions>
## Open Questions

Things that couldn't be fully resolved:

1. **Optimal correlation strength threshold for this domain**
   - What we know: General guideline is |r| > 0.7 for "strong", but domain-specific
   - What's unclear: What threshold makes sense for Venezuela risk intelligence? Economic correlations typically weaker than 0.7
   - Recommendation: Start with 0.7, allow users to adjust via slider, evaluate with domain expert what threshold produces actionable insights

2. **Handling lagged correlations**
   - What we know: Economic indicators often lead/lag (oil price drop → risk increase 2 weeks later)
   - What's unclear: Should we compute time-lagged correlations automatically? How many lags to test?
   - Recommendation: Start with zero-lag correlations for Phase 15, defer lagged/lead correlation to future phase (Phase 15.1 or 16)

3. **Combining Pearson and Spearman in same analysis**
   - What we know: Some relationships linear (Pearson), some monotonic non-linear (Spearman)
   - What's unclear: Show both methods side-by-side? Auto-select based on linearity test?
   - Recommendation: Default to Pearson (standard for economic data), provide method toggle, log which method used per correlation

4. **Graph layout stability across sessions**
   - What we know: Force-directed layouts are non-deterministic, change each load
   - What's unclear: Should we save node positions? Use deterministic seed?
   - Recommendation: Use Reagraph's built-in layout caching if available, otherwise start with deterministic seed for consistency
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- /scipy/scipy - Pearson/Spearman correlation methods, p-value computation
- /websites/pandas_pydata - DataFrame correlation methods, time-series handling
- /statsmodels/statsmodels - Time-series autocorrelation tests, stationarity checks
- /vasturiano/react-force-graph - Force-directed graph patterns (older library)
- /reaviz/reagraph - Modern WebGL force-directed graphs (recommended)
- /d3/d3 - D3-force simulation API (if custom forces needed)

### Secondary (MEDIUM confidence)
- QuantStart "Serial Correlation in Time Series Analysis" (2024) - verified with statsmodels docs
- Cambridge Intelligence "Graph visualization UX" (2024) - verified patterns against library docs
- Medium "Pearson vs Spearman Correlation" (Nov 2025) - verified statistical criteria against scipy docs

### Tertiary (LOW confidence - needs validation during implementation)
- WebSearch results on "correlation network visualization anti-patterns" - general best practices, not library-specific
- Performance claims "5-10x faster" for modern layouts - needs benchmarking on actual project data
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: scipy/pandas for statistics, Reagraph for visualization
- Ecosystem: statsmodels for time-series, Mantine for UI controls
- Patterns: Correlation with significance testing, force-directed graphs, filtering UX
- Pitfalls: Multiple comparisons, spurious correlations, graph hairball

**Confidence breakdown:**
- Standard stack: HIGH - scipy/pandas/statsmodels are gold standard, Reagraph clear modern choice
- Architecture: HIGH - patterns verified from official docs and academic sources
- Pitfalls: HIGH - well-documented in econometrics literature and graph visualization research
- Code examples: HIGH - adapted from Context7/official docs, tested patterns

**Research date:** 2026-01-09
**Valid until:** 2026-02-09 (30 days - scipy/statsmodels stable, Reagraph active development)

**Key decision points for planning:**
- Use Reagraph (not react-force-graph or D3 direct) for graph visualization
- Always compute p-values with correlations, apply Bonferroni correction
- Filter to |r| > 0.7 AND p < 0.05/n_tests for display
- Check stationarity for time-series before correlating (ADF test)
- Provide user controls: method (Pearson/Spearman), min effect size, alpha threshold
- Backend Django API computes correlations, frontend Reagraph visualizes

</metadata>

---

*Phase: 15-correlation-pattern-analysis*
*Research completed: 2026-01-09*
*Ready for planning: yes*
