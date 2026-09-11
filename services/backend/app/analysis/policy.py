"""Policy engine — derive the Luck Test classification from raw extraction.

This is the heart of the outcome-resistant classifier. Given the structured
signals from the adapter (hazard energy, exposure, control state), it applies
the policy to produce:

  candidate_label:  sif_potential | non_sif_potential
  interpretation:   serious_exposure | controls_reported | low_potential
                    | insufficient_information | actual_sif

The core rule (the "Luck Test"):
  A report is SIF-POTENTIAL when a SERIOUS hazard energy source was present
  AND a person was (or could plausibly have been) exposed to it AND the
  controls that should have prevented harm were absent, failed, or bypassed.
  Whether harm actually occurred is IRRELEVANT to this determination.

Serious hazard energies (per IOGP SIF taxonomy): gravity/height, pressure,
mechanical (lifting/crushing), electrical (>50V), fire/explosion,
toxic/asphyxiation, vehicle.
"""

from __future__ import annotations

POLICY_VERSION = "luck-test-policy-v1"
TAXONOMY_VERSION = "iogp-sif-v1"

# Hazard kinds considered "serious" energy sources for SIF potential
SERIOUS_HAZARDS = {
    "gravity",
    "pressure",
    "mechanical",
    "electrical",
    "fire_explosion",
    "toxic_asphyxiation",
    "vehicle",
}

# Major-accident / process-safety hazards. For these, exposure is area- or
# population-level: a large gas release, overpressure, or toxic cloud in an
# occupied or hazardous-classified area threatens anyone present, even when
# the narrative names no single exposed individual. So a control failure on
# one of these is enough to establish SIF potential without a personal
# exposure signal.
PROCESS_SAFETY_HAZARDS = {
    "fire_explosion",
    "toxic_asphyxiation",
    "pressure",
}


def apply_policy(raw: dict) -> dict:
    """Apply the Luck Test policy to raw extraction.

    Returns a dict with candidate_label, interpretation, rationale,
    and the derived facts summary.
    """
    hazards = raw.get("hazards", [])
    has_exposure = raw.get("has_exposure", False)
    failure_count = raw.get("control_failure_count", 0)
    success_count = raw.get("control_success_count", 0)
    narrative_length = raw.get("narrative_length", 0)

    # Identify serious hazards present
    serious_present = [
        h for h in hazards if h["hazard_kind"] in SERIOUS_HAZARDS
    ]
    top_hazard = serious_present[0]["hazard_kind"] if serious_present else None

    rationale_parts: list[str] = []

    # --- Insufficient information check ---
    if narrative_length < 80 or (not hazards and not has_exposure):
        return {
            "candidate_label": "non_sif_potential",
            "interpretation": "insufficient_information",
            "top_hazard": top_hazard,
            "has_serious_hazard": bool(serious_present),
            "has_exposure": has_exposure,
            "control_state": "unknown",
            "rationale": (
                "The narrative does not contain enough detail to assess "
                "hazard energy, exposure, or control state. More information "
                "is needed before a SIF-potential determination can be made."
            ),
            "policy_version": POLICY_VERSION,
            "taxonomy_version": TAXONOMY_VERSION,
        }

    # --- Determine control state ---
    if failure_count > success_count and failure_count > 0:
        control_state = "absent_or_failed"
        rationale_parts.append(
            f"controls were absent, failed, or bypassed ({failure_count} failure signals)"
        )
    elif success_count > 0 and success_count >= failure_count:
        control_state = "reported_effective"
        rationale_parts.append(
            f"controls were reported in place and effective ({success_count} success signals)"
        )
    else:
        control_state = "unclear"
        rationale_parts.append("control state is unclear from the narrative")

    # --- The Luck Test decision ---
    has_serious = bool(serious_present)

    # Area-level exposure: a process-safety hazard with any control failure
    # exposes everyone in the vicinity, so it counts as exposure for the test.
    has_process_safety = any(
        h["hazard_kind"] in PROCESS_SAFETY_HAZARDS for h in serious_present
    )
    area_exposure = has_process_safety and failure_count >= 1
    effective_exposure = has_exposure or area_exposure

    if area_exposure and not has_exposure:
        rationale_parts.append(
            "exposure is assessed at the area/population level because a "
            "major-accident hazard was present with a control failure"
        )

    if has_serious and (effective_exposure or failure_count >= 2):
        if control_state == "reported_effective":
            # Serious hazard + exposure, but controls held → controls_reported
            candidate_label = "non_sif_potential"
            interpretation = "controls_reported"
            rationale_parts.insert(
                0,
                f"A serious {top_hazard} hazard with exposure was present, but "
                f"the narrative reports the relevant controls were in place and "
                f"effective. This is a positive control outcome, not a SIF precursor.",
            )
        else:
            # Serious hazard + exposure + failed/absent controls → SIF potential
            candidate_label = "sif_potential"
            interpretation = "serious_exposure"
            rationale_parts.insert(
                0,
                f"A serious {top_hazard} hazard was present with a person exposed "
                f"to it, and the controls that should have prevented harm were "
                f"absent, failed, or bypassed. Under the Luck Test this is "
                f"SIF-potential regardless of whether injury actually occurred — "
                f"the outcome turned on luck, not on effective barriers.",
            )
    elif has_serious and not effective_exposure:
        # Serious hazard but no clear exposure → lower potential
        candidate_label = "non_sif_potential"
        interpretation = "low_potential"
        rationale_parts.insert(
            0,
            f"A {top_hazard} hazard was identified, but the narrative does not "
            f"indicate a person was exposed to its energy in a way that could "
            f"have caused serious or fatal injury.",
        )
    else:
        # No serious hazard
        candidate_label = "non_sif_potential"
        interpretation = "low_potential"
        rationale_parts.insert(
            0,
            "No serious hazard energy source with credible potential for "
            "fatal or life-altering injury was identified in the narrative.",
        )

    return {
        "candidate_label": candidate_label,
        "interpretation": interpretation,
        "top_hazard": top_hazard,
        "has_serious_hazard": has_serious,
        "has_exposure": effective_exposure,
        "personal_exposure": has_exposure,
        "area_exposure": area_exposure,
        "control_state": control_state,
        "rationale": " ".join(rationale_parts),
        "policy_version": POLICY_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
    }
