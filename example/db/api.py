#!/usr/bin/env python

"""An example to show how to use the MedSecId annotations.  This example uses
the Zensols API to create and use an object oriented way of accessing annotated
data as :class:`~zensols.mimic.Note` instances.

Note this example takes a while to run the first time (~5 min).  This is because
it preemptively creates the admissions cache, which covers all those admissions
that were annotated by at least one note (1,061 admissions).  After running it
once it is quick, which is why it is important to set the
``mimicsid_default:shared_data_dir`` configuration section/option.

"""
__author__ = 'Paul Landes'

from zensols.config import IniConfig
from zensols.mimic import Section
from zensols.mimicsid import ApplicationFactory
from zensols.mimic import Note
from zensols.mimicsid import AnnotatedNote, NoteStash


if (__name__ == '__main__'):
    # create a configuration with the Postgres database login
    config = IniConfig('db.conf')
    # get the `dict` like data structure that has notes by `row_id`
    note_stash: NoteStash = ApplicationFactory.note_stash(
        **config.get_options(section='mimic_postgres_conn_manager'))

    # get a note by `row_id`
    note: Note = note_stash[14793]
    # if the row_id specifies a note that was annotated, we'll get an
    # `AnnotatedNote` note instance, otherwise we'll get a `Note`
    assert isinstance(note, AnnotatedNote)
    # output the note in a friendly human readable format
    note.write_human()

    # iterate through the note object graph
    sec: Section
    for sec in note.sections.values():
        print(sec.id, sec.name)
