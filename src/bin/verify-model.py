#!/usr/bin/env python

from typing import Dict, Any
import torch
from pathlib import Path
from zensols.config import ConfigFactory, Configurable
from zensols.deeplearn.result import ModelResult


def check_config(config: Configurable):
    config['uts'].write()
    config['mimic_db'].write()
    assert config['uts']['api_key'] == 'NOT_SET'
    assert config['mimic_db']['password'] == 'PASSWORD_NOT_SET'


def verify_model(mdir: Path):
    data: Dict[str, Any] = torch.load(mdir / 'state.pt')
    if 0:
        for k, v in data.items():
            print(k, type(v))
    config_factory: ConfigFactory = data['config_factory']
    config: Configurable = config_factory.config
    res: ModelResult = data['model_result']
    res_config: Configurable = res.config
    check_config(config)
    check_config(res_config)
    if 0:
        data: Dict[str, Any] = torch.load(mdir / 'weight.pt')
        print(type(data))
        print(data.keys())
        for k, v in data['model_state_dict'].items():
            print(k, type(v))


def main():
    models: int = 0
    mdirs = Path('model/results/model')
    for mdir in filter(lambda p: p.name.endswith('model'), mdirs.iterdir()):
        print(f'verifying: {mdir}')
        verify_model(mdir)
        print(f'{mdir.name}: clear')
        print('_' * 80)
        models += 1
    assert models == 4
    print(f'verified {models} models: OK')


if (__name__ == '__main__'):
    main()
