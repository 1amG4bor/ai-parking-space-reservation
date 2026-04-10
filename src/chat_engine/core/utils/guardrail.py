

# class Guardrail:
#     """A guardrail class to check the user's query before processing it.
#     The goal is to prevent exposure of sensitive data and/or avoid any inappropriate or malicious act."""
#     def __init__(self):
#         self.model = create_llm(model_name="gpt-5-nano")  # Use a lightweight model for guardrail checks

#     def check(self, prompt: str) -> bool:
#         self.logger.info(f"Guardrail check for the user's query: {prompt}")
#         result = self.agent.invoke_tool("guardrail_tool", {"query": prompt})
#         return result.get("is_safe", False)