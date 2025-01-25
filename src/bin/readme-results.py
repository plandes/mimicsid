#!/usr/bin/env python

from typing import Iterable, Dict
from dataclasses import dataclass, field
import sys
import re
from pathlib import Path
from io import TextIOBase
import pandas as pd
from tabulate import tabulate
from zensols.config import Dictable


@dataclass
class ResultSummarizer(Dictable):
    result_path: Path = field()

    def _to_readme_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        type_re: re.Pattern = re.compile(
            r'^(.+) (Header|Section)(?: Type)?: 1$')
        cols: Dict[str, str] = {
            'name': 'Name',
            'type': 'Type',
            'resid': 'Id',
            'wF1v': 'wF1',
            'mF1v': 'mF1',
            'MF1v': 'MF1',
            'accv': 'acc'
        }
        for col in 'wF1v mF1v MF1v accv'.split():
            df[col] = df[col].round(3)
        df['resid'] = df['resid'].apply(
            lambda s: re.sub(r'^(.+)-1$', r'\1', s))
        #type_ser: pd.Series = df['name'].apply(
        df['type'] = df['name'].apply(
            lambda s: re.sub(type_re, r'\2', s))
        df['name'] = df['name'].apply(
            lambda s: re.sub(type_re, r"`\1`", s))
        #df.insert(0, 'type', type_ser)
        df = df.sort_values('type name'.split(), ascending=False)
        df = df[list(cols.keys())]
        df = df.rename(columns=cols)
        return df

    def _to_readme_table(self, df: pd.DataFrame) -> str:
        tab: str = tabulate(
            df,
            headers=df.columns,
            tablefmt='orgtbl',
            showindex=False)
        return tab.replace('+', '|')

    def write(self, depth: int = 0, writer: TextIOBase = sys.stdout):
        res_paths: Iterable[Path] = filter(
            lambda p: p.suffix == '.csv', self.result_path.iterdir())
        for path in res_paths:
            df: pd.DataFrame = pd.read_csv(path, index_col=0)
            df = self._to_readme_dataframe(df)
            self._write_line(f'{path}:', depth, writer)
            self._write_block(self._to_readme_table(df), depth, writer)
            self._write_divider(depth, writer)


def main():
    summarizer = ResultSummarizer(Path('stage'))
    summarizer.write()


if (__name__ == '__main__'):
    main()
