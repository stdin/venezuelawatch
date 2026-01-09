/**
 * ChatProvider component wrapping assistant-ui runtime.
 *
 * Provides conversation context to child components using
 * AssistantRuntimeProvider from @assistant-ui/react.
 */
import React from 'react'
import { AssistantRuntimeProvider } from '@assistant-ui/react'
import { useChatRuntime } from '../lib/chatRuntime'

// Import tool UI components to register them with makeAssistantToolUI
import { EventPreviewCard } from './chat/EventPreviewCard'
import { EntityPreviewCard, TrendingEntitiesCard } from './chat/EntityPreviewCard'
import { RiskTrendsChart } from './chat/RiskTrendsChart'

interface ChatProviderProps {
  children: React.ReactNode
}

/**
 * Provider component for AI chat functionality.
 *
 * Wraps children in AssistantRuntimeProvider with custom Django runtime.
 * Renders tool UI components to register them with assistant-ui.
 * Use this at the Chat page level to enable assistant-ui hooks.
 */
export function ChatProvider({ children }: ChatProviderProps) {
  const runtime = useChatRuntime()

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {/* Render tool UI components to register them (they don't display anything) */}
      <EventPreviewCard />
      <EntityPreviewCard />
      <TrendingEntitiesCard />
      <RiskTrendsChart />

      {children}
    </AssistantRuntimeProvider>
  )
}
