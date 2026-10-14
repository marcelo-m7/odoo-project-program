# ADR 0001: Extend project.milestone for numeric goals

Date: 2026-10-14. Status: accepted for implementation.

The latest V5 annotation asks us to start with native milestones. Odoo 19 `project.milestone` already belongs to a `project.project`, links tasks and has a completion flag. It has no baseline, target, unit, measurement history or target versions. We extend it with optional numeric goal fields gated by `is_program_goal`, leaving ordinary milestones unchanged. Each target change creates a new milestone version linked to its predecessor, while validated measurements continue to point to the old version. Reaching a milestone does not validate a numeric measurement.

AC03: each goal keeps its own unit; no cross-unit aggregate. AC04: a referenced version becomes immutable and changes create a successor. AC05: measurements use a required float so zero is data, while missing measurement has no record and displays as no data; the signed denominator supports increase and decrease, and progress is not capped at 100%.

Trade-off: a goal version is also a standard milestone and can appear in native milestone lists. Views filter current versions by default. The historical versions remain searchable for audit.
