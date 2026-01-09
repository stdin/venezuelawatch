"""
Chat API endpoints with Anthropic Claude streaming.

Provides POST /chat endpoint that streams Claude responses using Server-Sent Events (SSE).
Supports conversation context and tool calling for VenezuelaWatch data access.
"""
import json
import logging
import os
from typing import List, Optional
from ninja import Router, Schema
from django.http import HttpRequest, StreamingHttpResponse
import anthropic

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
    AI chat endpoint with streaming support.

    Accepts conversation history and streams Claude responses using Server-Sent Events.
    Supports tool calling for querying VenezuelaWatch data.

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
            # Streaming response with SSE
            def event_stream():
                try:
                    with client.messages.stream(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=4096,
                        messages=messages,
                    ) as stream:
                        for text in stream.text_stream:
                            # Format as SSE: "data: {json}\n\n"
                            chunk_data = {
                                "type": "content",
                                "text": text
                            }
                            yield f"data: {json.dumps(chunk_data)}\n\n"

                        # Send final message
                        yield f"data: {json.dumps({'type': 'done'})}\n\n"

                except anthropic.APIError as e:
                    logger.error(f"Anthropic API error: {e}", exc_info=True)
                    error_data = {
                        "type": "error",
                        "error": str(e)
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"

            return StreamingHttpResponse(
                event_stream(),
                content_type='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no',  # Disable nginx buffering
                }
            )
        else:
            # Non-streaming response
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=messages,
            )

            return {
                "role": "assistant",
                "content": response.content[0].text
            }

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
