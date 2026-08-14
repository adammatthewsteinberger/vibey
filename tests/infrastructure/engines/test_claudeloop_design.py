import json
from pathlib import Path

import pytest

from vibey.application.design import DesignStage
from vibey.infrastructure.engines.claudeloop_design import ClaudeLoopDesignProvider
from vibey.infrastructure.engines.claudeloop_process import ClaudeLoopResult


class FakeProcess:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls = []

    async def run(self, spec, *, web_search=False):  # type: ignore[no-untyped-def]
        self.calls.append((spec, web_search))
        return ClaudeLoopResult(
            "run-1",
            spec.worktree_path / ".claudeloop/runs/run-1",
            self.responses.pop(0),
        )


async def test_provider_adapts_all_three_design_ports_with_strict_structures(
    tmp_path: Path,
) -> None:
    process = FakeProcess(
        [
            '```json\n{"questions":[{"question_id":"q-1","text":"What outcome?",'
            '"default":"Ship one path","blocking":true}]}\n```\n\n'
            "CLAUDELOOP_TASK_FULLY_COMPLETE",
            '{"title":"Prior art","source":"https://example.test/doc","content":"Evidence"}',
            json.dumps(
                {
                    "objective": "Ship",
                    "constraints": [{"text": "Offline", "kind": "hard"}],
                    "non_goals": ["Cloud"],
                    "criteria": [
                        {
                            "criterion_id": "AC-1",
                            "given": "a plan",
                            "when": "it runs",
                            "then": "one path works",
                            "fit": "integration test passes",
                        }
                    ],
                    "nfrs": [
                        {
                            "nfr_id": "NFR-1",
                            "attribute": "latency",
                            "scale": "seconds",
                            "meter": "monotonic timer",
                            "must": "under 2",
                            "wish": "under 1",
                            "fit_criterion": "p95 under 2 seconds",
                        }
                    ],
                    "walking_skeleton": "one path",
                }
            ),
        ]
    )
    provider = ClaudeLoopDesignProvider(process=process, worktree_path=tmp_path)

    batch = await provider.batch(DesignStage.CONTEXT_FREE, ())
    research = await provider.research("prior-art")
    design = await provider.synthesize(())

    assert batch.questions[0].question_id == "q-1"
    assert research.source == "https://example.test/doc"
    assert design.is_buildable() == ()
    assert [web for _, web in process.calls] == [False, True, False]
    assert [call.effort.name for call, _ in process.calls] == ["LOW", "STANDARD", "HIGH"]
    assert all("Return only JSON" in call.prompt for call, _ in process.calls)
    assert "Do not inspect files or call tools" in process.calls[0][0].prompt
    assert "Do not inspect repository files" in process.calls[1][0].prompt
    assert "Use web search immediately" in process.calls[1][0].prompt
    assert "Do not narrate your plan" in process.calls[1][0].prompt


@pytest.mark.parametrize(
    "response",
    [
        "not json",
        '{"questions":[]}',
        '{"questions":[{"question_id":"q","text":"?","default":"","blocking":false}]}',
    ],
)
async def test_question_provider_rejects_malformed_or_empty_batches(
    tmp_path: Path, response: str
) -> None:
    provider = ClaudeLoopDesignProvider(process=FakeProcess([response]), worktree_path=tmp_path)
    with pytest.raises(ValueError):
        await provider.batch(DesignStage.CONTEXT_FREE, ())


async def test_provider_extracts_fenced_json_after_leading_prose(tmp_path: Path) -> None:
    provider = ClaudeLoopDesignProvider(
        process=FakeProcess(
            [
                "Based on web research:\n```json\n"
                '{"title":"Prior art","source":"https://example.test","content":"Evidence"}'
                "\n```\nCLAUDELOOP_TASK_FULLY_COMPLETE"
            ]
        ),
        worktree_path=tmp_path,
    )

    result = await provider.research("prior-art")

    assert result.title == "Prior art"
