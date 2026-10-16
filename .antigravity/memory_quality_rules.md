# Memory Palace Rigor & Antigravity Quality Gates

Before pushing or completing an edit to `palace-engine`:

1. COGNITIVE AUDIT:
   - Run `python engine/cognitive_linter.py`.
   - Any locus without kinetic, violent, or high-contrast sensory verbs must be rejected and rewritten.
   - Any numerical constraint must use the Major System consonant mapping. No naked numbers.

2. SRS CALIBRATION:
   - Verify that test mistakes immediately collapse intervals to 1 day.
   - Cross-concept mistakes must be logged into `confusion_pairs`.

3. PRE-COMMIT VERIFICATION:
   - Run `bash scripts/quality_scrub.sh`.
   - Ensure clean exit code 0.
