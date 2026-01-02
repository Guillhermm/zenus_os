
from dotenv import load_dotenv # type: ignore
from openai import OpenAI # type: ignore

import json
import os
from brain.llm.schemas import IntentIR


load_dotenv()


DEEPSEEK_API_KEY=os.getenv("DEEPSEEK_API_KEY"),
DEEPSEEK_API_URL=os.getenv("DEEPSEEK_API_BASE_URL")
MODEL="deepseek-chat"


client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_API_BASE_URL")
)


SYSTEM_PROMPT = """
You are an operating system intent compiler.

You MUST output a JSON object that EXACTLY matches this schema:

{
  "goal": string,                         // Short description of user intent
  "requires_confirmation": true | false, // true if filesystem changes occur
  "steps": [
    {
      "tool": "FileOps",
      "action": "scan" | "mkdir" | "move",
      "args": object,
      "risk": 0 | 1 | 2 | 3
    }
  ]
}

Risk levels:
0 = read-only
1 = create/move
2 = overwrite
3 = delete (avoid unless explicit)

Rules:
- Output ONLY valid JSON
- No markdown
- No explanations
- No extra keys
- No missing keys
- Use ONLY the tools listed
- Assume Linux filesystem
- Use ~ for home directory
- Never delete files unless explicitly requested
- Prefer minimal number of steps

If the user asks to organize files:
- First create required directories
- Then move files

Return ONLY valid JSON matching the schema.
"""


def extract_json(text: str) -> dict:
  start = text.find("{")
  end = text.rfind("}")
  if start == -1 or end == -1:
      raise RuntimeError("No JSON object found in model output")

  snippet = text[start:end + 1]
  return json.loads(snippet)


class DeepSeekLLM:
    def translate_intent(self, user_input: str) -> IntentIR:
        response = client.chat.completions.parse(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
        )

        content = response.choices[0].message.content

        try:
            data = extract_json(content)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"DeepSeek returned invalid JSON:\n{content}"
            ) from e

        return IntentIR.model_validate(data)
