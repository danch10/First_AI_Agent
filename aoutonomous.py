import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

MAX_STEPS = 10  # safety limit so it doesn't loop forever

def run_autonomous_task(goal, tools, run_tool_fn, client):
    print(f"\n🤖 Autonomous task started: {goal}")
    print("─" * 50)

    messages = [{"role": "user", "content": goal}]
    step = 0

    while step < MAX_STEPS:
        step += 1
        print(f"\n🔄 Step {step}")

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system="""You are an autonomous agent. You have been given a goal.
Break it into steps and use your tools to complete it.
Think carefully about what to do next after each tool result.
When the goal is fully complete, respond with your final answer WITHOUT using any tools.""",
            tools=tools,
            messages=messages
        )

        # If Claude stops using tools — task is done
        if response.stop_reason == "end_turn":
            final = next(b.text for b in response.content if hasattr(b, "text"))
            print(f"\n✅ Task complete!")
            print(f"─" * 50)
            return final

        # Claude wants to use tools — run them
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  🔧 {block.name}({block.input})")
                    result = run_tool_fn(block.name, block.input)
                    print(f"  📥 {result[:100]}...")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

    return "Task incomplete — reached maximum steps."