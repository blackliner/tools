#!/usr/bin/env python3
"""This script checks if your current ccache setup works with conan."""
import argparse
import logging
import subprocess
from typing import Any, List
from pathlib import Path

def stats_to_dict(raw_string: str):
    separated = [line.split(sep="  ") for line in raw_string.splitlines()]
    return_value = dict()
    for line in separated:
        key = line[0].strip()
        value = line[-1].strip()
        value = int(value) if value.isdigit() else value
        return_value[key] = value
    return return_value

def check(command: List[Any]) -> str:
    if isinstance(command, str):
        command = command.split()
    logging.info("Executing: " + " ".join(str(x) for x in command))
    try:
        return subprocess.check_output(command, stderr=subprocess.STDOUT).decode("utf-8")
    except subprocess.CalledProcessError as error:
        print(error.output.decode("utf-8"))
        raise

def read_stats() -> dict:
    return stats_to_dict(check("ccache --show-stats"))

def reset_ccache() -> None:
    check("ccache --clear --zero-stats")

def sign(value: int) -> str:
    return "+" if value >= 0 else "-"

def report_stats(stats: dict) -> None:
    chd = stats["cache hit (direct)"]
    cm = stats["cache miss"]
    logging.info(f"cache hit (direct):       {chd}")
    logging.info(f"cache miss:               {cm}")

def report_delta(stats_before: dict, stats_after: dict) -> None:
    chd_delta = stats_after["cache hit (direct)"] - stats_before["cache hit (direct)"]
    cm_delta = stats_after["cache miss"] - stats_before["cache miss"]
    logging.info(f"cache hit (direct):       {sign(chd_delta)}{chd_delta}")
    logging.info(f"cache miss:               {sign(cm_delta)}{cm_delta}")

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(description="Check if ccache works with conan")
    parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
    parser.add_argument("PACKAGE", help="conan package used to run checks", type=Path)
    args = parser.parse_args()

    try:
        reset_ccache()
    except subprocess.SubprocessError:
        logging.error("clearing ccache cache not possible")
        return
    
    stats_0 = read_stats()
    report_stats(stats_0)

    check(f"conan create {args.PACKAGE} -s build_type=Release -o *:with_tests=True")
    stats_1 = read_stats()
    report_delta(stats_0, stats_1)

    check(f"conan create {args.PACKAGE} -s build_type=Release -o *:with_tests=False")
    stats_2 = read_stats()
    report_delta(stats_1, stats_2)

    check(f"conan create {args.PACKAGE} -s build_type=Debug -o *:with_tests=True")
    stats_3 = read_stats()
    report_delta(stats_2, stats_3)

    check(f"conan create {args.PACKAGE} -s build_type=Release -o *:with_tests=True")
    stats_4 = read_stats()
    report_delta(stats_3, stats_4)

if __name__ == "__main__":
    main()

