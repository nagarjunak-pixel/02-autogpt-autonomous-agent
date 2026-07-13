#!/usr/bin/env python3
"""
#2 · AutoGPT — Autonomous Agent Demo
⭐ ~185k GitHub Stars
=====================================
AutoGPT was the FIRST truly autonomous AI agent. Give it a goal,
and it breaks it down into tasks, executes them, and self-corrects.

WHAT STUDENTS LEARN:
  • The Goal → Think → Act → Observe loop (ReAct pattern)
  • How autonomous agents make decisions without human input
  • Self-correction and retry mechanisms
  • Why AutoGPT started the entire AI agent revolution

OUTPUT: Agent autonomously researches a topic through think-act-observe cycles.
"""

import time
from datetime import datetime


class AutonomousAgent:
    """AutoGPT-style autonomous agent with goal decomposition."""

    def __init__(self, name: str, goal: str):
        self.name = name
        self.goal = goal
        self.memory: list[str] = []
        self.completed_tasks: list[str] = []
        self.iteration = 0
        self.max_iterations = 5

    def think(self) -> dict:
        """THINK: Analyze goal and decide next action."""
        self.iteration += 1

        # Simulated reasoning based on iteration
        plans = [
            {"thought": "I need to break down this goal into research subtasks",
             "action": "plan", "target": "decompose goal into 3 subtasks"},
            {"thought": "First, I should search for recent news on this topic",
             "action": "search", "target": f"latest news: {self.goal}"},
            {"thought": "Now I should analyze the key findings from my search",
             "action": "analyze", "target": "synthesize search results into insights"},
            {"thought": "I should compile my findings into a structured report",
             "action": "write", "target": "create summary report with key takeaways"},
            {"thought": "Let me review the report for quality and completeness",
             "action": "review", "target": "quality check and final output"},
        ]

        if self.iteration <= len(plans):
            return plans[self.iteration - 1]
        return {"thought": "Goal achieved!", "action": "complete", "target": "done"}

    def act(self, action: dict) -> dict:
        """ACT: Execute the decided action."""
        action_type = action["action"]
        target = action["target"]

        if action_type == "plan":
            result = {
                "status": "success",
                "output": [
                    f"Subtask 1: Research current state of '{self.goal}'",
                    f"Subtask 2: Identify key players and developments",
                    f"Subtask 3: Summarize findings with actionable insights",
                ],
            }
        elif action_type == "search":
            result = {
                "status": "success",
                "output": [
                    f"Found: AI agent adoption in India growing 340% YoY",
                    f"Found: Hyderabad emerging as India's AI hub with 200+ startups",
                    f"Found: Government launching National AI Mission with ₹10,000 Cr budget",
                    f"Found: TCS, Infosys, Wipro deploying agents for enterprise automation",
                ],
            }
        elif action_type == "analyze":
            result = {
                "status": "success",
                "output": [
                    "Insight 1: India is 3rd largest AI talent pool globally",
                    "Insight 2: Regional language AI agents are fastest-growing segment",
                    "Insight 3: Enterprise adoption outpacing consumer adoption 5:1",
                ],
            }
        elif action_type == "write":
            result = {
                "status": "success",
                "output": [
                    f"# Research Report: {self.goal}",
                    f"## Key Findings",
                    f"- India's AI agent market growing 340% year-over-year",
                    f"- Hyderabad is India's emerging AI capital (200+ startups)",
                    f"- Government committed ₹10,000 Cr to National AI Mission",
                    f"## Recommendation",
                    f"- Focus on regional language agents for maximum impact",
                ],
            }
        elif action_type == "review":
            result = {
                "status": "success",
                "output": ["✅ Report quality: GOOD", "✅ Coverage: COMPREHENSIVE", "✅ Actionable: YES"],
            }
        else:
            result = {"status": "complete", "output": ["Goal achieved!"]}

        self.completed_tasks.append(f"{action_type}: {target}")
        return result

    def observe(self, result: dict) -> str:
        """OBSERVE: Evaluate results and update memory."""
        observation = f"Iteration {self.iteration}: {result['status']} — {len(result.get('output', []))} items"
        self.memory.append(observation)
        return observation

    def run(self):
        """Run the autonomous agent loop."""
        print(f"\n{'═' * 65}")
        print(f"  #2 · AutoGPT — Autonomous Agent Demo")
        print(f"  ⭐ ~185,000 GitHub Stars | The Agent That Started It All")
        print(f"{'═' * 65}")
        print(f"  AutoGPT pioneered the Goal → Think → Act → Observe loop.")
        print(f"  Watch as the agent autonomously researches a topic.\n")
        print(f"  🎯 GOAL: {self.goal}")
        print(f"  🤖 AGENT: {self.name}")
        print(f"  🔄 MAX ITERATIONS: {self.max_iterations}\n")

        while self.iteration < self.max_iterations:
            print(f"{'─' * 55}")
            print(f"  ⟳ ITERATION {self.iteration + 1}/{self.max_iterations}")
            print(f"{'─' * 55}")

            # THINK
            action = self.think()
            print(f"  💭 THINK: {action['thought']}")
            print(f"  📋 ACTION: {action['action'].upper()} → {action['target']}")

            # ACT
            result = self.act(action)
            print(f"  ⚡ RESULT: {result['status']}")
            for item in result.get("output", []):
                print(f"     {item}")

            # OBSERVE
            obs = self.observe(result)
            print(f"  👁 OBSERVE: {obs}")

            if action["action"] == "complete":
                break

            time.sleep(0.3)  # Simulate processing time

        # Final summary
        print(f"\n{'═' * 65}")
        print(f"  ✅ AUTONOMOUS AGENT COMPLETE")
        print(f"{'═' * 65}")
        print(f"  Iterations: {self.iteration}")
        print(f"  Tasks completed: {len(self.completed_tasks)}")
        for i, task in enumerate(self.completed_tasks, 1):
            print(f"    {i}. {task}")
        print(f"  Memory entries: {len(self.memory)}")
        print(f"\n  💡 STUDENT TAKEAWAY: AutoGPT's genius is the autonomous loop.")
        print(f"     The agent THINKS about what to do, ACTS on its decision,")
        print(f"     OBSERVES the result, and loops — no human needed.\n")


def main():
    agent = AutonomousAgent(
        name="ResearchBot-v1",
        goal="Analyze the growth of AI agents in India's tech ecosystem",
    )
    agent.run()


if __name__ == "__main__":
    main()
