"""Shared enumerations for the SIF Sentinel analysis contract.

These are the single source of truth. Frontend types are generated from OpenAPI.
"""

from enum import StrEnum


class CandidateLabel(StrEnum):
    SIF_POTENTIAL = "sif_potential"
    NON_SIF_POTENTIAL = "non_sif_potential"


class Interpretation(StrEnum):
    SERIOUS_EXPOSURE = "serious_exposure"
    CONTROLS_REPORTED = "controls_reported"
    LOW_POTENTIAL = "low_potential"
    INSUFFICIENT_INFORMATION = "insufficient_information"
    ACTUAL_SIF = "actual_sif"


class ProcessingStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"


class ReviewDecision(StrEnum):
    CONFIRMED = "confirmed"
    CORRECTED = "corrected"
    NEEDS_INFORMATION = "needs_information"


class ReviewStatus(StrEnum):
    UNREVIEWED = "unreviewed"
    NEEDS_INFORMATION = "needs_information"
    CONFIRMED = "confirmed"
    CORRECTED = "corrected"
    STALE = "stale"


class HazardKind(StrEnum):
    GRAVITY = "gravity"
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    PRESSURE = "pressure"
    FIRE_EXPLOSION = "fire_explosion"
    TOXIC_ASPHYXIATION = "toxic_asphyxiation"
    VEHICLE = "vehicle"
    OTHER = "other"


class SeriousMechanism(StrEnum):
    SUPPORTED = "supported"
    NOT_SUPPORTED = "not_supported"
    UNKNOWN = "unknown"


class ExposureAssessment(StrEnum):
    EXPLICIT = "explicit"
    SUPPORTED_ROUTE = "supported_route"
    EXPLICITLY_PREVENTED = "explicitly_prevented"
    NOT_ESTABLISHED = "not_established"
    CONFLICTING = "conflicting"


class ControlState(StrEnum):
    EFFECTIVE_REPORTED = "effective_reported"
    PRESENT_UNVERIFIED = "present_unverified"
    ABSENT = "absent"
    FAILED = "failed"
    BYPASSED = "bypassed"
    PLANNED_ONLY = "planned_only"
    UNKNOWN = "unknown"
    CONFLICTING = "conflicting"


class ControlTiming(StrEnum):
    BEFORE_OR_DURING = "before_or_during"
    AFTER_EVENT = "after_event"
    UNSPECIFIED = "unspecified"


class EventState(StrEnum):
    NO_EVENT_REPORTED = "no_event_reported"
    EXPOSURE_ONLY = "exposure_only"
    INCIDENT_REPORTED = "incident_reported"
    CONTROLLED_EVENT = "controlled_event"
    UNKNOWN = "unknown"


class ActualOutcome(StrEnum):
    SERIOUS_REPORTED = "serious_reported"
    OTHER_INJURY = "other_injury"
    NO_INJURY = "no_injury"
    NOT_STATED = "not_stated"


class AvoidanceBasis(StrEnum):
    CONTROL_REPORTED = "control_reported"
    CHANCE_REPORTED = "chance_reported"
    NOT_STATED = "not_stated"
    NO_EVENT_REPORTED = "no_event_reported"


class RuleRelevance(StrEnum):
    RELEVANT = "relevant"
    UNCERTAIN = "uncertain"


class RuleControlIssue(StrEnum):
    SUPPORTED = "supported"
    NOT_ESTABLISHED = "not_established"
    NOT_APPLICABLE = "not_applicable"


class RuleMappingStatus(StrEnum):
    MAPPED = "mapped"
    NO_MATCH = "no_match"
    UNCERTAIN = "uncertain"


class ClaimKind(StrEnum):
    REPORTED = "reported"
    INFERRED_CONTEXT = "inferred_context"


class SourceKind(StrEnum):
    ORIGINAL = "original"
    CLARIFICATION = "clarification"


class DatasetProvenance(StrEnum):
    SYNTHETIC = "synthetic"
    PUBLIC_REAL = "public_real"
    AUTHORIZED_INTERNAL = "authorized_internal"


class LabelProvenance(StrEnum):
    DEVELOPER_REVIEWED = "developer_reviewed"
    EXPERT_INDEPENDENT = "expert_independent"
    EXPERT_ADJUDICATED = "expert_adjudicated"
    WEAK_MACHINE_SUGGESTED = "weak_machine_suggested"


class AnalysisMode(StrEnum):
    LIVE = "live"
    FIXTURE_REPLAY = "fixture_replay"


class JobStatus(StrEnum):
    PENDING = "pending"
    CLAIMED = "claimed"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    EXPIRED = "expired"


class JobKind(StrEnum):
    ANALYZE_REPORT = "analyze_report"
    ANALYZE_LAB = "analyze_lab"


class ImportRowStatus(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    UNCHANGED = "unchanged"


class ValidationStatus(StrEnum):
    PENDING = "pending"
    VALIDATED = "validated"
    FAILED = "failed"


# IOGP Life-Saving Rule IDs
class LifeSavingRule(StrEnum):
    BYPASSING_SAFETY_CONTROLS = "bypassing_safety_controls"
    CONFINED_SPACE = "confined_space"
    DRIVING = "driving"
    ENERGY_ISOLATION = "energy_isolation"
    HOT_WORK = "hot_work"
    LINE_OF_FIRE = "line_of_fire"
    SAFE_MECHANICAL_LIFTING = "safe_mechanical_lifting"
    WORK_AUTHORISATION = "work_authorisation"
    WORKING_AT_HEIGHT = "working_at_height"


# Official titles mapping
LSR_OFFICIAL_TITLES: dict[str, str] = {
    LifeSavingRule.BYPASSING_SAFETY_CONTROLS: "Bypassing Safety Controls",
    LifeSavingRule.CONFINED_SPACE: "Confined Space",
    LifeSavingRule.DRIVING: "Driving",
    LifeSavingRule.ENERGY_ISOLATION: "Energy Isolation",
    LifeSavingRule.HOT_WORK: "Hot Work",
    LifeSavingRule.LINE_OF_FIRE: "Line of Fire",
    LifeSavingRule.SAFE_MECHANICAL_LIFTING: "Safe Mechanical Lifting",
    LifeSavingRule.WORK_AUTHORISATION: "Work Authorisation",
    LifeSavingRule.WORKING_AT_HEIGHT: "Working at Height",
}
