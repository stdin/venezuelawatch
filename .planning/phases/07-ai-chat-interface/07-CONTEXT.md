# Phase 7: AI Chat Interface - Context

**Gathered:** 2026-01-08
**Status:** Ready for research

<vision>
## How This Should Work

Users land on a chat interface (/chat route) that feels like Perplexity - clean, research-oriented, with inline citations and rich previews. This is a chat-first experience where asking questions is the primary interaction, not a sidebar feature.

When users ask "Are there new sanctions affecting oil exports?" or "What's the supply chain risk level?", the AI responds with natural, conversational answers that include embedded preview cards showing the relevant events and entities. These cards display metadata (date, source, risk score), visual indicators (severity badges, trend arrows), and context about why this information matters.

The conversation flows naturally - the AI remembers context, asks clarifying questions when needed, and suggests related questions after answering. Users can click preview cards to expand them in-place for full details without leaving the chat. Everything stays within the conversational flow.

</vision>

<essential>
## What Must Be Nailed

- **Natural conversation quality** - The AI must feel like a knowledgeable colleague, not a search engine. It needs to:
  - Remember conversational context and handle follow-ups ("Tell me more about that")
  - Ask clarifying questions when queries are ambiguous
  - Use a conversational tone (not robotic)
  - Suggest related questions proactively after answering

- **Rich, informative previews** - When the AI cites events or entities, inline preview cards must show:
  - Key metadata (date, source, risk score)
  - Visual indicators (severity badges, entity type colors, trend arrows)
  - Contextual explanation ("This matters because...")

Better to have great conversations with limited data access than robotic responses with full data coverage.

</essential>

<boundaries>
## What's Out of Scope

- **Multi-user conversations** - No team collaboration, shared chats, or commenting features. Individual user conversations only.
- **Advanced report customization** - Reports are generated with standard format. No custom templates, branding options, or multiple export formats.
- **Voice/audio interface** - Text-only chat. No voice input, text-to-speech, or audio features.
- **Chat history/search** - Focus on current conversation. No persistent chat history, search across past conversations, or conversation management UI.

</boundaries>

<specifics>
## Specific Ideas

**Interface style:** Perplexity-like design
- Clean, research-oriented aesthetic
- Inline citations with visible data sourcing
- Rich previews embedded in chat responses
- Center-focused layout

**Navigation:** Separate route (/chat)
- Chat is a peer to /dashboard and /entities
- Users navigate between sections as distinct pages
- Tab or nav bar integration with existing app structure

**Interaction patterns:**
- Preview cards expand in-place (not navigate away)
- Suggested follow-up questions after each response
- Cards show all three information types: metadata, visual indicators, and contextual "why it matters"

**Query capabilities (all four types):**
1. Real-time intelligence: "What's happening in Venezuela right now?" "Show me today's high-risk events"
2. Entity research: "Tell me about PDVSA" "Who are the sanctioned individuals?"
3. Analytical deep-dives: "Why did the risk score spike?" "Explain this event's impact"
4. Report generation: "Generate a weekly briefing" (concise executive summaries for forwarding to stakeholders)

**Typical user journey:**
- Users arrive with a specific concern/question
- AI answers with conversational response + rich previews
- AI suggests related questions
- User continues conversational thread or explores suggestions

</specifics>

<notes>
## Additional Context

The assistant-ui library is mentioned in the roadmap for integration. The LLM provider choice is open (Claude/OpenAI mentioned as options).

Priority is conversation quality first, then comprehensive data access, then visual polish. Users should feel like they're talking to a smart analyst who understands context and helps them think through their concerns.

Reports should be concise executive summaries (2-3 paragraphs) that are perfect for forwarding to stakeholders - high-level takeaways, not detailed evidence trails.

</notes>

---

*Phase: 07-ai-chat-interface*
*Context gathered: 2026-01-08*
