from langchain.agents.middleware import PIIMiddleware
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
    violation_message="Your query is inappropriate therefore cannot be processed. Please rephrase and try again."
)
