# Graph Report - 202ToVital  (2026-10-09)

## Corpus Check
- Corpus is ~9,954 words - fits in a single context window. You may not need a graph.

## Summary
- 210 nodes · 379 edges · 11 communities (9 shown, 2 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 10 edges (avg confidence: 0.92)
- Token cost: AST 0; host semantic usage unavailable

## Community Hubs (Navigation)
- Format and Fidelity Evidence
- CLI and Vital Assets
- Graph Build Dependencies
- Source Parsing and Conversion Data
- Fitted Super Saw Mapping
- CLI and Parser Tests
- Synthesis Parameter Mapping
- Controlled Waveform Analysis
- Converter and Mapping Tests
- Waveform Fidelity Findings
- Package Metadata

## God Nodes (most connected - your core abstractions)
1. `Converter` - 19 edges
2. `convert()` - 16 edges
3. `Profile` - 14 edges

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

## Communities (11 total, 2 thin omitted)

### Community 0 - "Format and Fidelity Evidence"
Cohesion: 0.06
Nodes (41): Embedded int16 PCM sample, P202 binary framing, P202 parser validation, Pretty Pluck fixture correspondence, Absolute record offset table, Vital registered scalar defaults, Source-derived Vital scalar schema, Single preset and 47-preset bank (+33 more)

### Community 1 - "CLI and Vital Assets"
Cohesion: 0.09
Nodes (26): ArgumentParser, base64, functools, importlib_resources, os, random, json_bytes(), main() (+18 more)

### Community 2 - "Graph Build Dependencies"
Cohesion: 0.07
Nodes (25): argparse, ast, datetime, graphify_analyze, graphify_build, graphify_cache, graphify_cli, graphify_cluster (+17 more)

### Community 3 - "Source Parsing and Conversion Data"
Cohesion: 0.12
Nodes (22): contextlib, dataclasses, io, math, pathlib, Conversion, Best-effort mappings; all unknown Poison laws are reported, never asserted…, Poison-202 to Vital conversion. Runtime uses only the Python standard library. (+14 more)

### Community 4 - "Fitted Super Saw Mapping"
Cohesion: 0.17
Nodes (12): Revised Super Saw mapping evidence, Fitted Super Saw MIX and DETUNE law, Zero-detune clamp policy, convert(), JP-8000/Szabo-style normalized Super Saw detune fit. Poison's controlled…, Map Poison MIX to Vital Blend by matching center/side gain ratios. The Poison…, Approximate positive outer-voice separation measured in Poison., supersaw_blend() (+4 more)

### Community 5 - "CLI and Parser Tests"
Cohesion: 0.19
Nodes (4): skipUnless, CliTests, encode(), ParserTests

### Community 7 - "Controlled Waveform Analysis"
Cohesion: 0.23
Nodes (13): av, numpy, activity(), cosine_similarity(), envelope(), harmonic_spectrum(), main(), major_frequency() (+5 more)

### Community 8 - "Converter and Mapping Tests"
Cohesion: 0.40
Nodes (6): Relative steady-state harmonic comparison, Saw strong spectral match, Sine strong spectral match, Square strong spectral match, Super Saw mapping deficiency at zero controls, Triangle strong spectral match

### Community 9 - "Waveform Fidelity Findings"
Cohesion: 0.50
Nodes (4): Controlled waveform comparison, Original MIDI 72 versus Vital MIDI 60, Source and Vital output level difference, Pitch-matched Vita renders at MIDI 72

## Ambiguous Edges - Review These
- `ASCII tags and float32 values` → `Provisional filter selector mapping`  [AMBIGUOUS]
  docs/format.md · relation: conceptually_related_to

## Knowledge Gaps
- **11 isolated node(s):** `poison202-to-vital`, `Absolute record offset table`, `Vital registered scalar defaults`, `Source-derived Vital scalar schema`, `Finite samples and amplitude statistics` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 68 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ASCII tags and float32 values` and `Provisional filter selector mapping`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Converter` connect `Synthesis Parameter Mapping` to `CLI and Vital Assets`, `Source Parsing and Conversion Data`, `Fitted Super Saw Mapping`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
## Token accounting clarification

AST extraction has no LLM token cost. Host-agent semantic token usage was not exposed by the agent tool; JSON counters are zero placeholders, not measured zero semantic usage.

## Graph health warning

Raw AST extraction contains 69 unresolved endpoint edges, 1 self-loop, and 8 same-endpoint edges collapsed in the undirected graph. External references may be placeholders; the graph is navigable but not a lossless call graph. See health.json.
