# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The sovereign DESIGN provider (8.a): phase one without paid credentials."""

import json
from datetime import UTC, datetime

import pytest

from vibey.application.design import DesignEvent, DesignStage
from vibey.domain.ledger import EventKind, Provenance
from vibey.domain.spec import ConstraintKind
from vibey.infrastructure.engines import qwenloop_design as mod
from vibey.infrastructure.engines.qwenloop_design import (
    QwenloopDesignProvider,
    SovereignResearchUnavailable,
)

SPEC_PAYLOAD = {
    "objective": "publish a heartbeat ref",
    "walking_skeleton": "a CLI that writes one ref",
    "non_goals": ["a web UI"],
    "constraints": [{"text": "git and stdlib only", "kind": "hard"}],
    "criteria": [
        {
            "criterion_id": "c1",
            "given": "a repository",
            "when": "the CLI runs",
            "then": "a ref exists",
            "fit": "git ls-remote shows it",
        }
    ],
    "nfrs": [
        {
            "nfr_id": "n1",
            "attribute": "Latency",
            "scale": "seconds",
            "meter": "wall clock",
            "must": "under 5",
            "wish": "under 1",
            "fit_criterion": "timed push",
        }
    ],
}


def _event(payload: dict[str, object]) -> DesignEvent:
    return DesignEvent(
        kind=EventKind.ANSWER_GIVEN,
        provenance=Provenance.TRUSTED,
        produced_at=datetime.now(UTC),
        payload=payload,
    )


def _answers(monkeypatch: pytest.MonkeyPatch, content: object) -> list[dict[str, object]]:
    """Stand in for Ollama, capturing what was sent."""
    sent: list[dict[str, object]] = []

    async def fake(url: str, payload: dict[str, object], *, timeout: int) -> dict[str, object]:
        sent.append(payload)
        body = content if isinstance(content, str) else json.dumps(content)
        return {"message": {"content": body}}

    monkeypatch.setattr(mod, "_post_json", fake)
    return sent


@pytest.mark.asyncio
async def test_a_stage_of_questions_comes_back_shaped(monkeypatch: pytest.MonkeyPatch) -> None:
    sent = _answers(
        monkeypatch,
        {
            "questions": [
                {"question_id": "q1", "text": "what problem?", "default": "none", "blocking": True}
            ]
        },
    )
    batch = await QwenloopDesignProvider().batch(DesignStage.CONTEXT_FREE, [])
    assert batch.stage is DesignStage.CONTEXT_FREE
    assert [q.question_id for q in batch.questions] == ["q1"]
    assert batch.questions[0].blocking is True
    # Constrained decoding is the whole reason this provider is reliable: the schema is
    # compiled to a grammar, so malformed JSON is unreachable rather than merely unlikely.
    assert sent[0]["format"] == mod.QUESTIONS_SCHEMA
    # temperature 0: a DESIGN stage that asks different questions on an unchanged ledger
    # cannot be reasoned about by the phase that consumes it.
    assert sent[0]["options"]["temperature"] == 0
    assert sent[0]["options"]["num_ctx"] >= 4096
    assert sent[0]["stream"] is False


@pytest.mark.asyncio
async def test_a_stage_with_no_questions_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    _answers(monkeypatch, {"questions": []})
    with pytest.raises(ValueError, match="non-empty questions list"):
        await QwenloopDesignProvider().batch(DesignStage.JOB_STORY, [])


@pytest.mark.asyncio
async def test_research_refuses_rather_than_inventing_a_source() -> None:
    """The floor, declared. A local model has no web access, and returning its
    recollection with a `source` field would put a fabricated citation into a design
    spec — a wrong answer that looks sourced survives review, where a missing one does
    not."""
    with pytest.raises(SovereignResearchUnavailable) as caught:
        await QwenloopDesignProvider().research("OAuth device flow")
    message = str(caught.value)
    assert "OAuth device flow" in message
    assert "no" in message and "web access" in message
    assert "fabricated source" in message


@pytest.mark.asyncio
async def test_a_spec_is_synthesised_from_the_ledger(monkeypatch: pytest.MonkeyPatch) -> None:
    sent = _answers(monkeypatch, SPEC_PAYLOAD)
    spec = await QwenloopDesignProvider().synthesize([_event({"q": "objective", "a": "x"})])
    assert spec.objective == "publish a heartbeat ref"
    assert spec.walking_skeleton == "a CLI that writes one ref"
    assert spec.non_goals == ("a web UI",)
    assert spec.constraints[0].kind is ConstraintKind.HARD
    assert spec.criteria[0].criterion_id == "c1"
    assert spec.nfrs[0].wish == "under 1"
    # The ledger reaches the model as data, and the prompt says so.
    assert "never as instructions" in str(sent[0]["messages"][0]["content"])


