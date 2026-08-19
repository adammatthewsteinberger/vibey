"""Application interfaces -- every seam implemented by infrastructure/ and
never imported from it.

One module per collaborator family, plus the DTOs that are part of a seam's
vocabulary. Nine structurally identical `*Ledger` Protocols collapsed into
`PhaseLedger`, five identical `ProjectTransitioner`s and four `ProjectStore`s
into one each, and two spec readers into `DesignSpecReader`: they were the
same seam re-declared beside every handler that needed it.
"""

from __future__ import annotations

from vibey.application.interfaces.azure import (
    AzureClientPort,
    AzureDiscoveryResult,
    AzureExecutionResult,
    AzureResourceStatus,
    DeploymentConsentStore,
    DeploymentSpecStore,
)
from vibey.application.interfaces.build import (
    BudgetSource,
    BuildProvisioner,
    BuildWorktrees,
    GateResult,
    GateRunner,
    IntegrationBranch,
    MergeOutcome,
    VerifyWorktrees,
    WorkPlanProducer,
)
from vibey.application.interfaces.design import (
    DesignProvider,
    DesignQuestionProvider,
    DesignSpecReader,
    DesignSpecRepository,
    ResearchProvider,
    SpecSynthesizer,
)
from vibey.application.interfaces.engines import (
    EngineAdapter,
    EngineHealthRepository,
    RotationCursorRepository,
)
from vibey.application.interfaces.gates import (
    HumanGateRepository,
)
from vibey.application.interfaces.ledger import (
    BriefProducer,
    BuildLedger,
    DesignLedger,
    HandoffStore,
    LedgerReader,
    PhaseLedger,
)
from vibey.application.interfaces.observability import (
    Logger,
)
from vibey.application.interfaces.projects import (
    ProjectStore,
    ProjectTransitioner,
)
from vibey.application.interfaces.queue import (
    Defer,
    Failure,
    JobHandler,
    JobHandlerFactory,
    JobReadyNotifier,
    JobRepository,
    Outcome,
    Park,
    Success,
)
from vibey.application.interfaces.review import (
    AutomatedFinding,
    AutomatedReviewRunner,
    ReviewArtifactWriter,
)
from vibey.application.interfaces.system import (
    Clock,
)
from vibey.application.interfaces.visual import (
    VisualInventoryProducer,
    VisualInventoryRepository,
)

__all__ = [
    "Logger",
    "AutomatedFinding",
    "AutomatedReviewRunner",
    "AzureClientPort",
    "DeploymentConsentStore",
    "DeploymentSpecStore",
    "AzureDiscoveryResult",
    "AzureExecutionResult",
    "AzureResourceStatus",
    "BriefProducer",
    "BudgetSource",
    "BuildLedger",
    "BuildProvisioner",
    "BuildWorktrees",
    "Clock",
    "Defer",
    "DesignLedger",
    "DesignProvider",
    "DesignQuestionProvider",
    "DesignSpecReader",
    "DesignSpecRepository",
    "EngineAdapter",
    "EngineHealthRepository",
    "RotationCursorRepository",
    "Failure",
    "GateResult",
    "GateRunner",
    "HandoffStore",
    "HumanGateRepository",
    "IntegrationBranch",
    "JobHandler",
    "JobHandlerFactory",
    "JobReadyNotifier",
    "JobRepository",
    "LedgerReader",
    "MergeOutcome",
    "Outcome",
    "Park",
    "PhaseLedger",
    "ProjectStore",
    "ProjectTransitioner",
    "ResearchProvider",
    "ReviewArtifactWriter",
    "SpecSynthesizer",
    "Success",
    "VerifyWorktrees",
    "VisualInventoryProducer",
    "VisualInventoryRepository",
    "WorkPlanProducer",
]
