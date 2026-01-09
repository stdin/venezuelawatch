import { ThreadPrimitive, ComposerPrimitive, MessagePrimitive } from '@assistant-ui/react'
import { ChatProvider } from '../components/ChatProvider'
import './Chat.css'

/**
 * Chat page with Perplexity-style AI conversation interface.
 *
 * Features:
 * - Center-focused layout (max-width: 44rem)
 * - assistant-ui Thread component for message display
 * - Welcome message with suggestion chips
 * - Custom tool UI components for data preview
 * - Markdown rendering with inline citations
 */
export function Chat() {
  return (
    <ChatProvider>
      <div className="chat-container">
        <div className="chat-content">
          <ThreadPrimitive.Root className="chat-thread">
            {/* Welcome message with suggestions */}
            <ThreadPrimitive.Empty>
              <div className="chat-welcome">
                <h1 className="chat-welcome-title">
                  How can I help you with Venezuela intelligence today?
                </h1>

                <div className="chat-suggestions">
                  <ThreadPrimitive.Suggestion
                    prompt="What are today's high-risk events?"
                    method="replace"
                    autoSend
                  >
                    <div className="chat-suggestion-chip">
                      What are today's high-risk events?
                    </div>
                  </ThreadPrimitive.Suggestion>

                  <ThreadPrimitive.Suggestion
                    prompt="Show me trending entities this week"
                    method="replace"
                    autoSend
                  >
                    <div className="chat-suggestion-chip">
                      Show me trending entities this week
                    </div>
                  </ThreadPrimitive.Suggestion>

                  <ThreadPrimitive.Suggestion
                    prompt="Analyze risk trends for the last 30 days"
                    method="replace"
                    autoSend
                  >
                    <div className="chat-suggestion-chip">
                      Analyze risk trends for the last 30 days
                    </div>
                  </ThreadPrimitive.Suggestion>

                  <ThreadPrimitive.Suggestion
                    prompt="Who is affected by recent sanctions?"
                    method="replace"
                    autoSend
                  >
                    <div className="chat-suggestion-chip">
                      Who is affected by recent sanctions?
                    </div>
                  </ThreadPrimitive.Suggestion>
                </div>
              </div>
            </ThreadPrimitive.Empty>

            {/* Scrollable message area */}
            <ThreadPrimitive.Viewport className="chat-viewport" aria-label="Conversation thread">
              <ThreadPrimitive.Messages
                components={{
                  UserMessage: () => (
                    <MessagePrimitive.Root className="chat-message chat-message-user">
                      <MessagePrimitive.Content />
                    </MessagePrimitive.Root>
                  ),
                  AssistantMessage: () => (
                    <MessagePrimitive.Root className="chat-message chat-message-assistant">
                      <MessagePrimitive.Content />
                    </MessagePrimitive.Root>
                  )
                }}
              />
            </ThreadPrimitive.Viewport>

            {/* Composer at bottom */}
            <div className="chat-composer-container">
              <ComposerPrimitive.Root className="chat-composer">
                <ComposerPrimitive.Input
                  className="chat-composer-input"
                  placeholder="Ask about Venezuela intelligence..."
                  aria-label="Chat message input"
                />
                <ComposerPrimitive.Send className="chat-composer-send" aria-label="Send message">
                  Send
                </ComposerPrimitive.Send>
              </ComposerPrimitive.Root>
            </div>
          </ThreadPrimitive.Root>
        </div>
      </div>
    </ChatProvider>
  )
}
