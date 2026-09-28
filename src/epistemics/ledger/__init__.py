"""Experiment ledger: reproducible tables and facts from frozen collection artifacts.

Every figure is recomputed from plan, execution and report files under `output/`. Disposition
reports are verified and read with the implementation snapshot they were collected under, so
version-specific designs are interpreted by the code that produced them. The hand-maintained
registry (`docs/experiments.json`) supplies questions, predictions and outcomes.
"""

VERSION = "ledger/0.1.0"
