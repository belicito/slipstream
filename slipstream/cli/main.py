import os
import sys
from argparse import ArgumentParser
from .trades import show_trades, summarize_trades


def main():
    ap = ArgumentParser(
        prog="slipstream",
    )
    ap.add_argument("--show-trades", dest="show_trades", metavar="<trades file>", nargs=1)
    ap.add_argument("--summarize-trades", dest="summarize_trades", metavar="<trades file>", nargs=1)
    args = ap.parse_args()
    
    if args.show_trades is not None:
        file = args.show_trades[0]
        show_trades(file)
    elif args.summarize_trades is not None:
        file = args.summarize_trades[0]
        summarize_trades(file)
