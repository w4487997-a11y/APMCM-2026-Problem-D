"""Score a composition-only CSV using a trusted local final joblib bundle."""

import argparse
from pathlib import Path

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

from audit.init_check import COMPOSITION, read_csv
from q1.baselines import write_table
from q1.delivery import scored_rows
from q1.experiments import composition


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-pool', required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a new output path.')
    fields, rows = read_csv(args.input)
    if fields != COMPOSITION or not rows or len({row['id'] for row in rows}) != len(rows):
        parser.error('Input must contain the official six composition columns and unique IDs.')

    bundle = joblib.load(args.model)
    with threadpool_limits(limits=1):
        values = bundle['model'].predict(composition(rows))
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError('Model generated invalid scores.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    lookup = {row['id']: value for row, value in zip(rows, values)}
    write_table(args.output, scored_rows(rows, lookup, bundle['version'], args.source_pool))


if __name__ == '__main__':
    main()
