import os
import sys
from slipstream.cli.trades import app as trades_app
import typer


app = typer.Typer()
app.add_typer(trades_app, name="trades")


def main():
    app()


if __name__ == "__main__":
    main()
