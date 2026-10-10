# Graph Report - 202ToVital  (2026-10-09)

## Corpus Check
- Corpus is ~10,299 words - fits in a single context window. You may not need a graph.

## Summary
- 242 nodes · 412 edges · 16 communities (13 shown, 3 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.92)
- Token cost: AST 0; host semantic usage unavailable

## Community Hubs (Navigation)
- Format and Fidelity Evidence
- Fitted Super Saw Mapping
- CLI and Vital Assets
- Graph Build Dependencies
- Synthesis Parameter Mapping
- Source Parsing and Validation
- CLI and Parser Tests
- Controlled Waveform Analysis
- Super Saw Vital Strategy
- Free-running LFO Calibration
- Waveform Fidelity Findings
- LFO Reset Policy
- Controlled Waveform Comparison
- Tempo-Sync Approximation
- Signed Modulation
- Package Metadata

## God Nodes (most connected - your core abstractions)
1. `Converter` - 19 edges
2. `convert()` - 17 edges
3. `Profile` - 16 edges

## Surprising Connections (you probably didn't know these)
- `Zero-detune clamp policy` --rationale_for--> `supersaw_detune_curve()`  [EXTRACTED]
  docs/mapping.md → src/poison202_to_vital/convert.py
- `Fitted Super Saw MIX and DETUNE law` --rationale_for--> `supersaw_detune_curve()`  [EXTRACTED]
  docs/mapping.md → src/poison202_to_vital/convert.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Four basic waves have close harmonic structures** — docs_controlled_waveform_review_saw_match, docs_controlled_waveform_review_sine_match, docs_controlled_waveform_review_square_match, docs_controlled_waveform_review_triangle_match [EXTRACTED 1.00]
- **Self-contained Vital state assets** — docs_format_vital_serialization, docs_format_wave_source, docs_format_noise_pcm [EXTRACTED 1.00]
- **Fitted Super Saw control mapping** — docs_mapping_fitted_supersaw_control_law, src_poison202_to_vital_convert_supersaw_blend, src_poison202_to_vital_convert_supersaw_detune_curve, src_poison202_to_vital_convert_supersaw_outer_cents [EXTRACTED 1.00]
- **Unmeasured Poison mappings need calibration** — docs_mapping_calibration_curves, docs_mapping_calibration_experiments, docs_validation_fidelity_unverified, readme_calibration_profile [INFERRED 0.95]

## Communities (16 total, 3 thin omitted)

### Community 0 - "Format and Fidelity Evidence"
Cohesion: 0.07
Nodes (40): Embedded int16 PCM sample, P202 binary framing, P202 parser validation, Pretty Pluck fixture correspondence, Absolute record offset table, Vital registered scalar defaults, Source-derived Vital scalar schema, Single preset and 47-preset bank (+32 more)

### Community 1 - "Fitted Super Saw Mapping"
Cohesion: 0.10
Nodes (20): contextlib, Revised Super Saw mapping evidence, Fitted Super Saw MIX and DETUNE law, Zero-detune clamp policy, Conversion, convert(), lfo_free_rate_hz(), Best-effort mappings; all unknown Poison laws are reported, never asserted… (+12 more)

### Community 2 - "CLI and Vital Assets"
Cohesion: 0.10
Nodes (27): ArgumentParser, base64, functools, importlib_resources, io, os, random, json_bytes() (+19 more)

### Community 3 - "Graph Build Dependencies"
Cohesion: 0.07
Nodes (25): argparse, ast, datetime, graphify_analyze, graphify_build, graphify_cache, graphify_cli, graphify_cluster (+17 more)

### Community 5 - "Source Parsing and Validation"
Cohesion: 0.17
Nodes (14): dataclasses, math, pathlib, Bank, FormatError, load(), parse(), Path (+6 more)

### Community 6 - "CLI and Parser Tests"
Cohesion: 0.19
Nodes (4): skipUnless, CliTests, encode(), ParserTests

### Community 7 - "Controlled Waveform Analysis"
Cohesion: 0.23
Nodes (13): av, numpy, activity(), cosine_similarity(), envelope(), harmonic_spectrum(), main(), major_frequency() (+5 more)

### Community 8 - "Super Saw Vital Strategy"
Cohesion: 0.15
Nodes (13): Nonlinear DETUNE Mapping, Detune Power 0.95, Sustained Full-Detune Recording, Measured Outer-Voice Cents, Missing Lowest JP Side Voice, Nonlinear MIX Mapping, Poison Physical Voice Count, Random Oscillator Phase (+5 more)

### Community 9 - "Free-running LFO Calibration"
Cohesion: 0.29
Nodes (7): Default Calibration Profile, Free-running LFO Rate Mapping, LFO Maximum Frequency Profile Control, LFO Minimum Frequency, LFO Rate Exponent Profile Control, Measured LFO Rate Points, Mapping Decisions and Known Fidelity Limits

### Community 10 - "Waveform Fidelity Findings"
Cohesion: 0.40
Nodes (6): Relative steady-state harmonic comparison, Saw strong spectral match, Sine strong spectral match, Square strong spectral match, Super Saw mapping deficiency at zero controls, Triangle strong spectral match

### Community 11 - "LFO Reset Policy"
Cohesion: 0.33
Nodes (6): LFO Reset Policy, Normal LFO Phase-zero Reset, Poison Reset-phase Offset, Poison RETRIG, Random LFO Per-note Reset, Vital Sample-and-hold Generator

### Community 12 - "Controlled Waveform Comparison"
Cohesion: 0.50
Nodes (4): Controlled waveform comparison, Original MIDI 72 versus Vital MIDI 60, Source and Vital output level difference, Pitch-matched Vita renders at MIDI 72

### Community 13 - "Tempo-Sync Approximation"
Cohesion: 0.67
Nodes (3): Uncertain 22-entry Tempo Division List, Tempo-sync Mapping, Vital Straight Dotted Triplet Divisions

## Ambiguous Edges - Review These
- `ASCII tags and float32 values` → `Provisional filter selector mapping`  [AMBIGUOUS]
  docs/format.md · relation: conceptually_related_to

## Knowledge Gaps
- **30 isolated node(s):** `poison202-to-vital`, `Absolute record offset table`, `Vital registered scalar defaults`, `Source-derived Vital scalar schema`, `Finite samples and amplitude statistics` (+25 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 87 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ASCII tags and float32 values` and `Provisional filter selector mapping`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Converter` connect `Synthesis Parameter Mapping` to `Fitted Super Saw Mapping`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
## Token accounting clarification

AST extraction has no LLM token cost. Host-agent semantic token usage was not exposed by the agent tool; JSON counters are zero placeholders, not measured zero semantic usage.

## Graph health warning

Raw AST extraction contains 69 unresolved endpoint edges, 1 self-loop, and 9 same-endpoint edges collapsed in the undirected graph. External references may be placeholders; the graph is navigable but not a lossless call graph. See health.json.
