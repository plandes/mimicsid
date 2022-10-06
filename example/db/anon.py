#!/usr/bin/env python

"""An example to show how to  use the MedSecId annotations.  This examples shows
how to use  the Zensols CLI API  to create an application  context, which allows
customization of the environment.

Note this example takes a while to run the first time (~5 min).  This is because
it preemptively creates the admissions cache, which covers all those admissions
that were annotated by at least one note (1,061 admission).  After running it
once it is quick, which is why it is important to set the
``mimicsid_default:shared_data_dir`` configuration section/option.

"""
__author__ = 'Paul Landes'

from dataclasses import dataclass
import logging
from io import StringIO
from zensols.cli import CliHarness, ProgramNameConfigurator
from zensols.mimic import Note
from zensols.mimicsid import NoteStash

logger = logging.getLogger(__name__)

CONFIG = """
[cli]
apps = list: log_cli, app

[log_cli]
class_name = zensols.cli.LogConfigurator
format = ${program:name}: %%(message)s
log_name = ${program:name}
level = debug

[mimicsid_default]
embedding = glove_300_embedding

[import]
sections = list: pkg_imp

[pkg_imp]
type = import
config_files = list:
  resource(zensols.mimicsid): resources/pkg/all.conf,
  path: ./db.conf


[app]
class_name = ${program:name}.Application
note_stash = instance: mimicsid_note_stash
"""


@dataclass
class Application(object):
    """An example to show how to use the MedSecId annotations and model.

    """
    note_stash: NoteStash

    def write_note(self, row_id: int = 14793):
        """Write an admission, note or section.

        :param row_id: the row ID of the note to write

        """
        row_id = str(row_id)
        note: Note = self.note_stash[row_id]
        note.write_human()


if (__name__ == '__main__'):
    CliHarness(
        app_config_resource=StringIO(CONFIG),
        app_config_context=ProgramNameConfigurator(
            None, default='anon').create_section(),
        proto_args='',
        proto_factory_kwargs={'reload_pattern': '^anon'},
    ).run()
