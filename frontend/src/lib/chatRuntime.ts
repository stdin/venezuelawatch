/**
 * Custom assistant-ui runtime for Django SSE streaming.
 *
 * Implements useExternalStoreRuntime pattern to connect assistant-ui components
 * to Django chat API with Server-Sent Events streaming.
 */
import { useState, useCallback } from 'react'
import { useExternalStoreRuntime } from '@assistant-ui/react'
import type { ChatMessage } from './types'

const API_BASE = '/api'

interface SSEChunk {
  type: 'content' | 'tool_use' | 'done' | 'error'
  text?: string
  tool?: string
  error?: string
}

/**
 * Custom hook for Django chat runtime with SSE streaming.
 *
 * Manages conversation state and connects to /api/chat endpoint.
 * Streams responses using fetch() with ReadableStream parsing.
 */
export function useChatRuntime() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const handleNewMessage = useCallback(async (userMessage: string) => {
    // Add user message to conversation
    const newUserMessage: ChatMessage = {
      role: 'user',
      content: userMessage
    }

    const updatedMessages = [...messages, newUserMessage]
    setMessages(updatedMessages)
    setIsLoading(true)

    // Initialize assistant message
    let assistantContent = ''
    const assistantMessage: ChatMessage = {
      role: 'assistant',
      content: ''
    }

    try {
      // Fetch from Django API with SSE streaming
      const response = await fetch(`${API_BASE}/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          messages: updatedMessages,
          stream: true
        })
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      // Parse SSE stream
      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('Response body is not readable')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) {
          break
        }

        // Decode chunk and add to buffer
        buffer += decoder.decode(value, { stream: true })

        // Process complete SSE messages (format: "data: {json}\n\n")
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || '' // Keep incomplete message in buffer

        for (const line of lines) {
          if (!line.trim() || !line.startsWith('data: ')) {
            continue
          }

          try {
            const jsonStr = line.slice(6) // Remove "data: " prefix
            const chunk: SSEChunk = JSON.parse(jsonStr)

            if (chunk.type === 'content' && chunk.text) {
              // Accumulate text content
              assistantContent += chunk.text
              assistantMessage.content = assistantContent

              // Update messages with streaming content
              setMessages([...updatedMessages, { ...assistantMessage }])
            } else if (chunk.type === 'tool_use' && chunk.tool) {
              // Tool execution notification (optional: show in UI)
              console.log(`Executing tool: ${chunk.tool}`)
            } else if (chunk.type === 'done') {
              // Stream complete
              break
            } else if (chunk.type === 'error') {
              // Error from backend
              throw new Error(chunk.error || 'Unknown error from chat API')
            }
          } catch (parseError) {
            console.error('Failed to parse SSE chunk:', parseError)
            // Continue processing other chunks
          }
        }
      }

      // Finalize assistant message
      setMessages([...updatedMessages, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)

      // Add error message to chat
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to get response'}`
      }
      setMessages([...updatedMessages, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }, [messages])

  // Create assistant-ui compatible runtime using useExternalStoreRuntime
  const runtime = useExternalStoreRuntime({
    messages: messages.map((msg, idx) => ({
      id: `msg-${idx}`,
      role: msg.role,
      content: [{ type: 'text' as const, text: msg.content }],
      createdAt: new Date() // Could enhance with actual timestamps
    })),
    isRunning: isLoading,
    convertMessage: (message) => message, // Pass through - messages already in correct format
    onNew: async (message) => {
      // Extract text content from assistant-ui message format
      const textContent = message.content
        .filter(part => part.type === 'text')
        .map(part => 'text' in part ? part.text : '')
        .join('')

      await handleNewMessage(textContent)
    }
  })

  return runtime
}
