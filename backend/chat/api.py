"""
Chat API endpoints with Anthropic Claude streaming.

Provides POST /chat endpoint that streams Claude responses using Server-Sent Events (SSE).
Supports conversation context and tool calling for VenezuelaWatch data access.
"""
import json
import logging
import os
from typing import List, Optional, Any, Dict
from ninja import Router, Schema
from django.http import HttpRequest, StreamingHttpResponse
import anthropic
from anthropic.types import MessageStreamEvent

from chat.tools import TOOLS, execute_tool

logger = logging.getLogger(__name__)

chat_router = Router(tags=["AI Chat"])


# Request/Response schemas
class ChatMessage(Schema):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(Schema):
    messages: List[ChatMessage]
    stream: bool = True


@chat_router.post("/")
def chat(request: HttpRequest, payload: ChatRequest):
    """
    AI chat endpoint with streaming support and tool calling.

    Accepts conversation history and streams Claude responses using Server-Sent Events.
    Supports tool calling for querying VenezuelaWatch data (events, entities, risk trends).

    Args:
        payload: ChatRequest with messages list and stream flag

    Returns:
        StreamingHttpResponse with SSE chunks if stream=True, else JSON response
    """
    # Get Anthropic API key from environment
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return StreamingHttpResponse(
            iter([f"data: {json.dumps({'error': 'ANTHROPIC_API_KEY not configured'})}\n\n"]),
            content_type='text/event-stream',
            status=500
        )

    # Convert messages to Anthropic format
    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in payload.messages
    ]

    try:
        client = anthropic.Anthropic(api_key=api_key)

        if payload.stream:
            # Streaming response with SSE and tool calling
            def event_stream():
                try:
                    # Handle tool calling loop
                    conversation_messages = messages.copy()

                    while True:
                        # Create message with tools
                        with client.messages.stream(
                            model="claude-3-5-sonnet-20241022",
                            max_tokens=4096,
                            messages=conversation_messages,
                            tools=TOOLS,
                        ) as stream:
                            # Stream text content
                            for text in stream.text_stream:
                                chunk_data = {
                                    "type": "content",
                                    "text": text
                                }
                                yield f"data: {json.dumps(chunk_data)}\n\n"

                            # Get final message to check for tool use
                            final_message = stream.get_final_message()

                        # Check if Claude wants to use tools
                        tool_use_blocks = [
                            block for block in final_message.content
                            if block.type == "tool_use"
                        ]

                        if not tool_use_blocks:
                            # No tool use - done
                            yield f"data: {json.dumps({'type': 'done'})}\n\n"
                            break

                        # Execute tools and add results to conversation
                        # Add assistant's response (with tool_use blocks) to conversation
                        conversation_messages.append({
                            "role": "assistant",
                            "content": final_message.content
                        })

                        # Execute tools and build tool_result blocks
                        tool_results = []
                        for tool_block in tool_use_blocks:
                            logger.info(f"Executing tool: {tool_block.name} with input: {tool_block.input}")

                            # Execute tool
                            result = execute_tool(tool_block.name, tool_block.input)

                            # Add result
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_block.id,
                                "content": json.dumps(result),
                            })

                            # Stream tool execution notification
                            yield f"data: {json.dumps({'type': 'tool_use', 'tool': tool_block.name})}\n\n"

                        # Add tool results to conversation
                        conversation_messages.append({
                            "role": "user",
                            "content": tool_results
                        })

                        # Continue loop to get Claude's response with tool results

                except anthropic.APIError as e:
                    logger.error(f"Anthropic API error: {e}", exc_info=True)
                    error_data = {
                        "type": "error",
                        "error": str(e)
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                except Exception as e:
                    logger.error(f"Unexpected error in chat streaming: {e}", exc_info=True)
                    yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

            return StreamingHttpResponse(
                event_stream(),
                content_type='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no',  # Disable nginx buffering
                }
            )
        else:
            # Non-streaming response with tool calling
            conversation_messages = messages.copy()

            while True:
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4096,
                    messages=conversation_messages,
                    tools=TOOLS,
                )

                # Check for tool use
                tool_use_blocks = [
                    block for block in response.content
                    if block.type == "tool_use"
                ]

                if not tool_use_blocks:
                    # No tool use - return response
                    text_content = next(
                        (block.text for block in response.content if hasattr(block, 'text')),
                        ""
                    )
                    return {
                        "role": "assistant",
                        "content": text_content
                    }

                # Execute tools
                conversation_messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                tool_results = []
                for tool_block in tool_use_blocks:
                    result = execute_tool(tool_block.name, tool_block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": json.dumps(result),
                    })

                conversation_messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # Continue loop

    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}", exc_info=True)
        return StreamingHttpResponse(
            iter([f"data: {json.dumps({'error': str(e)})}\n\n"]),
            content_type='text/event-stream',
            status=500
        )
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
        return StreamingHttpResponse(
            iter([f"data: {json.dumps({'error': 'Internal server error'})}\n\n"]),
            content_type='text/event-stream',
            status=500
        )
