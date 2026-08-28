# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Phase 1 DESIGN protocol primitives.

The application owns interactive turn-taking. Engines may propose the question
wording, but this module enforces the seven-stage order, bounded batches,
defaults, ledger lifecycle, untrusted research provenance, and the independent
synthesizer constraint.
"""

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from vibey.domain.effort import Effort
from vibey.domain.engine import EngineId, JobRequirement
from vibey.domain.ledger import EventKind, Provenance


class DesignStage(StrEnum):
    CONTEXT_FREE = "context_free"
    JOB_STORY = "job_story"
    LADDERING = "laddering"
    EXAMPLE_MAPPING = "example_mapping"
    WALKING_SKELETON = "walking_skeleton"
    NFR_PLANGUAGE = "nfr_planguage"
    PREMORTEM = "premortem"


DESIGN_STAGES = tuple(DesignStage)

REENTRANT_DESIGN_STAGES: tuple[DesignStage, ...] = (
    DesignStage.EXAMPLE_MAPPING,
    DesignStage.WALKING_SKELETON,
    DesignStage.NFR_PLANGUAGE,
    DesignStage.PREMORTEM,
)


def stages_for_cycle(cycle: int) -> tuple[DesignStage, ...]:
    """Cycle 1 runs the full 7-stage elicitation. Cycle > 1 is a re-entrant
    design scoped to specific findings driving loop-back (<= 5 question batches)."""
    if cycle <= 1:
        return DESIGN_STAGES
    return REENTRANT_DESIGN_STAGES


@dataclass(frozen=True, slots=True)
class DesignQuestion:
    question_id: str
    text: str
    default: str
    blocking: bool


@dataclass(frozen=True, slots=True)
class DesignEvent:
    kind: EventKind
    provenance: Provenance
    produced_at: datetime
    payload: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class QuestionBatch:
    stage: DesignStage
    questions: tuple[DesignQuestion, ...]

    def events(self, *, now: datetime, cycle: int = 1) -> tuple[DesignEvent, ...]:
        return tuple(
            DesignEvent(
                kind=EventKind.QUESTION_ASKED,
                provenance=Provenance.AGENT,
                produced_at=now,
                payload={
                    "item_id": question.question_id,
                    "text": question.text,
                    "default": question.default,
                    "blocking": question.blocking,
                    "stage": self.stage.value,
                    "cycle": cycle,
                },
            )
            for question in self.questions
        )


def build_question_batch(
    stage: DesignStage, questions: tuple[DesignQuestion, ...]
) -> QuestionBatch:
    if len(questions) > 4:
        raise ValueError("a design turn may ask at most 4 questions")
    if any(not question.default.strip() for question in questions):
        raise ValueError("every design question requires a proposed default")
    return QuestionBatch(stage=stage, questions=questions)


@dataclass(frozen=True, slots=True)
class InterviewSession:
    stage_index: int

    @classmethod
    def start(cls) -> "InterviewSession":
        return cls(stage_index=0)

    @property
    def complete(self) -> bool:
        return self.stage_index == len(DESIGN_STAGES)

    @property
    def stage(self) -> DesignStage:
        if self.complete:
            raise ValueError("the interview is complete")
        return DESIGN_STAGES[self.stage_index]

    def advance(self) -> "InterviewSession":
        if self.complete:
            raise ValueError("the interview is complete")
        return InterviewSession(stage_index=self.stage_index + 1)


def answer_questions(
    questions: Sequence[DesignQuestion], answers: Mapping[str, str], *, now: datetime
) -> tuple[DesignEvent, ...]:
    known = {question.question_id for question in questions}
    return tuple(
        DesignEvent(
            kind=EventKind.ANSWER_GIVEN,
            provenance=Provenance.TRUSTED,
            produced_at=now,
            payload={"item_id": question_id, "answer": answer},
        )
        for question_id, answer in answers.items()
        if question_id in known
    )


def finalize_questions(
    questions: Sequence[DesignQuestion], *, answered_ids: frozenset[str], now: datetime
) -> tuple[DesignEvent, ...]:
    unanswered = tuple(q for q in questions if q.question_id not in answered_ids)
    if any(question.blocking for question in unanswered):
        raise ValueError("an unanswered blocking question cannot become an assumption")
    return tuple(
        DesignEvent(
            kind=EventKind.ASSUMPTION_STATED,
            provenance=Provenance.TRUSTED,
            produced_at=now,
            payload={
                "item_id": question.question_id,
                "text": question.default,
                "question": question.text,
            },
        )
        for question in unanswered
    )


@dataclass(frozen=True, slots=True)
class ResearchResult:
    title: str
    source: str
    content: str


def research_event(result: ResearchResult, *, now: datetime) -> DesignEvent:
    return DesignEvent(
        kind=EventKind.ARTIFACT_PRODUCED,
        provenance=Provenance.UNTRUSTED,
        produced_at=now,
        payload={"title": result.title, "source": result.source, "content": result.content},
    )


def synthesizer_requirement(interviewers: Sequence[EngineId]) -> JobRequirement:
    if not interviewers:
        raise ValueError("at least one interviewer is required")
    counts = Counter(interviewers)
    majority = max(interviewers, key=lambda engine: counts[engine])
    return JobRequirement(effort=Effort.HIGH, excluded=frozenset({majority}))
