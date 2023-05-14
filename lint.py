import argparse
import logging
from pylint.lint import Run


logging.getLogger().setLevel(logging.INFO)
parser = argparse.ArgumentParser(prog="LINT")

parser.add_argument(
    "-p",
    "--path",
    help="path to directory you want to run pylint | "
    "Default: %(default)s | "
    "Type: %(type)s ",
    default="./src",
    type=str,
)
parser.add_argument(
    "-t",
    "--threshold",
    help="score threshold to fail pylint runner | "
    "Default: %(default)s | "
    "Type: %(type)s ",
    default=7,
    type=float,
)

args = parser.parse_args()
path = str(args.path)
threshold = float(args.threshold)

logging.info(f"PyLint Starting | Path: {path} | Threshold: {threshold}")

results = Run([path], do_exit=False)
final_score = results.linter.stats["global_note"]

if final_score < threshold:

    message = f"PyLint Failed | Score: {final_score} | Threshold: {threshold}"
    logging.error(message)
    raise Exception(message)

else:

    message = f"PyLint Passed | Score: {final_score} | Threshold: {threshold}"
    logging.info(message)
    exit(0)
