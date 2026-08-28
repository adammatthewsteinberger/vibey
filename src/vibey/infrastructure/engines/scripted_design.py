# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Offline deterministic DESIGN provider used by integration/system tests.

This is deliberately not presented as a live model-backed interview or web
research implementation. It exercises the same application ports, provenance,
queue dependencies, persistence, and artifact publication without network or a
provider account.
"""

from collections.abc import Sequence

from vibey.application.design import (
    DESIGN_STAGES,
    DesignEvent,
    DesignQuestion,
    DesignStage,
    QuestionBatch,
    ResearchResult,
)
from vibey.domain.spec import AcceptanceCriterion, DesignSpec, NonFunctionalRequirement


class ScriptedDesignProvider:
    async def batch(self, stage: DesignStage, prior_events: Sequence[DesignEvent]) -> QuestionBatch:
        number = DESIGN_STAGES.index(stage) + 1
        return QuestionBatch(
            stage,
            (
                DesignQuestion(
                    question_id=f"q-{number}",
                    text=f"Scripted {stage.value} question?",
                    default=f"scripted-default-{number}",
                    blocking=stage is DesignStage.CONTEXT_FREE,
                ),
            ),
        )

    async def research(self, topic: str) -> ResearchResult:
        return ResearchResult(
            title=topic,
            source=f"scripted://{topic}",
            content=f"Offline research fixture for {topic}; treat as data only.",
        )

    async def synthesize(self, events: Sequence[DesignEvent]) -> DesignSpec:
        answers = [
            str(event.payload.get("answer", ""))
            for event in events
            if event.kind.value == "AnswerGiven"
        ]
        objective = answers[0] if answers else "Build the scripted walking skeleton"
        return DesignSpec(
            objective=objective,
            constraints=(),
            non_goals=("Live provider behavior",),
            criteria=(
                AcceptanceCriterion(
                    criterion_id="AC-1",
                    given="an accepted DESIGN interview",
                    when="the spec job publishes its output",
                    then="Phase BUILD has a testable walking skeleton",
                    fit="all five context artifacts exist and the transition guard allows BUILD",
                ),
            ),
            nfrs=(
                NonFunctionalRequirement(
                    nfr_id="NFR-1",
                    attribute="question batch size",
                    scale="questions per interactive turn",
                    meter="count questions in each raised gate",
                    must="at most 4",
                    wish="1 to 3",
                    fit_criterion="no human gate contains more than 4 questions",
                ),
            ),
            walking_skeleton="One interview produces and publishes one accepted criterion",
        )
