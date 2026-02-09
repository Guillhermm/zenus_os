
from dotenv import load_dotenv # type: ignore
from openai import OpenAI # type: ignore

import json
import os
from brain.llm.schemas import IntentIR


load_dotenv()


DEEPSEEK_API_KEY=os.getenv("DEEPSEEK_API_KEY"),
DEEPSEEK_API_URL=os.getenv("DEEPSEEK_API_BASE_URL")
MODEL=os.getenv("LLM_MODEL")
MAX_TOKENS=int(os.getenv("LLM_TOKENS"))

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
      "tool": "FileOps" | "SystemOps" | "ProcessOps",
      "action": string,
      "args": object,
      "risk": 0 | 1 | 2 | 3
    }
  ]
}

Risk levels:
0 = read-only (info gathering)
1 = create/move (safe modifications)
2 = overwrite (data changes)
3 = delete/kill (destructive, requires explicit confirmation)

Rules:
- Output ONLY valid JSON
- No markdown
- No explanations
- No extra keys
- No missing keys
- Use ONLY the tools listed below
- Assume Linux filesystem
- Use ~ for home directory
- Never delete files unless explicitly requested
- Prefer minimal number of steps

AVAILABLE TOOLS:

FileOps:
- scan(path: string): list directory contents
- mkdir(path: string): create directory
- move(source: string, destination: string): move files
- write_file(path: string, content: string): create file with content
- touch(path: string): create empty file

SystemOps:
- disk_usage(path: string = "/"): show disk space
- memory_info(): show memory usage
- cpu_info(): show CPU usage
- list_processes(limit: int = 10): list top processes
- uptime(): show system uptime

ProcessOps:
- find_by_name(name: string): find processes by name
- info(pid: int): get process details
- kill(pid: int, force: bool = false): terminate process (risk=3)

PROJECT CREATION RULES:
- A project consists of:
  (1) A root directory
  (2) A minimal runnable entry point
  (3) A README explaining how to run it
- If the user asks for a project:
  - You MUST create files, not only directories
  - You MUST populate code files with valid content
- Generated code must be minimal but functional
- Prefer standard conventions for the requested stack

IMPORTANT:
- NEVER include "content" in FileOps.move
- To create a file with content, ALWAYS use FileOps.write_file
- FileOps.move is ONLY for moving existing files
- If content is provided, the action MUST be FileOps.write_file

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
            max_tokens=MAX_TOKENS*1024
        )

        content = response.choices[0].message.content

        try:
            data = extract_json(content)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"DeepSeek returned invalid JSON:\n{content}"
            ) from e

        return IntentIR.model_validate(data)
