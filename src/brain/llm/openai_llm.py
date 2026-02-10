from dotenv import load_dotenv # type: ignore
from openai import OpenAI # type: ignore

import os
from brain.llm.schemas import IntentIR


load_dotenv()


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL")
)


SYSTEM_PROMPT = """
You are an operating system intent compiler.

Rules:
- Convert user intent into structured OS actions
- NEVER invent tools
- NEVER include destructive actions unless explicitly requested
- Assume Linux filesystem
- Prefer safe, minimal steps

Allowed tools:
- FileOps: scan, mkdir, move, write_file, touch
- TextOps: read, write, append, search, count_lines, head, tail
- SystemOps: disk_usage, memory_info, cpu_info, list_processes, uptime
- ProcessOps: find_by_name, info, kill

Risk levels:
0 = read-only (info gathering)
1 = create/move (safe modifications)
2 = overwrite (data changes)
3 = delete/kill (destructive, requires explicit confirmation)

Return ONLY valid JSON matching the schema.
"""


class OpenAILLM:
    def translate_intent(self, user_input: str) -> IntentIR:
        response = client.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
            response_format=IntentIR,
        )


        return response.choices[0].message.parsed
