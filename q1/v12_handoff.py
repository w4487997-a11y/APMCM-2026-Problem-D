"""Publish V1.2 column names and local Git provenance from the frozen v1 predictions."""

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from audit.init_check import COMPOSITION, read_csv
from q1.baselines import ROOT, sha256, write_table
from q1.experiments import write_json


FROZEN = ROOT / 'handoff' / 'v1'
EXPORT = ROOT / 'handoff' / 'v1_2'
MANIFEST = ROOT / 'handoff' / 'manifest.json'
PLAN = ROOT / 'APMCM_D_final_execution_V1.2.md'
SUPPLEMENT = ROOT / 'experiments' / 'q1_v12'
NEW_FILES = {'04': 'q1_holdout_predictions.csv', '07': 'q2_pool_predictions.csv',
             '08': 'q3_pool_predictions.csv', '11': 'q2_blind_predictions.csv',
             '12': 'q3_blind_predictions.csv'}
NEW_FIELDS = (*COMPOSITION, 'V_hat', 'pool', 'model_version', 'source_pool')


def remap_pool(row, pool):
    if row['source_pool'] != pool:
        raise ValueError(f'Expected {pool} in frozen pool record')
    return {k: pool if k == 'pool' else row[k] for k in NEW_FIELDS}


def source_snapshot(directory):
    sources = [path for folder in ('q1', 'audit', 'tests') for path in
               sorted((ROOT / folder).glob('*.py'))]
    sources.append(ROOT / 'requirements-baseline.txt')
    with TemporaryDirectory(prefix='q1-private-source-') as work:
        repo = Path(work)
        git = lambda *args: subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()
        git('init', '-q', '-b', 'q1-v1-2')
        git('config', 'core.autocrlf', 'false')
        git('config', 'user.name', 'APMCM Q1 Source Snapshot')
        git('config', 'user.email', 'q1-source-snapshot@example.invalid')
        git('config', 'commit.gpgsign', 'false')
        for source in sources:
            target = repo / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        git('add', '.')
        git('commit', '-qm', 'Archive Q1 V1.2 source and dependency pins')
        commit = git('rev-parse', 'HEAD')
        bundle = directory / 'q1_source.bundle'
        git('bundle', 'create', str(bundle.resolve()), 'q1-v1-2')
        advertised = git('bundle', 'list-heads', str(bundle.resolve()))
        if advertised != f'{commit} refs/heads/q1-v1-2':
            raise ValueError('Unexpected Git bundle reference')
    return {'commit': commit, 'branch': 'q1-v1-2', 'file': bundle.name, 'bundle_sha256': sha256(bundle),
            'scope': 'Local snapshot. Source files, tests and pinned requirements only.',
            'files': {p.relative_to(ROOT).as_posix(): sha256(p) for p in sources}}


def build(out, manifest):
    old = json.loads((FROZEN / 'manifest.json').read_text(encoding='utf-8'))
    for filename, expected in old['artifacts_sha256'].items():
        if sha256(FROZEN / filename) != expected:
            raise ValueError(f'Frozen file changed: {filename}')
    if not (SUPPLEMENT / 'run_config.json').is_file():
        raise ValueError('Run the V1.2 supplement first.')
    out.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=out.parent, prefix='.v12-export-') as work:
        stage = Path(work) / 'release'
        stage.mkdir()
        merged, pools = [], {}
        for pool, name in NEW_FILES.items():
            previous_name = old['outputs'][pool]['file']
            _, frozen_rows = read_csv(FROZEN / previous_name)
            mapped = [remap_pool(row, pool) for row in frozen_rows]
            write_table(stage / name, mapped)
            if pool != '04':
                merged.extend(mapped)
            pools[pool] = {**old['outputs'][pool], 'file': name,
                           'sha256': sha256(stage / name), 'frozen_file': previous_name,
                           'frozen_sha256': old['artifacts_sha256'][previous_name],
                           'same_v_hat_as_frozen': True}
        if len(merged) != len({(r['pool'], r['id']) for r in merged}):
            raise ValueError('Duplicate pool and ID in combined predictions')
        write_table(stage / 'candidate_predictions.csv', merged)
        git_source = source_snapshot(stage)
        combined = stage / 'candidate_predictions.csv'
        payload = {
            'handoff_version': 'v1.2', 'frozen_model_release': 'v1',
            'selected_spec': old['selected_spec'], 'selection': old['selection'],
            'model_training': old['model_training'], 'formula': old['formula'], 'feature_order': old['features'],
            'primary_pools': {'Q2': '07', 'Q3': '08'}, 'blind_alternatives': {'Q2': '11', 'Q3': '12'},
            'inputs': old['inputs'], 'score_columns': NEW_FIELDS,
            'pool_alias': 'pool and source_pool are equal. String pool code retains leading zero.',
            'models': {path: old['artifacts_sha256'][path]
                       for path in ('models/q1_final.joblib', 'models/q23_final.joblib')},
            'frozen_root': 'handoff/v1', 'frozen_manifest_sha256': sha256(FROZEN / 'manifest.json'),
            'experiment_root': 'experiments/q1_v12', 'experiment_config_sha256': sha256(SUPPLEMENT / 'run_config.json'),
            'planning_file': PLAN.name, 'planning_sha256': sha256(PLAN), 'source_snapshot': git_source,
            'export_root': out.relative_to(ROOT).as_posix() if out.is_relative_to(ROOT) else str(out),
            'outputs': pools, 'combined_output': {'file': combined.name, 'rows': len(merged),
                                                    'sha256': sha256(combined)},
            'review_status': {'local_program_checks': 'see audit/v12_acceptance.json',
                              'independent_team_member_and_QUBO_signoff': 'pending human review',
                              'official_04_submission_fields': 'pending logged-in contest portal verification'},
        }
        write_json(stage / 'manifest.json', payload)
        stage.rename(out)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open('xb') as handle:
        handle.write((out / 'manifest.json').read_bytes())
    print(f'Published {len(merged):,} Q2/Q3 rows and a separate 04 file. Git source commit {git_source["commit"]}.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, default=EXPORT)
    parser.add_argument('--manifest', type=Path, default=MANIFEST)
    args = parser.parse_args()
    out, manifest = args.out_dir.resolve(), args.manifest.resolve()
    if out.exists() or manifest.exists() or out in manifest.parents:
        parser.error('Choose a fresh output directory and a fresh external manifest path.')
    build(out, manifest)


if __name__ == '__main__':
    main()
