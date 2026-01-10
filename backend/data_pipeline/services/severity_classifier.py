"""
P1-P4 Severity Classification System

Implements industry-standard severity classification from platform design (section 6):
- P1 (CRITICAL): Auto-triggers (coup, nationalization, 10+ fatalities, oil disruption)
- P2 (HIGH): 1-9 fatalities, major policy shift, >10% economic swing, regional violence
- P3 (MODERATE): Moderate impact (0.3-0.7 magnitude), protests without violence, minor regulatory
- P4 (LOW): Low impact (<0.3 magnitude), informational

Deterministic auto-trigger detection (not LLM-based) ensures reliable P1 classification.
"""

import re
from typing import Tuple
from api.bigquery_models import Event


class SeverityClassifier:
    """
    Classify events into P1-P4 severity levels with deterministic auto-triggers.
    """

    # P1 Auto-Trigger Definitions (from design doc section 6.1)
    P1_AUTO_TRIGGERS = {
        # Event type patterns (exact match)
        'event_types': [
            'COUP',
            'COUP_ATTEMPT',
            'NATIONALIZATION',
            'EXPROPRIATION',
            'SOVEREIGN_DEFAULT',
            'MILITARY_INTERVENTION',
            'HEAD_OF_STATE_REMOVED',
            'OIL_EXPORT_HALT',
        ],

        # CAMEO codes (GDELT-specific)
        'cameo_codes': [
            '192',   # Engage in ethnic cleansing
            '193',   # Conduct suicide, car, or other non-military bombing
            '194',   # Use weapons of mass destruction
            '195',   # Assassinate
            '1031',  # Coup d'état
        ],

        # Keyword patterns (regex, case-insensitive)
        'keywords': [
            r'coup\s+(attempt|d\'état)?',
            r'nationali[sz](e|ation)',
            r'expropriate?',
            r'sovereign\s+default',
            r'sanctions?\s+(announced|imposed)',
            r'oil\s+export\s+(halt|stop|ban)',
            r'pdvsa\s+(seize|shutdown|halt)',
        ],

        # Fatality threshold
        'fatality_threshold': 10,
    }

    @classmethod
    def assign_severity(cls, event: Event) -> Tuple[str, str]:
        """
        Assign P1-P4 severity to an event using deterministic rules.

        Args:
            event: Canonical Event instance with classification fields populated

        Returns:
            Tuple of (severity, reason) where:
            - severity is "P1" | "P2" | "P3" | "P4"
            - reason is human-readable explanation of classification

        Classification logic (from design doc section 6.2):
        - P1: Auto-triggers, 10+ fatalities, major oil disruption
        - P2: 1-9 fatalities, major policy shift, >10% economic swing, regional violence
        - P3: Moderate impact (0.3-0.7 norm), protests without violence, minor regulatory
        - P4: Everything else (low impact, informational)
        """

        # ============ P1: CRITICAL ============

        # Check event type auto-triggers
        if event.event_type and event.event_type.upper() in cls.P1_AUTO_TRIGGERS['event_types']:
            return ("P1", f"Auto-trigger: {event.event_type}")

        # Check CAMEO code auto-triggers (stored in metadata or subcategory for GDELT)
        cameo_code = None
        if event.source == 'gdelt':
            cameo_code = event.subcategory or event.metadata.get('event_code')

        if cameo_code and str(cameo_code) in cls.P1_AUTO_TRIGGERS['cameo_codes']:
            return ("P1", f"Auto-trigger: CAMEO {cameo_code}")

        # Check keyword patterns in title and content
        search_text = f"{event.title or ''} {event.content or ''}".lower()
        for pattern in cls.P1_AUTO_TRIGGERS['keywords']:
            if re.search(pattern, search_text, re.IGNORECASE):
                return ("P1", f"Auto-trigger: {pattern}")

        # Check fatality threshold (10+)
        if (event.magnitude_unit == 'fatalities' and
            event.magnitude_raw is not None and
            event.magnitude_raw >= cls.P1_AUTO_TRIGGERS['fatality_threshold']):
            return ("P1", f"High fatalities: {int(event.magnitude_raw)}")

        # Check major oil/energy disruption
        if (event.category == 'ENERGY' and
            event.commodities and 'OIL' in event.commodities and
            event.direction == 'NEGATIVE' and
            event.magnitude_norm is not None and
            event.magnitude_norm > 0.8):
            return ("P1", "Major oil/energy disruption")

        # ============ P2: HIGH ============

        # 1-9 fatalities
        if (event.magnitude_unit == 'fatalities' and
            event.magnitude_raw is not None and
            1 <= event.magnitude_raw < cls.P1_AUTO_TRIGGERS['fatality_threshold']):
            return ("P2", f"Fatalities: {int(event.magnitude_raw)}")

        # Major policy shift
        if (event.category in ['POLITICAL', 'REGULATORY'] and
            event.magnitude_norm is not None and
            event.magnitude_norm > 0.7 and
            event.direction == 'NEGATIVE'):
            return ("P2", "Significant policy/regulatory event")

        # Currency/economic shock (>10% change)
        if (event.category == 'ECONOMIC' and
            event.magnitude_unit == 'percent_change' and
            event.magnitude_raw is not None and
            abs(event.magnitude_raw) > 10):
            return ("P2", f"Major economic shift: {event.magnitude_raw:.1f}%")

        # Regional violence/protests
        if (event.category == 'CONFLICT' and
            event.magnitude_norm is not None and
            event.magnitude_norm > 0.5 and
            event.admin1 is not None):
            return ("P2", "Significant regional conflict event")

        # ============ P3: MODERATE ============

        # Moderate impact, contained
        if (event.direction == 'NEGATIVE' and
            event.magnitude_norm is not None and
            0.3 < event.magnitude_norm <= 0.7):
            return ("P3", "Moderate negative event")

        # Protests without violence
        if (event.event_type and
            event.event_type.upper() in ['PROTESTS', 'PROTEST'] and
            (event.magnitude_raw is None or event.magnitude_raw == 0)):
            return ("P3", "Protest activity (no casualties)")

        # Minor regulatory changes
        if (event.category == 'REGULATORY' and
            event.magnitude_norm is not None and
            event.magnitude_norm <= 0.5):
            return ("P3", "Minor regulatory event")

        # ============ P4: LOW ============
        # Everything else
        return ("P4", "Low impact / informational")
