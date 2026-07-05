from typing import Callable

from langchain.agents.middleware import ModelRequest, ModelResponse, PIIMiddleware, wrap_model_call, wrap_tool_call
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langchain_openai.middleware import OpenAIModerationMiddleware

from chat_engine.core.config.logging import logger

# Redact emails in user input before sending to model
email_guard = PIIMiddleware("email", strategy="redact")
# Mask credit card numbers in user input before sending to model.
credit_card_guard = PIIMiddleware("credit_card", strategy="mask")

# Moderate user input to prevent policy violations
moderation_guard = OpenAIModerationMiddleware(
    check_input=True,
    check_output=False,  # Only check user input, not model output
    exit_behavior="end",  # Stops execution if violation is found
    violation_message="Your query is inappropriate therefore cannot be processed. Please rephrase and try again.",
)


@wrap_model_call
def model_logger_middleware(request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]) -> ModelResponse:
    """Middleware to log details related to model calls."""
    # logger.info(f"Model call initiated with prompt: '{request.prompt}'.")
    response = handler(request)
    logger.info(f"Model call completed with response: '{response.result[-1].content}'.")
    return response


@wrap_tool_call
def tool_logger_middleware(request: ToolCallRequest, handler: Callable) -> ToolMessage:
    """Middleware to log details related to tool calls."""
    # logger.info(f"Tool call initiated with input: '{request.input}'.")
    response = handler(request)
    # logger.info(f"Tool call completed with output: '{response.output}'.")
    return response
