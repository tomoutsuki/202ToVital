"""Build/label the project graph from AST plus host-extracted semantic JSON.

Run with graphify's Python interpreter after semantic extraction via the skill:
  /path/to/graphify/python tools/build_graph.py
  /path/to/graphify/python tools/build_graph.py --labels graphify-out/community-labels.json
The curated semantic input is kept at graphify-out/semantic.json for auditing.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from graphify.analyze import god_nodes, surprising_connections, suggest_questions
from graphify.build import build_from_json
from graphify.cache import save_semantic_cache
from graphify.cli import _stamped_manifest_files
from graphify.cluster import cluster, score_all
from graphify.detect import detect, save_manifest
from graphify.diagnostics import diagnose_extraction, format_diagnostic_report
from graphify.export import to_json
from graphify.extract import extract
from graphify.report import generate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--labels', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = root / 'graphify-out'
    out.mkdir(exist_ok=True)
    semantic = json.loads((out / 'semantic.json').read_text())
    detection = detect(root)
    if detection['total_files'] > 500 or detection['total_words'] > 2_000_000:
        raise SystemExit('Corpus exceeds skill threshold: narrow the scan before building')
    if detection.get('skipped_sensitive'):
        print('Skipped sensitive:', detection['skipped_sensitive'])
    structural = extract([Path(f) for f in detection['files'].get('code', [])], cache_root=root)
    nodes = {n['id']: n for n in structural['nodes']}
    for node in semantic['nodes']:
        nodes.setdefault(node['id'], node)
    extraction = {'nodes': list(nodes.values()), 'edges': structural['edges'] + semantic['edges'],
                  'hyperedges': semantic.get('hyperedges', []), 'input_tokens': 0, 'output_tokens': 0}
    for name, data in [('detect', detection), ('extract', extraction), ('ast', structural), ('semantic', semantic)]:
        (out / f'.graphify_{name}.json').write_text(json.dumps(data, indent=2))
    graph = build_from_json(extraction, root=str(root), directed=False)
    if not graph.number_of_nodes():
        raise SystemExit('Empty extraction; refusing to overwrite graph')
    communities = cluster(graph)
    cohesion = score_all(graph, communities)
    labels = {int(k): v for k, v in json.loads(args.labels.read_text()).items()} if args.labels else {cid: f'Community {cid}' for cid in communities}
    gods = god_nodes(graph)[:3]
    surprises = surprising_connections(graph, communities)[:2]
    questions = suggest_questions(graph, communities, labels)[:2]
    if not to_json(graph, communities, str(out / 'graph.json'), community_labels=labels):
        raise SystemExit('Graph shrink guard refused export')
    report = generate(graph, communities, cohesion, labels, gods, surprises, detection,
                      {'input': 0, 'output': 0}, str(root), suggested_questions=questions)
    report = report.replace('Token cost: 0 input · 0 output', 'Token cost: AST 0; host semantic usage unavailable')
    report += '\n## Token accounting clarification\n\nAST extraction has no LLM token cost. Host-agent semantic token usage was not exposed by the agent tool; JSON counters are zero placeholders, not measured zero semantic usage.\n'
    (out / 'GRAPH_REPORT.md').write_text(report)
    analysis = {'communities': {str(k): v for k, v in communities.items()},
                'cohesion': {str(k): v for k, v in cohesion.items()}, 'gods': gods,
                'surprises': surprises, 'questions': questions}
    (out / '.graphify_analysis.json').write_text(json.dumps(analysis, indent=2))
    (out / '.graphify_labels.json').write_text(json.dumps(labels))
    health = diagnose_extraction(extraction, directed=False, root=str(root))
    (out / 'health.json').write_text(json.dumps(health, indent=2))
    report += (f'\n## Graph health warning\n\nRaw AST extraction contains '
               f'{health.get("dangling_endpoint_edges", 0)} unresolved endpoint edges, '
               f'{health.get("self_loop_edges", 0)} self-loop, and '
               f'{health.get("undirected_same_endpoint_collapsed_edges", 0)} same-endpoint edges '
               'collapsed in the undirected graph. External references may be placeholders; '
               'the graph is navigable but not a lossless call graph. See health.json.\n')
    (out / 'GRAPH_REPORT.md').write_text(report)
    print(format_diagnostic_report(health))
    print(f'Graph: {graph.number_of_nodes()} nodes; {graph.number_of_edges()} edges; {len(communities)} communities')
    for cid, members in communities.items():
        print(cid, ':', ', '.join(graph.nodes[n].get('label', n) for n in members[:12]))
    if args.labels:
        files = detection['files']
        semantic_files = [f for t in ('document', 'paper', 'image') for f in files.get(t, [])]
        spec = Path('/home/tomas/.codex/skills/graphify/references/extraction-spec.md')
        if spec.exists():
            save_semantic_cache(semantic['nodes'], semantic['edges'], semantic.get('hyperedges', []),
                                root=str(root), allowed_source_files=semantic_files, prompt_file=str(spec))
        stamped = _stamped_manifest_files(files, extraction, root)
        scan = {f for paths in files.values() for f in paths}
        stamped_set = {f for paths in stamped.values() for f in paths}
        save_manifest(stamped, root=str(root), scan_corpus=scan, clear_semantic=set(semantic_files) - stamped_set or None)
        cost_path = out / 'cost.json'
        cost = json.loads(cost_path.read_text()) if cost_path.exists() else {'runs': [], 'total_input_tokens': 0, 'total_output_tokens': 0}
        cost['runs'].append({'date': datetime.now(timezone.utc).isoformat(), 'input_tokens': 0, 'output_tokens': 0,
                             'files': detection['total_files'], 'semantic_token_usage': 'unavailable from host agent tool'})
        cost_path.write_text(json.dumps(cost, indent=2))
        (out / '.graphify_python').write_text(sys.executable)
        (out / '.graphify_root').write_text(str(root))


if __name__ == '__main__':
    main()
