#!/usr/bin/env python

"""An example to show how to predict sections using the MedSecId pretrained
model.  This example shows how to create a Zenols application with a context,
which allows you to customize the behavior of the prediction.

"""
__author__ = 'Paul Landes'

from dataclasses import dataclass
import logging
from io import StringIO
from pathlib import Path
from zensols.cli import CliHarness, ProgramNameConfigurator
from zensols.mimicsid import PredictedNote
from zensols.mimicsid.pred import SectionPredictor

logger = logging.getLogger(__name__)

CONFIG = """
[cli]
apps = list: log_cli, app

[log_cli]
class_name = zensols.cli.LogConfigurator
format = ${program:name}: %%(message)s
log_name = ${program:name}
level = debug

[import]
config_file = resource(zensols.mimicsid): resources/model/pkg/all.conf

[app]
class_name = ${program:name}.Application
section_predictor = instance: mimicsid_section_predictor
"""


@dataclass
class Application(object):
    """An example to show how to use the MedSecId annotations and model.

    """
    section_predictor: SectionPredictor

    def predict(self, infile: Path = Path('../../test-resources/note.txt')):
        """Identify sections of a medical note.

        :param infile: the note to section

        """
        logger.info(f'sectioning {infile}')
        with open(infile) as f:
            content = f.read()
        note: PredictedNote = self.section_predictor.predict([content])[0]
        note.write_human()


if (__name__ == '__main__'):
    CliHarness(
        app_config_resource=StringIO(CONFIG),
        app_config_context=ProgramNameConfigurator(
            None, default='section').create_section(),
        proto_args='',
        proto_factory_kwargs={'reload_pattern': '^section'},
    ).run()
