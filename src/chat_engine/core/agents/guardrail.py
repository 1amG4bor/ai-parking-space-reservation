from typing import List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from chat_engine.core.config.logging import logger
from chat_engine.core.prompts import GUARDRAIL_PROMPT


class GuardrailOutput(BaseModel):
    """Model output for guardrail checks,
    indicating whether the query is blocked and the reason for blocking if applicable.
    """

    blocked: bool = Field(..., description="Indicates if the query is blocked due to content moderation checks.")
    reason: Optional[str] = Field(default="", description="The reason why the query was blocked, if applicable.")
    suggestions: Optional[List[str]] = Field(
        default=[], description="Suggestions for the user to rephrase their query in a compliant manner, if applicable."
    )


DEFAULT_SUGGESTION = (
    "Please rephrase your question so that it complies with the general content guidelines"
    " and avoids offensive, unethical or harmful content."
)


class ModerationGuardrail:
    """A guardrail class to check the intent of the user's query before processing it."""

    def __init__(self):
        guard_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt_template = ChatPromptTemplate.from_template(GUARDRAIL_PROMPT, template_format="mustache")
        guard = guard_llm.with_structured_output(GuardrailOutput)
        self.guard_chain = prompt_template | guard

    def validate(self, user_input):
        """Validate the user's query to determine if it should be blocked based on content moderation checks."""
        logger.info(f"Guardrail check for the user's query: {user_input}")
        try:
            result = self.guard_chain.invoke({"user_query": user_input})
            if result.blocked:
                logger.warning(f"Guardrail blocked the query: {result.reason}.")
                if not result.suggestions:
                    suggestions = DEFAULT_SUGGESTION
                else:
                    suggestions = result.suggestions

                return {"blocked": True, "reason": result.reason, "suggestions": suggestions}

            return {"blocked": False}
        except Exception as err:  # pylint: disable=broad-except
            logger.error(f"Error during guardrail validation: {err}")
            return {
                "blocked": True,
                "reason": "An error occurred during content moderation checks. Please try again later.",
            }
