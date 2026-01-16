"""Claude Bedrock client for conversational AI."""

import json
import boto3
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from utils.logger import setup_logger
from utils.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    BEDROCK_MODEL_ID
)

logger = setup_logger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime and pandas objects."""

    def default(self, obj):
        if isinstance(obj, (pd.Timestamp, datetime, date)):
            return obj.isoformat()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if pd.isna(obj):
            return None
        return super().default(obj)


class ClaudeClient:
    """Client for AWS Bedrock Claude API."""

    def __init__(self):
        """Initialize Claude client."""
        from botocore.config import Config

        # Configure with increased timeouts for long responses
        config = Config(
            read_timeout=300,  # 5 minutes for reading response
            connect_timeout=10,  # 10 seconds for connection
            retries={'max_attempts': 2}
        )

        self.bedrock = boto3.client(
            service_name='bedrock-runtime',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
            config=config
        )
        self.model_id = BEDROCK_MODEL_ID
        self.conversation_history = []

        logger.info(f"Claude client initialized with model {self.model_id}")

    def send_message(self,
                    user_message: str,
                    tools: Optional[List[Dict[str, Any]]] = None,
                    system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Send a message to Claude and get response.

        Args:
            user_message: User's message
            tools: Optional list of tool definitions for function calling
            system_prompt: Optional system prompt

        Returns:
            Claude's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Prepare request
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 8192,
            "messages": self.conversation_history,
            "temperature": 0.7
        }

        if system_prompt:
            request_body["system"] = system_prompt

        if tools:
            request_body["tools"] = tools

        try:
            # Call Bedrock API
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )

            # Parse response
            response_body = json.loads(response['body'].read())

            # Add assistant response to history (with validation)
            content = response_body.get("content", [])
            if content:  # ✅ FIX: Only add if content is not empty
                self.conversation_history.append({
                    "role": "assistant",
                    "content": content
                })
            else:
                logger.warning("Received empty content from Claude, not adding to history")

            logger.info(f"Claude response received (stop_reason: {response_body.get('stop_reason')})")

            return response_body

        except Exception as e:
            logger.error(f"Failed to call Claude API: {e}")
            raise

    def handle_tool_use(self,
                       response: Dict[str, Any],
                       tool_executor: Any,
                       tools: Optional[List[Dict[str, Any]]] = None,
                       system_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Handle tool use from Claude's response.

        Args:
            response: Claude's response containing tool use
            tool_executor: Function executor instance
            tools: Optional tool definitions (needed for multi-turn)
            system_prompt: Optional system prompt (needed for multi-turn)

        Returns:
            Final response after tool execution, or None if no tool use
        """
        content = response.get("content", [])

        # Check if response contains tool use
        tool_uses = [block for block in content if block.get("type") == "tool_use"]

        if not tool_uses:
            return None

        # Execute each tool
        tool_results = []
        for tool_use in tool_uses:
            tool_name = tool_use.get("name")
            tool_input = tool_use.get("input", {})
            tool_use_id = tool_use.get("id")

            logger.info(f"Executing tool: {tool_name} with input: {tool_input}")

            try:
                # Execute the tool
                result = tool_executor.execute(tool_name, tool_input)

                # Serialize result with validation
                result_json = json.dumps(result, cls=DateTimeEncoder)

                # ✅ FIX: Validate result is not empty
                if not result_json or result_json == "null" or result_json == "{}":
                    result_json = json.dumps({"message": "No data found"})

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": result_json
                })

                logger.info(f"Tool {tool_name} executed successfully")

            except Exception as e:
                logger.error(f"Tool execution failed: {e}", exc_info=True)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": json.dumps({"error": str(e)})
                })

        # Send tool results back to Claude
        self.conversation_history.append({
            "role": "user",
            "content": tool_results
        })

        # ✅ FIX: Include system_prompt and tools in follow-up request
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 8192,
            "messages": self.conversation_history,
            "temperature": 0.7
        }

        if system_prompt:  # ✅ FIX: Preserve system prompt
            request_body["system"] = system_prompt

        if tools:  # ✅ FIX: Preserve tools for multi-turn
            request_body["tools"] = tools

        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )

            response_body = json.loads(response['body'].read())

            # Add to history (with validation)
            content = response_body.get("content", [])
            if content:  # ✅ FIX: Only add if content is not empty
                self.conversation_history.append({
                    "role": "assistant",
                    "content": content
                })
            else:
                logger.warning("Received empty content after tool use, not adding to history")

            return response_body

        except Exception as e:
            logger.error(f"Failed to get final response: {e}")
            raise

    def chat(self,
            user_message: str,
            tools: Optional[List[Dict[str, Any]]] = None,
            tool_executor: Optional[Any] = None,
            system_prompt: Optional[str] = None,
            max_tool_iterations: int = 5) -> str:
        """Complete chat interaction with tool support.

        Args:
            user_message: User's message
            tools: Optional tool definitions
            tool_executor: Optional tool executor
            system_prompt: Optional system prompt
            max_tool_iterations: Maximum number of tool call iterations (default: 5)

        Returns:
            Final text response from Claude
        """
        # Get initial response
        response = self.send_message(user_message, tools, system_prompt)

        # ✅ FIX: Handle multiple rounds of tool calls
        iterations = 0
        while tool_executor and response.get("stop_reason") == "tool_use" and iterations < max_tool_iterations:
            logger.info(f"Tool use iteration {iterations + 1}/{max_tool_iterations}")

            # Pass tools and system_prompt to maintain context
            response = self.handle_tool_use(response, tool_executor, tools, system_prompt)

            if not response:
                logger.error("Tool use handler returned None")
                break

            iterations += 1

        # ✅ FIX: Warn if max iterations reached
        if iterations >= max_tool_iterations:
            logger.warning(f"Reached max tool iterations ({max_tool_iterations})")

        # Extract text response
        text_response = ""
        content = response.get("content", [])

        for block in content:
            if block.get("type") == "text":
                text_response += block.get("text", "")

        # ✅ FIX: Return helpful message if no text was generated
        if not text_response:
            logger.warning("No text response generated by Claude")
            text_response = "I was unable to generate a response. Please try rephrasing your question."

        return text_response

    def chat_stream(self,
                   user_message: str,
                   tools: Optional[List[Dict[str, Any]]] = None,
                   tool_executor: Optional[Any] = None,
                   system_prompt: Optional[str] = None,
                   max_tool_iterations: int = 5):
        """Complete chat interaction with streaming support.

        Args:
            user_message: User's message
            tools: Optional tool definitions
            tool_executor: Optional tool executor
            system_prompt: Optional system prompt
            max_tool_iterations: Maximum number of tool call iterations

        Yields:
            Text chunks as they are generated
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Prepare request
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 8192,
            "messages": self.conversation_history,
            "temperature": 0.7
        }

        if system_prompt:
            request_body["system"] = system_prompt

        if tools:
            request_body["tools"] = tools

        iterations = 0
        while iterations <= max_tool_iterations:
            try:
                # Call Bedrock API with streaming
                response = self.bedrock.invoke_model_with_response_stream(
                    modelId=self.model_id,
                    body=json.dumps(request_body)
                )

                # Process the stream
                full_response_text = ""
                tool_uses = []
                current_tool_use = None
                stop_reason = None

                for event in response['body']:
                    chunk = json.loads(event['chunk']['bytes'].decode())

                    if chunk['type'] == 'content_block_start':
                        block = chunk.get('content_block', {})
                        if block.get('type') == 'tool_use':
                            current_tool_use = {
                                'id': block.get('id'),
                                'name': block.get('name'),
                                'input_json': ''
                            }

                    elif chunk['type'] == 'content_block_delta':
                        delta = chunk.get('delta', {})
                        if delta.get('type') == 'text_delta':
                            text = delta.get('text', '')
                            full_response_text += text
                            yield text
                        elif delta.get('type') == 'input_json_delta':
                            if current_tool_use:
                                current_tool_use['input_json'] += delta.get('partial_json', '')

                    elif chunk['type'] == 'content_block_stop':
                        if current_tool_use:
                            try:
                                current_tool_use['input'] = json.loads(current_tool_use['input_json']) if current_tool_use['input_json'] else {}
                            except json.JSONDecodeError:
                                current_tool_use['input'] = {}
                            tool_uses.append({
                                'type': 'tool_use',
                                'id': current_tool_use['id'],
                                'name': current_tool_use['name'],
                                'input': current_tool_use['input']
                            })
                            current_tool_use = None

                    elif chunk['type'] == 'message_delta':
                        stop_reason = chunk.get('delta', {}).get('stop_reason')

                # Build content for history
                content = []
                if full_response_text:
                    content.append({'type': 'text', 'text': full_response_text})
                content.extend(tool_uses)

                # ✅ FIX: Always add content, even if empty (to maintain history integrity)
                if content:
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": content
                    })
                elif not tool_uses:
                    # Empty response - add placeholder to maintain history
                    logger.warning("Empty response from Claude in streaming, adding placeholder")
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": [{"type": "text", "text": ""}]
                    })

                # Handle tool use if needed
                if stop_reason == 'tool_use' and tool_executor and tool_uses:
                    iterations += 1
                    logger.info(f"Tool use iteration {iterations}/{max_tool_iterations}")

                    # Execute tools
                    tool_results = []
                    for tool_use in tool_uses:
                        tool_name = tool_use.get("name")
                        tool_input = tool_use.get("input", {})
                        tool_use_id = tool_use.get("id")

                        logger.info(f"Executing tool: {tool_name}")
                        yield f"\n\n*Calling {tool_name}...*\n\n"

                        try:
                            result = tool_executor.execute(tool_name, tool_input)
                            result_json = json.dumps(result, cls=DateTimeEncoder)
                            if not result_json or result_json == "null" or result_json == "{}":
                                result_json = json.dumps({"message": "No data found"})
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": result_json
                            })
                            logger.info(f"✓ Tool {tool_name} result added to history (use_id: {tool_use_id})")
                        except Exception as e:
                            logger.error(f"Tool execution failed: {e}", exc_info=True)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": json.dumps({"error": str(e)})
                            })
                            logger.info(f"✓ Tool {tool_name} error added to history (use_id: {tool_use_id})")

                    # ✅ FIX: Validate all tool results are present before adding to history
                    if len(tool_results) != len(tool_uses):
                        logger.error(f"Tool result count mismatch! Expected {len(tool_uses)}, got {len(tool_results)}")
                        # Add missing tool results as errors
                        for tool_use in tool_uses:
                            if not any(r["tool_use_id"] == tool_use.get("id") for r in tool_results):
                                logger.error(f"Missing result for tool_use_id: {tool_use.get('id')}")
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use.get("id"),
                                    "content": json.dumps({"error": "Tool result missing"})
                                })

                    # Add tool results to history
                    self.conversation_history.append({
                        "role": "user",
                        "content": tool_results
                    })
                    logger.info(f"✓ Added {len(tool_results)} tool results to conversation history")

                    # Prepare next request
                    request_body["messages"] = self.conversation_history
                else:
                    # No more tool calls, we're done
                    break

            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield f"\n\nError: {str(e)}"
                break

        if iterations >= max_tool_iterations:
            logger.warning(f"Reached max tool iterations ({max_tool_iterations})")

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")

    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversation history.

        Returns:
            List of conversation messages
        """
        return self.conversation_history
