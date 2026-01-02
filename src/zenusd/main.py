from brain.llm.factory import get_llm
from brain.planner import execute_plan


def main():
    llm = get_llm()

    while True:
        user_input = input("\nZenus > ")
        if user_input in ("exit", "quit"):
            break

        intent = llm.translate_intent(user_input)
        execute_plan(intent)


if __name__ == "__main__":
    main()
