"""
CROID AI Agent Orchestrator

Chains the six specialized agents in logical workflows:

  FULL_PIPELINE  → OrderSearch → ApplicationProcessor → CostOptimizer
                 → ProposalGenerator → RevenueOptimizer

  NEW_LEAD       → OrderSearch

  PROCESS_APP    → ApplicationProcessor → CostOptimizer → ProposalGenerator

  RETAIN_CLIENTS → ClientRetention → RevenueOptimizer

  REVENUE_AUDIT  → RevenueOptimizer
"""
import json
from dataclasses import dataclass, field
from typing import Callable

import anthropic

import config
from agents import (
    ApplicationProcessorAgent,
    ClientRetentionAgent,
    CostOptimizerAgent,
    OrderSearchAgent,
    ProposalGeneratorAgent,
    RevenueOptimizerAgent,
)
from utils.display import (
    console,
    print_agent_header,
    print_agent_result,
    print_error,
    print_info,
    print_section,
    print_success,
)


@dataclass
class WorkflowResult:
    workflow: str
    steps: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def add_step(self, agent_name: str, result: dict) -> None:
        self.steps.append({"agent": agent_name, "result": result})

    @property
    def last(self) -> dict:
        return self.steps[-1]["result"] if self.steps else {}

    def to_summary(self) -> dict:
        """Return a flat summary of all agent outputs."""
        summary: dict = {"workflow": self.workflow}
        for step in self.steps:
            summary[step["agent"]] = step["result"]
        return summary


class Orchestrator:
    """
    Central orchestrator that runs agent workflows for CROID.

    Usage:
        orch = Orchestrator()
        result = orch.run("process_app", context={...})
    """

    WORKFLOWS = {
        "full_pipeline": "Полный pipeline: поиск → обработка → стоимость → КП → выручка",
        "new_lead": "Поиск и квалификация новых лидов",
        "process_app": "Обработка заявки → расчёт стоимости → КП",
        "retain_clients": "Анализ оттока и стратегия возврата клиентов",
        "revenue_audit": "Аудит выручки и рекомендации по росту",
    }

    def __init__(self) -> None:
        import os
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY не задан. Создайте .env файл из .env.example")

        self.client = anthropic.Anthropic()
        self._agents = {
            "order_search": OrderSearchAgent(self.client),
            "app_processor": ApplicationProcessorAgent(self.client),
            "cost_optimizer": CostOptimizerAgent(self.client),
            "proposal": ProposalGeneratorAgent(self.client),
            "retention": ClientRetentionAgent(self.client),
            "revenue": RevenueOptimizerAgent(self.client),
        }

    # ── Workflow runners ──────────────────────────────────────────────────

    def run(self, workflow: str, context: dict) -> WorkflowResult:
        """Execute a named workflow with the given context."""
        handlers: dict[str, Callable[[dict, WorkflowResult], None]] = {
            "full_pipeline": self._run_full_pipeline,
            "new_lead": self._run_new_lead,
            "process_app": self._run_process_app,
            "retain_clients": self._run_retain_clients,
            "revenue_audit": self._run_revenue_audit,
        }
        if workflow not in handlers:
            raise ValueError(f"Неизвестный workflow: {workflow}")

        result = WorkflowResult(workflow=workflow)
        print_info(f"\n⚙ Запуск workflow: {self.WORKFLOWS[workflow]}\n")

        try:
            handlers[workflow](context, result)
        except KeyboardInterrupt:
            print_error("Прервано пользователем")
        except anthropic.APIError as e:
            msg = f"Ошибка API Anthropic: {e}"
            print_error(msg)
            result.errors.append(msg)

        return result

    def _run_step(
        self,
        agent_key: str,
        context: dict,
        workflow_result: WorkflowResult,
    ) -> dict:
        agent = self._agents[agent_key]
        print_agent_header(agent.name)
        step_result = agent.run(context)
        workflow_result.add_step(agent_key, step_result)
        print()  # newline after streaming
        return step_result

    # ── Individual workflows ──────────────────────────────────────────────

    def _run_full_pipeline(self, context: dict, result: WorkflowResult) -> None:
        # 1. Find leads
        search_ctx = {k: v for k, v in context.items()}
        search_result = self._run_step("order_search", search_ctx, result)

        # 2. Process the top lead as an application
        top_lead = (search_result.get("leads") or [{}])[0]
        app_ctx = {**context, "top_lead": top_lead}
        app_result = self._run_step("app_processor", app_ctx, result)

        # 3. Calculate cost based on requirements
        cost_ctx = {
            **context,
            "requirements": app_result.get("requirements", {}),
            "application_status": app_result.get("status", {}),
        }
        cost_result = self._run_step("cost_optimizer", cost_ctx, result)

        # 4. Generate proposal
        proposal_ctx = {
            **context,
            "client_name": app_result.get("client_name", ""),
            "requirements": app_result.get("requirements", {}),
            "pricing": cost_result.get("pricing", {}),
            "cost_items": cost_result.get("cost_items", []),
        }
        self._run_step("proposal", proposal_ctx, result)

        # 5. Revenue audit on the full picture
        revenue_ctx = {
            **context,
            "search_summary": search_result.get("summary", {}),
            "leads": search_result.get("leads", []),
            "current_project": app_result.get("requirements", {}),
            "pricing": cost_result.get("pricing", {}),
        }
        self._run_step("revenue", revenue_ctx, result)

    def _run_new_lead(self, context: dict, result: WorkflowResult) -> None:
        self._run_step("order_search", context, result)

    def _run_process_app(self, context: dict, result: WorkflowResult) -> None:
        app_result = self._run_step("app_processor", context, result)

        cost_ctx = {
            **context,
            "requirements": app_result.get("requirements", {}),
            "application_status": app_result.get("status", {}),
        }
        cost_result = self._run_step("cost_optimizer", cost_ctx, result)

        proposal_ctx = {
            **context,
            "client_name": app_result.get("client_name", ""),
            "requirements": app_result.get("requirements", {}),
            "pricing": cost_result.get("pricing", {}),
            "cost_items": cost_result.get("cost_items", []),
        }
        self._run_step("proposal", proposal_ctx, result)

    def _run_retain_clients(self, context: dict, result: WorkflowResult) -> None:
        retention_result = self._run_step("retention", context, result)

        revenue_ctx = {
            **context,
            "client_analyses": retention_result.get("client_analyses", []),
            "retention_actions": retention_result.get("retention_actions", []),
        }
        self._run_step("revenue", revenue_ctx, result)

    def _run_revenue_audit(self, context: dict, result: WorkflowResult) -> None:
        self._run_step("revenue", context, result)

    # ── Formatting helpers ────────────────────────────────────────────────

    def format_report(self, result: WorkflowResult) -> str:
        """Format a WorkflowResult into a readable text report."""
        lines = [
            f"# Отчёт {config.COMPANY_NAME} — {self.WORKFLOWS.get(result.workflow, result.workflow)}",
            "",
        ]
        for step in result.steps:
            agent_name = self._agents[step["agent"]].name
            lines.append(f"## {agent_name}")
            lines.append("```json")
            lines.append(json.dumps(step["result"], ensure_ascii=False, indent=2))
            lines.append("```")
            lines.append("")
        return "\n".join(lines)
