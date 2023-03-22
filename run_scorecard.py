import argparse
import json
import logging

from scorecard import Scorecard


def main() -> None:
    parser = argparse.ArgumentParser('Calculate Scorecard')
    parser.add_argument('scene_file', help='Scene file')
    parser.add_argument('history_file', help='History file')
    args = parser.parse_args()

    with open(args.scene_file) as scene_file:
        scene = json.load(scene_file)
    with open(args.history_file) as history_file:
        history = json.load(history_file)
    scorecard = Scorecard(history, scene)
    scores = scorecard.score_all()
    for key, value in scores.items():
        print(f'{key}: {value}')


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
