# Phase 12: Chat Interface Polish - Context

**Gathered:** 2026-01-09
**Status:** Ready for planning

<vision>
## How This Should Work

The chat interface already works well with assistant-ui and tool calling from Phase 7. This phase is about visual polish—upgrading the tool cards that appear in conversation when Claude calls tools (search_events, get_entity_profile, get_trending_entities, analyze_risk_trends).

Tool cards should keep their current compact chat-optimized layout (not full-size like Dashboard components) but get enhanced with Mantine's professional typography, spacing, color tokens, and component styling. Think: same compact inline display, but with the visual polish and consistency of the Mantine design system.

The result should feel cohesive with the redesigned Dashboard and Entity pages—when you see a risk score badge or entity type badge in chat, it should look identical to the ones on Dashboard.

</vision>

<essential>
## What Must Be Nailed

- **Professional polish without losing compactness** - Upgrade to Mantine components (Card, Badge, Text, Group, Stack) but maintain the chat-optimized compact inline display. Tool cards need to work in conversation context, not dominate the screen like full dashboard components.

- **Adaptive density based on content** - Single entity/event cards can be very compact. Multiple results (trending entities list, search results) need more spacing for scannability. The design should adapt to the amount of information being displayed.

- **Same visual language as Dashboard** - Risk score badges (red ≥75, orange 50-74, blue <50), severity badges (SEV1-5 with color-coding), entity type badges (blue=Person, grape=Org, red=Gov, green=Location) should all use the exact same Mantine color scheme and styling established in Phase 10/11.

</essential>

<boundaries>
## What's Out of Scope

- **Message rendering improvements** - assistant-ui's ThreadPrimitive components for message rendering stay as-is. Focus is on tool cards only, not chat bubbles or message layout.

- **Chat page layout changes** - Keep the Perplexity-style center-focused layout (max-width: 44rem) from Phase 7. Don't redesign the page structure.

- **New chat features** - No conversation history, message editing, export, or other new functionality. Purely visual polish of existing tool cards.

- **Tool calling logic** - Backend tool implementations and LLM tool calling stay unchanged. Only frontend rendering of tool results.

</boundaries>

<specifics>
## Specific Ideas

- Use Mantine Card, Badge, Text, Group, Stack components instead of custom CSS
- Match Dashboard badge colors exactly: risk scores, severity levels, entity types
- Adaptive density: compact for single items, more spacing for lists
- Keep expand-in-place interaction pattern from Phase 7
- Preserve visual indicators: risk score colors, severity badges, entity type badges, trend arrows, sanctions pulse animation

</specifics>

<notes>
## Additional Context

Phase 7 established the foundation with assistant-ui, Claude streaming, and 4 tool types. The tool cards already have good information architecture—this phase is about upgrading them with Mantine components for visual consistency with the rest of the app.

The key tension is maintaining compactness (chat context) while adding professional polish (Mantine design system). The solution is adaptive density: let the content type determine the spacing, and use Mantine's size variants (sm, xs) where appropriate.

User emphasized that message rendering (ThreadPrimitive components) is out of scope—focus is purely on the tool result cards that appear when Claude calls backend tools.

</notes>

---

*Phase: 12-chat-interface-polish*
*Context gathered: 2026-01-09*
