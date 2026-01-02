# This is Zenus

from tools.registry import TOOLS
from safety.policy import check_step


def execute_plan(intent):
    print(f"\nGoal: {intent.goal}\n")

    for i, step in enumerate(intent.steps, 1):
        print(f"Step {i}: {step.tool}.{step.action} {step.args}")

    if intent.requires_confirmation:
        confirm = input("\nExecute this plan? (y/n): ")
        if confirm.lower() != "y":
            print("Aborted.")
            return

    for step in intent.steps:
        check_step(step)

        tool = TOOLS.get(step.tool)
        action = getattr(tool, step.action)

        result = action(**step.args)
        print(f"✔ {result}")
