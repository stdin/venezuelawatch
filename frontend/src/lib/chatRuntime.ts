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
  type: 'content' | 'tool_result' | 'done' | 'error'
  text?: string
  tool?: string
  tool_call_id?: string
  result?: any
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

    // Initialize assistant message with content parts
    let textContent = ''
    const toolCalls: Array<{ toolName: string; toolCallId: string; result: any }> = []

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
              textContent += chunk.text

              // Update messages with streaming content (text + any tool results collected so far)
              const currentMessage: ChatMessage = {
                role: 'assistant',
                content: textContent,
                toolResults: toolCalls.length > 0 ? toolCalls : undefined
              }
              setMessages([...updatedMessages, currentMessage])
            } else if (chunk.type === 'tool_result' && chunk.tool && chunk.result) {
              // Tool execution result - add immediately and update message
              toolCalls.push({
                toolName: chunk.tool,
                toolCallId: chunk.tool_call_id || `tool-${Date.now()}`,
                result: chunk.result
              })
              console.log(`Tool executed: ${chunk.tool}`, chunk.result)

              // Update message with new tool result
              const currentMessage: ChatMessage = {
                role: 'assistant',
                content: textContent,
                toolResults: [...toolCalls]
              }
              setMessages([...updatedMessages, currentMessage])
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

      // Finalize assistant message (combine text and tool results)
      const finalMessage: ChatMessage = {
        role: 'assistant',
        content: textContent,
        toolResults: toolCalls.length > 0 ? toolCalls : undefined
      }
      setMessages([...updatedMessages, finalMessage])
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
    messages: messages.map((msg, idx) => {
      // Build content parts: text + tool-call results
      const contentParts: Array<{ type: 'text'; text: string } | { type: 'tool-call'; toolCallId: string; toolName: string; args: any; result?: any }> = []

      // Add text content if present
      if (msg.content) {
        contentParts.push({ type: 'text' as const, text: msg.content })
      }

      // Add tool results if present (for assistant messages)
      if (msg.toolResults) {
        for (const toolResult of msg.toolResults) {
          contentParts.push({
            type: 'tool-call' as const,
            toolCallId: toolResult.toolCallId,
            toolName: toolResult.toolName,
            args: {}, // Args not available from backend, empty object
            result: toolResult.result
          })
        }
      }

      const message = {
        id: `msg-${idx}`,
        role: msg.role,
        content: contentParts,
        createdAt: new Date()
      }

      // Debug: Log messages with tool results
      if (msg.toolResults && msg.toolResults.length > 0) {
        console.log('Message with tool results:', message)
      }

      return message
    }),
    isRunning: isLoading,
    convertMessage: (message) => message,
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
