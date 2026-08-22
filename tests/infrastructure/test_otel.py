# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from datetime import timedelta
from uuid import uuid4

import pytest

from vibey.domain.effort import Effort
from vibey.domain.engine import EngineId
from vibey.domain.phase import Phase
from vibey.infrastructure.otel import (
    TelemetryMetrics,
    TelemetryTracer,
    calculate_rotation_fairness,
)


def test_span_recording_and_attributes() -> None:
    tracer = TelemetryTracer()
    project_id = uuid4()

    with tracer.trace_job(
        project_id=project_id,
        cycle=1,
        phase=Phase.BUILD,
        job_kind="build.implement",
        engine_id=EngineId.CLAUDELOOP,
        effort=Effort.LOW,
    ) as span:
        assert span.attributes["project_id"] == str(project_id)
        assert span.attributes["phase"] == "build"
        assert span.attributes["cycle"] == 1
        assert span.attributes["job_kind"] == "build.implement"
        assert span.attributes["engine_id"] == "claudeloop"
        assert span.attributes["effort"] == "low"

        with tracer.trace_turn(engine_id=EngineId.CLAUDELOOP, turn_number=1) as child:
            assert child.parent_id == span.span_id
            assert child.attributes["turn_number"] == 1

    spans = tracer.get_finished_spans()
    assert len(spans) == 2
    assert spans[0].name == "turn"
    assert spans[1].name == "job:build.implement"
    assert spans[1].duration >= timedelta(0)


def test_telemetry_metrics_recording() -> None:
    metrics = TelemetryMetrics()
    project_id = uuid4()

    # Record rotation selections
    metrics.record_engine_selection(project_id, EngineId.CLAUDELOOP)
    metrics.record_engine_selection(project_id, EngineId.CLAUDELOOP)
    metrics.record_engine_selection(project_id, EngineId.CODEXLOOP)

    # Record queue latency and phase duration
    metrics.record_queue_latency(project_id, Phase.BUILD, "build.implement", 0.45)
    metrics.record_phase_duration(project_id, 1, Phase.BUILD, 120.0)

    # Record handoff failure and cost
    metrics.record_handoff_gate_failure(project_id, "R2")
    metrics.record_cost_spend(project_id, 1, Phase.BUILD, EngineId.CLAUDELOOP, 0.75)

    exported = metrics.export_metrics(project_id)
    assert exported["engine_selections"]["claudeloop"] == 2
    assert exported["engine_selections"]["codexloop"] == 1
    assert exported["queue_latencies"]["build.implement"] == [0.45]
    assert exported["phase_durations"]["build"] == [120.0]
    assert exported["handoff_gate_failures"]["R2"] == 1
    assert exported["cost_spend"]["claudeloop"] == 0.75


def test_rotation_fairness_calculation() -> None:
    # Equal weights and equal distribution -> perfect fairness (1.0)
    selections = {"claudeloop": 10, "codexloop": 10}
    weights = {"claudeloop": 1, "codexloop": 1}
    fairness = calculate_rotation_fairness(selections, weights)
    assert pytest.approx(fairness, 0.01) == 1.0

    # Skewed selections -> lower fairness
    skewed = {"claudeloop": 18, "codexloop": 2}
    skewed_fairness = calculate_rotation_fairness(skewed, weights)
    assert skewed_fairness < 0.7

    # Empty selections -> 1.0
    assert calculate_rotation_fairness({}, {}) == 1.0
    assert calculate_rotation_fairness({"a": 0, "b": 0}, {"a": 1, "b": 1}) == 1.0


def test_trace_handoff_and_error_span() -> None:
    tracer = TelemetryTracer()

    with tracer.trace_handoff(
        from_engine=EngineId.CLAUDELOOP,
        to_engine=EngineId.CODEXLOOP,
        reason="capacity_exhausted",
    ) as span:
        span.set_attribute("custom_k", "custom_v")
        span.add_event("brief_generated", {"mode": "strict"})
        assert span.attributes["from_engine"] == "claudeloop"
        assert span.attributes["to_engine"] == "codexloop"
        assert len(span.events) == 1

    spans = tracer.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status == "OK"

    # Test error handling
    with pytest.raises(ValueError, match="boom"), tracer.start_span("failing_span"):
        raise ValueError("boom")

    err_spans = tracer.get_finished_spans()
    assert len(err_spans) == 2
    assert err_spans[1].status == "ERROR"
    assert err_spans[1].attributes["error.type"] == "ValueError"

    tracer.clear()
    assert len(tracer.get_finished_spans()) == 0


def test_span_duration_on_open_span() -> None:
    tracer = TelemetryTracer()
    with tracer.start_span("open") as span:
        dur = span.duration
        assert dur >= timedelta(0)
        assert span.end_time is None


def test_trace_job_with_none_engine_and_effort() -> None:
    tracer = TelemetryTracer()
    with tracer.trace_job(
        project_id=uuid4(),
        cycle=1,
        phase=Phase.BUILD,
        job_kind="build.plan",
        engine_id=None,
        effort=None,
    ) as span:
        assert "engine_id" not in span.attributes
        assert "effort" not in span.attributes


def test_trace_job_with_string_engine_and_effort() -> None:
    tracer = TelemetryTracer()
    with tracer.trace_job(
        project_id=uuid4(),
        cycle=1,
        phase=Phase.BUILD,
        job_kind="build.plan",
        engine_id="custom-engine",
        effort="HIGH",
    ) as span:
        assert span.attributes["engine_id"] == "custom-engine"
        assert span.attributes["effort"] == "high"


def test_trace_turn_with_none_engine_and_turn_number() -> None:
    tracer = TelemetryTracer()
    with tracer.trace_turn(engine_id=None, turn_number=None) as span:
        assert "engine_id" not in span.attributes
        assert "turn_number" not in span.attributes


def test_trace_turn_with_string_engine() -> None:
    tracer = TelemetryTracer()
    with tracer.trace_turn(engine_id="str-engine", turn_number=3) as span:
        assert span.attributes["engine_id"] == "str-engine"


def test_trace_handoff_with_none_engines() -> None:
    tracer = TelemetryTracer()
    with tracer.trace_handoff(from_engine=None, to_engine=None, reason="test") as span:
        assert "from_engine" not in span.attributes
        assert "to_engine" not in span.attributes
        assert span.attributes["reason"] == "test"


def test_trace_handoff_with_string_engines() -> None:
    tracer = TelemetryTracer()
    with tracer.trace_handoff(from_engine="e1", to_engine="e2") as span:
        assert span.attributes["from_engine"] == "e1"
        assert span.attributes["to_engine"] == "e2"


def test_rotation_fairness_with_zero_weight() -> None:
    result = calculate_rotation_fairness({"a": 5}, {"a": 0})
    assert result == pytest.approx(1.0)


def test_rotation_fairness_with_negative_weight() -> None:
    result = calculate_rotation_fairness({"a": 5}, {"a": -1})
    assert result == pytest.approx(1.0)
