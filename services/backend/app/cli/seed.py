"""Seed demo dataset with sample Oil India safety reports."""

import asyncio
import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db.models import Base, Dataset, Job, Report, ReportRevision, SourceSegment


# ---------------------------------------------------------------------------
# Sample narratives — realistic Oil India SIF precursor scenarios
# ---------------------------------------------------------------------------
DEMO_REPORTS = [
    {
        "source_id": "OIL-2025-0147",
        "site": "Duliajan Field",
        "report_type": "near_miss",
        "narrative": (
            "During routine well-head maintenance at Well #DJ-42, a rigger was working at "
            "approximately 6 meters height on the monkey board without a fall arrest harness. "
            "The safety officer observed the situation during a routine patrol and immediately "
            "stopped the work. The rigger stated his harness was damaged and he decided to "
            "proceed without it to avoid delaying the scheduled maintenance. No injury occurred. "
            "Investigation found that harness inspection records were 3 months overdue and "
            "the permit-to-work did not include a height work checklist."
        ),
    },
    {
        "source_id": "OIL-2025-0163",
        "site": "Moran Processing Plant",
        "report_type": "unsafe_condition",
        "narrative": (
            "A pressure relief valve on the gas dehydration unit TEG-03 was found to be "
            "corroded and seized during a planned turnaround inspection. The valve had not been "
            "tested since installation 18 months ago, contrary to the 6-month testing schedule "
            "in the process safety management plan. If the valve had failed to open during an "
            "overpressure event, the vessel could have exceeded its design pressure of 45 bar. "
            "The dehydration unit processes approximately 2.5 MMSCMD of natural gas. "
            "No process upset occurred during the period the valve was non-functional."
        ),
    },
    {
        "source_id": "OIL-2025-0178",
        "site": "Naharkatiya Drilling Site",
        "report_type": "near_miss",
        "narrative": (
            "While lifting a 2.8-ton BOP stack with the rig crane, the main lifting sling "
            "showed visible strand breakage at approximately 15 meters elevation. The crane "
            "operator noticed the load shifting and immediately lowered it to the ground. "
            "Two workers were positioned in the red zone beneath the load path, contrary to "
            "the lifting plan. The sling was last inspected 45 days prior and certified as fit. "
            "Weather conditions were clear with wind at 12 km/h. The shift supervisor was "
            "not present at the lift site despite the critical lift classification."
        ),
    },
    {
        "source_id": "OIL-2025-0191",
        "site": "Digboi Refinery",
        "report_type": "incident",
        "narrative": (
            "A contract worker received second-degree burns to his left forearm when a flange "
            "on a steam line (150°C, 8 bar) failed during bolt tightening. The gasket had been "
            "replaced the previous day but was found to be the wrong specification — a spiral "
            "wound gasket rated for 5 bar was used instead of the required 16 bar rated gasket. "
            "The worker was wearing standard cotton coveralls but not the required heat-resistant "
            "arm guards specified in the hot work procedure. He was treated at the site medical "
            "center and referred to Dibrugarh hospital. The material requisition showed the "
            "correct gasket was out of stock for 2 weeks."
        ),
    },
    {
        "source_id": "OIL-2025-0203",
        "site": "Jorhat Pipeline Corridor",
        "report_type": "near_miss",
        "narrative": (
            "During pipeline right-of-way inspection, the patrol team discovered unauthorized "
            "third-party excavation within 3 meters of the 16-inch crude oil trunk pipeline "
            "(operating at 28 bar). A JCB excavator was observed digging a foundation trench "
            "for a residential building. The excavation had reached 1.5 meters depth; the "
            "pipeline burial depth at that location is 1.2 meters per the as-built survey. "
            "The contractor had no dig permit and was unaware of the pipeline's presence. "
            "Pipeline marker posts were found to be missing for a 200-meter stretch. "
            "Operations were halted and the area was secured."
        ),
    },
    {
        "source_id": "OIL-2025-0215",
        "site": "Duliajan Field",
        "report_type": "unsafe_act",
        "narrative": (
            "A production operator was found bypassing the high-level shutdown alarm on "
            "crude oil storage tank T-14 (capacity 5000 barrels). The operator had jumpered "
            "the level transmitter signal to prevent repeated nuisance trips that had been "
            "occurring for the past week due to a faulty transmitter. The operator's supervisor "
            "was aware of the faulty transmitter but had not raised a maintenance work order. "
            "During the bypass period, the tank level was being monitored manually every 2 hours "
            "instead of the continuous automated monitoring. A tank overflow at this location "
            "would flow into the nearby Burhi Dihing river tributary within 50 meters."
        ),
    },
    {
        "source_id": "OIL-2025-0228",
        "site": "Geleki Gas Collection Station",
        "report_type": "near_miss",
        "narrative": (
            "While performing a gas leak survey with an infrared camera, a significant methane "
            "leak was detected at the inlet manifold flange of the gas compressor K-201. "
            "Quantification estimated the leak rate at approximately 50 kg/hour. The leak had "
            "gone undetected for an estimated 3-5 days based on the last survey records. "
            "The gas detection system in the area showed no alarms during this period — "
            "investigation revealed that 2 of 4 gas detectors in the zone were in fault mode "
            "and had not been repaired. The area is classified as Zone 1 hazardous. "
            "The compressor was shut down and the flange was re-torqued."
        ),
    },
    {
        "source_id": "OIL-2025-0234",
        "site": "Moran Processing Plant",
        "report_type": "near_miss",
        "narrative": (
            "A tanker truck carrying 16 kiloliters of crude oil overturned on the internal "
            "haul road between the gathering station and the processing plant. The driver "
            "was traveling at approximately 45 km/h in a zone with a 25 km/h speed limit. "
            "The road had a sharp curve with no guardrail or warning signage. Approximately "
            "2000 liters of crude spilled onto the unpaved road surface before the tanker "
            "could be righted. The driver sustained minor injuries. The vehicle's speed "
            "limiting device was found to be disabled. The driver's logbook showed he had "
            "been on duty for 14 hours at the time of the incident."
        ),
    },
    {
        "source_id": "OIL-2025-0247",
        "site": "Naharkatiya Drilling Site",
        "report_type": "unsafe_condition",
        "narrative": (
            "A routine electrical inspection identified exposed live conductors on the "
            "temporary power distribution board at Rig #NK-12. The main breaker panel cover "
            "was missing, exposing 440V bus bars. The electrician reported the cover had been "
            "removed 2 weeks earlier to troubleshoot a tripping issue and was never reinstalled. "
            "Multiple cable entries to the panel lacked proper glands, allowing water ingress. "
            "The inspection was prompted by an electrical shock report from a roughneck who "
            "touched the panel frame while wearing wet gloves. He experienced tingling but "
            "no injury requiring treatment."
        ),
    },
    {
        "source_id": "OIL-2025-0259",
        "site": "Rupsi Helibase",
        "report_type": "near_miss",
        "narrative": (
            "During helicopter passenger transfer operations, a ground crew member walked into "
            "the tail rotor danger zone while the aircraft (Dauphin AS365) was at flight idle. "
            "The pilot observed the crew member through the rear mirror and immediately "
            "alerted via intercom. The crew member was within 2 meters of the tail rotor. "
            "Investigation found the ground crew member had not completed the mandatory "
            "helipad safety refresher training due 3 months ago. The painted danger zone "
            "markings on the helipad were faded and barely visible. Wind conditions were "
            "gusty at 25 knots, creating noise that may have masked the tail rotor sound."
        ),
    },
]


