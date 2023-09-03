import os
import pandas as pd
from slipstream.trading.analysis import TradesAnalysis
import typer

app = typer.Typer()


@app.command()
def show(file: str):
    assert os.path.exists(file), f"File not found: {file}"
    trades = pd.read_csv(file)
    print(file, "trades:", trades.shape)

    # TODO: format the display of fields


@app.command()
def summarize(file: str):
    assert os.path.exists(file), f"File not found: {file}"
    analysis = TradesAnalysis(file)
    summary = analysis.summary()
    max_field_width = max(len(k) for k in summary.keys())
    k_fmt_str = f"%{max_field_width + 1}s"
    for k, v in summary.items():
        print(k_fmt_str % k, ":", v)
