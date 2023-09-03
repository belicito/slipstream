import os
import pandas as pd
import re
import shutil
from slipstream.trading.analysis import TradesAnalysis
import s3fs
import tempfile
import typer
import uuid
import zstd

app = typer.Typer()


def _fetch_s3_file(s3_path: str, local_path: str = None, overwrite_ok: bool = True) -> str:
    s3 = s3fs.S3FileSystem()
    with s3.open(s3_path, "rb") as f:
        trades_data = f.read()
    tags = s3.get_tags(s3_path)
    if tags.get("compression", "") == "zstd":
        trades_data = zstd.decompress(trades_data)

    if local_path is None:
        _, filename = os.path.split(s3_path)
        local_path = os.path.join("/tmp", filename)
    if os.path.exists(local_path):
        if overwrite_ok:
            os.remove(local_path)
        else:
            raise FileExistsError(local_path)

    with open(local_path, "wb+") as f:
        f.write(trades_data)
    return local_path


@app.command()
def show(file: str):
    m = re.match("s3://(.*)", file)
    if m is not None:
        s3_path = m.group(1)
        file = _fetch_s3_file(s3_path)

    assert os.path.exists(file), f"File not found: {file}"
    trades = pd.read_csv(file)
    print(file, "trades:", trades.shape)

    # TODO: format the display of fields


@app.command()
def summarize(file: str):
    m = re.match("s3://(.*)", file)
    if m is not None:
        s3_path = m.group(1)
        file = _fetch_s3_file(s3_path)

    assert os.path.exists(file), f"File not found: {file}"
    analysis = TradesAnalysis(file)
    summary = analysis.summary()
    max_field_width = max(len(k) for k in summary.keys())
    k_fmt_str = f"%{max_field_width + 1}s"
    for k, v in summary.items():
        print(k_fmt_str % k, ":", v)
