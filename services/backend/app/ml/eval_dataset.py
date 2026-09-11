"""Labelled evaluation dataset for benchmarking the Luck Test engine.

Each record is (narrative, label) where label is the ground-truth SIF potential.
The dataset is deliberately built around *adversarial pairs*: the same hazard and
control state described once with a benign outcome ("no injury") and once with a
severe outcome ("fatally injured"). Because SIF potential is defined by hazard +
exposure + control failure — NOT by the outcome — both members of a pair carry the
SAME label. This is exactly where a bag-of-words classifier fails: it latches onto
outcome words ("injured", "fatality", "hospital") and flips its prediction, while a
control-sensitive engine holds steady.

Labels: 1 = sif_potential, 0 = non_sif_potential.
"""

# Each tuple: (narrative, label, pair_id)
# pair_id groups outcome-swapped variants so the eval can measure "pair consistency".
EVAL_RECORDS: list[tuple[str, int, str]] = [
    # --- Pair A: working at height, no harness (SIF regardless of outcome) ---
    (
        "A rigger was working at 6 meters height on the monkey board without a fall "
        "arrest harness. His harness was damaged and he proceeded anyway. No injury occurred.",
        1, "height_no_harness",
    ),
    (
        "A rigger was working at 6 meters height on the monkey board without a fall "
        "arrest harness. His harness was damaged and he proceeded anyway. He fell and "
        "was fatally injured; he was pronounced dead at the hospital.",
        1, "height_no_harness",
    ),
    # --- Pair B: height WITH controls (non-SIF regardless of outcome) ---
    (
        "A rigger was working at 6 meters height. His fall arrest harness was worn "
        "correctly and inspection was up to date. The permit was valid. Work proceeded safely.",
        0, "height_with_controls",
    ),
    (
        "A rigger was working at 6 meters height. His fall arrest harness was worn "
        "correctly and inspection was up to date. He slipped but the harness arrested "
        "the fall; he was shaken but unharmed and completed the task.",
        0, "height_with_controls",
    ),
    # --- Pair C: crane lift, sling failure, workers in red zone ---
    (
        "While lifting a 2.8-ton BOP stack, the main sling showed strand breakage at 15 "
        "meters. Two workers were in the red zone beneath the load. The load was lowered. "
        "No one was hurt.",
        1, "lift_sling_failure",
    ),
    (
        "While lifting a 2.8-ton BOP stack, the main sling failed at 15 meters. Two workers "
        "were in the red zone beneath the load. The load struck a worker, who suffered "
        "fatal crush injuries.",
        1, "lift_sling_failure",
    ),
    # --- Pair D: gas leak, failed detectors, Zone 1 (process-safety SIF) ---
    (
        "A 50 kg/hour methane leak was found at the compressor flange in a Zone 1 area. "
        "Two of four gas detectors were in fault mode. The leak had gone undetected for "
        "days. It was isolated with no ignition.",
        1, "gas_leak_failed_detectors",
    ),
    (
        "A 50 kg/hour methane leak at the compressor flange in a Zone 1 area found an "
        "ignition source and exploded, killing two workers and injuring five.",
        1, "gas_leak_failed_detectors",
    ),
    # --- Pair E: minor slip, low energy (non-SIF regardless of wording) ---
    (
        "A worker slipped on a wet floor in the canteen and grazed his elbow. First aid "
        "was applied. Housekeeping was notified to mop the area.",
        0, "minor_slip",
    ),
    (
        "A worker slipped on a wet floor in the office corridor. He caught the handrail "
        "and did not fall. A wet-floor sign was placed.",
        0, "minor_slip",
    ),
    # --- Pair F: electrical, exposed 440V bus bars, wet gloves ---
    (
        "Exposed live 440V bus bars were found on a distribution board with the cover "
        "missing. A worker touched the frame with wet gloves and felt tingling. No injury.",
        1, "electrical_exposed_busbars",
    ),
    (
        "Exposed live 440V bus bars on a distribution board with the cover missing "
        "electrocuted a worker who touched the frame with wet gloves; he died on site.",
        1, "electrical_exposed_busbars",
    ),
    # --- Pair G: driving, overspeed, disabled limiter, fatigue ---
    (
        "A crude tanker took a sharp curve at 45 km/h in a 25 km/h zone; the speed limiter "
        "was disabled and the driver had been on duty 14 hours. It nearly overturned but "
        "the driver recovered. No spill.",
        1, "driving_overspeed",
    ),
    (
        "A crude tanker took a sharp curve at 45 km/h in a 25 km/h zone; the speed limiter "
        "was disabled and the driver had been on duty 14 hours. It overturned and the "
        "driver was killed.",
        1, "driving_overspeed",
    ),
    # --- Singletons: clear non-SIF administrative/observation reports ---
    (
        "During an inspection, a torn safety poster was found in the mess hall. It was "
        "replaced the same day.",
        0, "admin_poster",
    ),
    (
        "A near-miss form was submitted noting that a bin lid was left open near the office "
        "entrance. It was closed.",
        0, "admin_bin",
    ),
]