async def seed_demo_data():
    """Create demo dataset and seed sample reports."""
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Create demo dataset
        dataset = Dataset(
            name="Oil India Demo Dataset",
            provenance="synthetic",
            usage_permission="demo_only",
            is_demo=True,
        )
        session.add(dataset)
        await session.flush()

        for report_data in DEMO_REPORTS:
            # Create report
            report = Report(
                dataset_id=dataset.id,
                source_report_id=report_data["source_id"],
                supplied_site=report_data["site"],
                report_type=report_data["report_type"],
            )
            session.add(report)
            await session.flush()

            # Create initial revision
            narrative = report_data["narrative"]
            text_hash = hashlib.sha256(narrative.encode()).hexdigest()
            revision = ReportRevision(
                report_id=report.id,
                revision_number=1,
                original_text=narrative,
                source_kind="original",
                text_hash=text_hash,
            )
            session.add(revision)
            await session.flush()

            # Create source segment
            segment = SourceSegment(
                report_revision_id=revision.id,
                kind="original",
                text=narrative,
            )
            session.add(segment)

            # Link revision to report
            report.current_revision_id = revision.id

            # Enqueue analysis job so the worker classifies it
            job = Job(
                kind="analyze_report",
                payload={
                    "report_id": str(report.id),
                    "revision_id": str(revision.id),
                    "text_hash": text_hash,
                },
                idempotency_key=f"analyze:{report.id}:rev:{revision.id}",
                status="pending",
            )
            session.add(job)

        await session.commit()
        print(f"Seeded {len(DEMO_REPORTS)} demo reports in dataset '{dataset.name}' (id={dataset.id})")
        print(f"Enqueued {len(DEMO_REPORTS)} analysis jobs — start the worker to classify them.")

    await engine.dispose()


def main():
    asyncio.run(seed_demo_data())


if __name__ == "__main__":
    main()
