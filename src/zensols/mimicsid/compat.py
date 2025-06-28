"""Add configured properties that were remove from
:class:`.zensols.mednlp.resource.MedCatResource` starting in version 1.9.0.

"""
__author__ = 'Paul Landes'

from zensols.mednlp import MedCatResource

_init_mednlp_180 = MedCatResource.__init__


def _init_mednlp_190(*args, **kwargs):
    for attr in 'auto_install_models requirements_dir'.split():
        kwargs.pop(attr, None)
    return _init_mednlp_180(*args, **kwargs)


MedCatResource.__init__ = _init_mednlp_190
