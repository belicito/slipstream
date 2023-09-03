import os
import sys
from slipstream.cli.trades import app as trades_app
from slipstream.cli.bento import app as bento_app
import typer


app = typer.Typer()
app.add_typer(bento_app, name="bento")
app.add_typer(trades_app, name="trades")


def main():
    app()


if __name__ == "__main__":
    main()
