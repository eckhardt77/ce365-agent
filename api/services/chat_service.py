"""
TechCare Bot - Chat Service
Chat Logic mit Anthropic Tool Use API
"""

from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import AsyncGenerator, Dict, Any, List
import logging
import json

from api.models import Conversation, Message, ToolCall
from api.models.message import MessageRole
from api.models.conversation import ConversationState
from api.config import settings

# Import TechCare Core Tools
from techcare.tools.registry import ToolRegistry
from techcare.tools.executor import CommandExecutor
from techcare.config.system_prompt import get_system_prompt

logger = logging.getLogger(__name__)


class ChatService:
    """Chat Service mit Anthropic Tool Use"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.tool_registry = ToolRegistry()
        self.executor = CommandExecutor(self.tool_registry)

        # Register tools (aus bestehender TechCare Logic)
        self._register_tools()

    def _register_tools(self):
        """Register alle TechCare Tools"""
        # TODO: Import und registriere Tools
        # from techcare.tools.audit import SystemInfoTool, ProcessMonitorTool
        # self.tool_registry.register(SystemInfoTool())
        # self.tool_registry.register(ProcessMonitorTool())
        # ...
        logger.info(f"Registered {len(self.tool_registry._tools)} tools")

    async def chat_stream(
        self,
        conversation_id: str,
        user_message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Chat Stream mit Tool Use Loop

        Yields:
            Dict mit:
                - type: "content" | "tool_use" | "tool_result" | "done" | "error"
                - content: str
                - tool_name: str (optional)
                - tool_input: dict (optional)
        """
        # Load conversation
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            yield {"type": "error", "error": "Conversation not found"}
            return

        # Add user message to database
        await self._save_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=user_message
        )

        # Load message history
        messages = await self._get_messages(conversation_id)

        # System Prompt
        system_prompt = get_system_prompt(conversation.state)

        # Tool Definitions
        tool_definitions = self.tool_registry.get_tool_definitions()

        try:
            # Anthropic API Call mit Streaming
            async with self.anthropic.messages.stream(
                model=settings.claude_model,
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                tools=tool_definitions if tool_definitions else None,
            ) as stream:

                assistant_content = ""
                tool_uses = []

                # Stream chunks
                async for event in stream:
                    # Content Chunk
                    if hasattr(event, 'type') and event.type == "content_block_delta":
                        if hasattr(event.delta, 'text'):
                            chunk_text = event.delta.text
                            assistant_content += chunk_text

                            yield {
                                "type": "content",
                                "content": chunk_text
                            }

                    # Tool Use
                    elif hasattr(event, 'type') and event.type == "content_block_start":
                        if hasattr(event.content_block, 'type') and event.content_block.type == "tool_use":
                            tool_use = {
                                "id": event.content_block.id,
                                "name": event.content_block.name,
                                "input": {}
                            }
                            tool_uses.append(tool_use)

                            yield {
                                "type": "tool_use",
                                "tool_name": event.content_block.name
                            }

                # Message done
                final_message = await stream.get_final_message()

                # Save assistant message
                await self._save_message(
                    conversation_id=conversation_id,
                    role=MessageRole.ASSISTANT,
                    content=assistant_content or "(Tool use only)",
                    input_tokens=final_message.usage.input_tokens,
                    output_tokens=final_message.usage.output_tokens
                )

                # Execute Tools wenn vorhanden
                if final_message.stop_reason == "tool_use":
                    # Extract tool uses
                    for content_block in final_message.content:
                        if content_block.type == "tool_use":
                            tool_name = content_block.name
                            tool_input = content_block.input

                            yield {
                                "type": "tool_executing",
                                "tool_name": tool_name,
                                "tool_input": tool_input
                            }

                            # Execute tool
                            tool_result = await self._execute_tool(
                                conversation_id=conversation_id,
                                conversation_state=conversation.state,
                                tool_name=tool_name,
                                tool_input=tool_input
                            )

                            yield {
                                "type": "tool_result",
                                "tool_name": tool_name,
                                "success": tool_result["success"],
                                "output": tool_result["output"]
                            }

                            # Recursive: Continue conversation mit tool result
                            # (vereinfacht - in Production würde man das rekursiv machen)

                # Done
                yield {
                    "type": "done",
                    "conversation_id": conversation_id
                }

        except Exception as e:
            logger.error(f"Chat stream error: {e}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e)
            }

    async def _get_messages(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get message history in Anthropic format"""
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sequence)
        )
        messages = result.scalars().all()

        # Convert to Anthropic format
        anthropic_messages = []
        for msg in messages:
            if msg.role == MessageRole.USER:
                anthropic_messages.append({
                    "role": "user",
                    "content": msg.content
                })
            elif msg.role == MessageRole.ASSISTANT:
                anthropic_messages.append({
                    "role": "assistant",
                    "content": msg.content
                })

        return anthropic_messages

    async def _save_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        input_tokens: int = None,
        output_tokens: int = None
    ):
        """Save message to database"""
        # Get next sequence number
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sequence.desc())
        )
        last_message = result.scalar_one_or_none()
        next_sequence = (last_message.sequence + 1) if last_message else 0

        # Create message
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sequence=next_sequence,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

        self.db.add(message)
        await self.db.commit()

        return message

    async def _execute_tool(
        self,
        conversation_id: str,
        conversation_state: ConversationState,
        tool_name: str,
        tool_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tool und log in database"""
        # Load conversation
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()

        # Get tool
        tool = self.tool_registry.get_tool(tool_name)

        if not tool:
            return {
                "success": False,
                "output": f"Tool {tool_name} not found"
            }

        # Check if tool can be executed
        if not conversation.can_execute_tool(tool.tool_type):
            return {
                "success": False,
                "output": f"Tool {tool_name} not allowed in state {conversation.state.value}"
            }

        # Execute tool
        import time
        start_time = time.time()

        try:
            output = await self.executor.execute_tool(tool_name, tool_input)
            success = True
            error_message = None
        except Exception as e:
            output = str(e)
            success = False
            error_message = str(e)

        execution_time_ms = (time.time() - start_time) * 1000

        # Save tool call
        tool_call = ToolCall(
            conversation_id=conversation_id,
            tool_name=tool_name,
            tool_type=tool.tool_type,
            tool_input=tool_input,
            tool_output=output,
            success=success,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
            requires_approval=tool.tool_type == "repair",
            approved=False  # TODO: Implement approval flow
        )

        self.db.add(tool_call)
        await self.db.commit()

        return {
            "success": success,
            "output": output
        }
