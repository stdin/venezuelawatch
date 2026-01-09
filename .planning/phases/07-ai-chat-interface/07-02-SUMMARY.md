---
phase: 07-ai-chat-interface
plan: 02
subsystem: ui

tags: [assistant-ui, react, sse, streaming, chat, django-integration]

# Dependency graph
requires:
  - phase: 07-ai-chat-interface
    provides: Backend chat API with SSE streaming, tool calling framework
provides:
  - assistant-ui React integration with custom Django runtime
  - useChatRuntime hook with SSE streaming support
  - ChatProvider component for conversation context
  - TypeScript types for chat messages and tool execution

affects: [07-03-chat-ui-components, frontend-chat-pages]

# Tech tracking
tech-stack:
  added: [@assistant-ui/react, @assistant-ui/react-markdown, remark-gfm]
  patterns: [useExternalStoreRuntime for custom backends, SSE streaming with fetch ReadableStream, conversation state management]

key-files:
  created:
    - frontend/src/lib/chatRuntime.ts
    - frontend/src/components/ChatProvider.tsx
  modified:
    - frontend/package.json
    - frontend/src/lib/types.ts

key-decisions:
  - "useExternalStoreRuntime pattern for custom Django backend (not Vercel AI SDK)"
  - "fetch() with ReadableStream for SSE parsing (not EventSource API)"
  - "Accumulate text chunks in single assistant message (not separate messages)"
  - "ChatMessage type matches Django backend format (role + content)"

patterns-established:
  - "Custom runtime pattern: useState for messages, useCallback for handlers, useExternalStoreRuntime for assistant-ui compatibility"
  - "SSE parsing: buffer incomplete chunks, split on \\n\\n, parse data: {json} format"
  - "Error handling: network errors and parse errors show in chat as assistant messages"
  - "Provider pattern: ChatProvider wraps AssistantRuntimeProvider with custom runtime"

issues-created: []

# Metrics
duration: 2min
completed: 2026-01-08
---

# Phase 7: AI Chat Interface - Plan 2 Summary

**assistant-ui React integration with custom Django runtime for SSE streaming and conversation management**

## Performance

- **Duration:** 2 min
- **Started:** 2026-01-08T23:10:22-08:00
- **Completed:** 2026-01-08T23:11:44-08:00
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- assistant-ui React library integrated (@assistant-ui/react, @assistant-ui/react-markdown, remark-gfm)
- Custom runtime implemented with useExternalStoreRuntime pattern connecting to Django SSE API
- SSE streaming parser with fetch ReadableStream handling text chunks and tool notifications
- ChatProvider component ready for Chat page integration
- TypeScript types defined for ChatMessage, ToolCall, ToolResult

## Task Commits

Each task was committed atomically:

1. **Task 1: Install assistant-ui and configure dependencies** - `e3a8e20` (feat)
2. **Task 2: Create custom runtime for Django SSE streaming** - `04ebd9c` (feat)
3. **Task 3: Create ChatProvider component wrapping runtime** - `692e876` (feat)

**Plan metadata:** `b680ccd` (docs: complete plan)

## Files Created/Modified

- `frontend/package.json` - Added @assistant-ui/react, @assistant-ui/react-markdown, remark-gfm dependencies
- `frontend/src/lib/types.ts` - Added ChatMessage, ToolCall, ToolResult types matching Django backend
- `frontend/src/lib/chatRuntime.ts` - Custom useChatRuntime hook with SSE streaming, message accumulation, error handling
- `frontend/src/components/ChatProvider.tsx` - Provider component wrapping AssistantRuntimeProvider with custom runtime

## Decisions Made

**useExternalStoreRuntime over Vercel AI SDK:** The plan explicitly specified not to use Vercel AI SDK packages (@ai-sdk/*, ai) since we're using a custom Django backend. Implemented custom runtime with useExternalStoreRuntime pattern from @assistant-ui/react for full control over Django SSE integration.

**fetch() with ReadableStream over EventSource API:** While EventSource API is simpler for SSE, we used fetch() with ReadableStream to get finer control over stream parsing, error handling, and compatibility with our JSON-based SSE format ("data: {json}\n\n"). This allows better integration with Django's streaming response format.

**Message accumulation strategy:** Accumulate all text chunks from a single assistant response into one ChatMessage object, updating it reactively as chunks arrive. This matches Django backend behavior where tool calling loops generate complete assistant responses before streaming.

**Type compatibility:** ChatMessage type defined with simple {role, content} structure matching Django backend's ChatMessage schema. This ensures seamless serialization between frontend and backend without transformation layers.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - implementation followed plan specifications without blockers.

## Next Phase Readiness

- assistant-ui infrastructure complete and ready for UI component integration
- ChatProvider component can be used in Chat page (Plan 3)
- Custom runtime connects to Django backend and streams responses
- TypeScript types ensure type safety between frontend and backend
- Ready for Phase 7 Plan 3: Chat UI components with Thread, Composer, Messages

---

*Phase: 07-ai-chat-interface*
*Completed: 2026-01-08*