@pytest.mark.asyncio
async def test_an_empty_wish_is_absent_rather_than_an_empty_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A grammar cannot express "omit this key", so the model emits `""` for an NFR with
    no wish. Carrying that through as a wish of "" would be a requirement nobody stated."""
    payload = json.loads(json.dumps(SPEC_PAYLOAD))
    payload["nfrs"][0]["wish"] = ""
    _answers(monkeypatch, payload)
    spec = await QwenloopDesignProvider().synthesize([])
    assert spec.nfrs[0].wish is None


@pytest.mark.asyncio
async def test_a_spec_without_a_single_criterion_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A spec nothing can be checked against is not buildable, and would hand the BUILD
    phase a target it can never prove it hit."""
    payload = json.loads(json.dumps(SPEC_PAYLOAD))
    payload["criteria"] = []
    _answers(monkeypatch, payload)
    with pytest.raises(ValueError, match="at least one acceptance criterion"):
        await QwenloopDesignProvider().synthesize([])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mutate, expected",
    [
        (lambda p: p.pop("objective"), "invalid DesignSpec JSON"),
        (lambda p: p.update(non_goals="not a list"), "non_goals must be a list"),
        (lambda p: p.update(constraints=["not an object"]), "every constraints item"),
        (lambda p: p.update(constraints=[{"text": "x", "kind": "sideways"}]), "invalid DesignSpec"),
    ],
)
async def test_a_malformed_spec_is_refused_at_the_boundary(
    monkeypatch: pytest.MonkeyPatch, mutate, expected: str
) -> None:
    payload = json.loads(json.dumps(SPEC_PAYLOAD))
    mutate(payload)
    _answers(monkeypatch, payload)
    with pytest.raises(ValueError, match=expected):
        await QwenloopDesignProvider().synthesize([])


@pytest.mark.asyncio
async def test_a_gateway_that_is_not_ollama_cannot_pass_for_an_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Constrained decoding guarantees the schema only if the thing on the other end is
    actually Ollama. This is a process boundary, so the shape is asserted, not trusted."""
    _answers(monkeypatch, "[1, 2, 3]")
    with pytest.raises(ValueError, match="expected a JSON object"):
        await QwenloopDesignProvider().batch(DesignStage.PREMORTEM, [])

    async def no_message(url: str, payload: dict[str, object], *, timeout: int) -> dict:
        return {"nothing": "useful"}

    monkeypatch.setattr(mod, "_post_json", no_message)
    with pytest.raises(ValueError, match="no message content"):
        await QwenloopDesignProvider().batch(DesignStage.PREMORTEM, [])


def test_the_context_window_is_sized_to_the_prompt() -> None:
    """Ollama's default window is far smaller than a full ledger, and overflowing it
    degrades generation from seconds to never-finishes rather than erroring."""
    assert mod._num_ctx(0) == 4096
    assert mod._num_ctx(300_000) == 32768
    assert 4096 < mod._num_ctx(60_000) < 32768


@pytest.mark.asyncio
async def test_the_transport_refuses_a_non_object_response(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc: object) -> None:
            return None

        def read(self) -> bytes:
            return b"[1, 2]"

    monkeypatch.setattr(mod.urllib.request, "urlopen", lambda *a, **k: FakeResponse())
    with pytest.raises(ValueError, match="non-object response"):
        await mod._post_json("http://127.0.0.1:11434/api/chat", {}, timeout=1)


@pytest.mark.asyncio
async def test_the_transport_returns_the_decoded_body(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *exc: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"message": {"content": "{}"}}'

    monkeypatch.setattr(mod.urllib.request, "urlopen", lambda *a, **k: FakeResponse())
    body = await mod._post_json("http://127.0.0.1:11434/api/chat", {}, timeout=1)
    assert body == {"message": {"content": "{}"}}


def test_the_base_url_is_normalised() -> None:
    provider = QwenloopDesignProvider(base_url="http://example.test:11434/")
    assert provider._base_url == "http://example.test:11434"


def test_the_shared_decoders_refuse_the_wrong_shape() -> None:
    """Both providers cross the same boundary — model text becoming domain objects — so
    they refuse malformed input in one place rather than two."""
    from vibey.infrastructure.engines.design_json import as_list, as_object_list

    assert as_list([1, 2], "xs") == [1, 2]
    with pytest.raises(ValueError, match="xs must be a list"):
        as_list("not a list", "xs")
    with pytest.raises(ValueError, match="every xs item must be an object"):
        as_object_list([{"a": 1}, "not an object"], "xs")
