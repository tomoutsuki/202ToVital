# Graph Report - 202ToVital  (2026-10-09)

## Corpus Check
- 19 files · ~67,606 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 50 file(s) not represented in the graph (top: .vital 48, (none) 2)

## Summary
- 200 nodes · 361 edges · 12 communities (10 shown, 2 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 10 edges (avg confidence: 0.92)
- Token cost: AST 0; host semantic usage unavailable

## Community Hubs (Navigation)
- Format and Fidelity Evidence
- Graph Build Dependencies
- Source Parsing and Conversion Data
- CLI and Calibration Profiles
- Vital Assets and Serialization
- CLI and Parser Tests
- Synthesis Parameter Mapping
- Controlled Waveform Analysis
- Converter and Mapping Tests
- Waveform Fidelity Findings
- Controlled Recording Experiment
- Package Metadata

## God Nodes (most connected - your core abstractions)
1. `Converter` - 19 edges
2. `convert()` - 15 edges
3. `Profile` - 14 edges

## Surprising Connections (you probably didn't know these)
- `MappingTests` --uses--> `Profile`  [INFERRED]
  tests/test_converter.py → src/poison202_to_vital/profile.py
- `Tempo division and LFO approximation` --references--> `Conversion report`  [EXTRACTED]
  docs/mapping.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Four basic waves have close harmonic structures** — docs_controlled_waveform_review_saw_match, docs_controlled_waveform_review_sine_match, docs_controlled_waveform_review_square_match, docs_controlled_waveform_review_triangle_match [EXTRACTED 1.00]
- **Self-contained Vital state assets** — docs_format_vital_serialization, docs_format_wave_source, docs_format_noise_pcm [EXTRACTED 1.00]
- **Unmeasured Poison mappings need calibration** — docs_mapping_calibration_curves, docs_mapping_calibration_experiments, docs_validation_fidelity_unverified, readme_calibration_profile [INFERRED 0.95]

## Communities (12 total, 2 thin omitted)

### Community 0 - "Format and Fidelity Evidence"
Cohesion: 0.06
Nodes (41): Embedded int16 PCM sample, P202 binary framing, P202 parser validation, Pretty Pluck fixture correspondence, Absolute record offset table, Vital registered scalar defaults, Source-derived Vital scalar schema, Single preset and 47-preset bank (+33 more)

### Community 1 - "Graph Build Dependencies"
Cohesion: 0.08
Nodes (26): argparse, ast, datetime, graphify_analyze, graphify_build, graphify_cache, graphify_cli, graphify_cluster (+18 more)

### Community 2 - "Source Parsing and Conversion Data"
Cohesion: 0.12
Nodes (21): contextlib, dataclasses, io, math, Conversion, Best-effort mappings; all unknown Poison laws are reported, never asserted…, Poison-202 to Vital conversion. Runtime uses only the Python standard library., Bank (+13 more)

### Community 3 - "CLI and Calibration Profiles"
Cohesion: 0.18
Nodes (12): ArgumentParser, json_bytes(), main(), parser(), CLI entry point; conversion is offline and has no third-party dependencies., run_conversion(), select(), Profile (+4 more)

### Community 4 - "Vital Assets and Serialization"
Cohesion: 0.17
Nodes (14): base64, functools, importlib_resources, os, random, bundle(), init_preset(), line() (+6 more)

### Community 5 - "CLI and Parser Tests"
Cohesion: 0.19
Nodes (4): skipUnless, CliTests, encode(), ParserTests

### Community 7 - "Controlled Waveform Analysis"
Cohesion: 0.23
Nodes (13): av, numpy, activity(), cosine_similarity(), envelope(), harmonic_spectrum(), main(), major_frequency() (+5 more)

### Community 8 - "Converter and Mapping Tests"
Cohesion: 0.42
Nodes (3): convert(), MappingTests, source()

### Community 9 - "Waveform Fidelity Findings"
Cohesion: 0.40
Nodes (6): Relative steady-state harmonic comparison, Saw strong spectral match, Sine strong spectral match, Square strong spectral match, Super Saw mapping deficiency at zero controls, Triangle strong spectral match

### Community 10 - "Controlled Recording Experiment"
Cohesion: 0.50
Nodes (4): Controlled waveform comparison, Original MIDI 72 versus Vital MIDI 60, Source and Vital output level difference, Pitch-matched Vita renders at MIDI 72

## Ambiguous Edges - Review These
- `ASCII tags and float32 values` → `Provisional filter selector mapping`  [AMBIGUOUS]
  docs/format.md · relation: conceptually_related_to

## Knowledge Gaps
- **10 isolated node(s):** `poison202-to-vital`, `Absolute record offset table`, `Vital registered scalar defaults`, `Source-derived Vital scalar schema`, `Finite samples and amplitude statistics` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 63 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `ASCII tags and float32 values` and `Provisional filter selector mapping`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `Converter` connect `Synthesis Parameter Mapping` to `Converter and Mapping Tests`, `Source Parsing and Conversion Data`, `CLI and Calibration Profiles`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
## Token accounting clarification

AST extraction has no LLM token cost. Host-agent semantic token usage was not exposed by the agent tool; JSON counters are zero placeholders, not measured zero semantic usage.

## Graph health warning

Raw AST extraction contains 69 unresolved endpoint edges, 1 self-loop, and 8 same-endpoint edges collapsed in the undirected graph. External references may be placeholders; the graph is navigable but not a lossless call graph. See health.json.
