"""Command line entry point to the application.

"""
__author__ = 'Paul Landes'

from typing import List, Any, Dict
import sys
from zensols.cli import ActionResult, CliHarness
from zensols.cli import ApplicationFactory as CliApplicationFactory
from . import SectionPredictor, NoteStash


class ApplicationFactory(CliApplicationFactory):
    """The application factory for section identification.

    """
    def __init__(self, *args, **kwargs):
        kwargs['package_resource'] = 'zensols.mimicsid'
        super().__init__(*args, **kwargs)

    @classmethod
    def section_predictor(cls) -> SectionPredictor:
        """Return the section predictor using the app context."""
        harness: CliHarness = cls.create_harness()
        return harness.get_instance('predict').section_predictor

    @classmethod
    def note_stash(cls, host: str, port: str, db_name: str,
                   user: str, password: str) -> NoteStash:
        """Return the note stash using the app context, which is populated with
        the Postgres DB login provided as the parameters.

        """
        harness: CliHarness = cls.create_harness(
            app_config_context={
                'mimic_postgres_conn_manager':
                dict(host=host, port=port, db_name=db_name,
                     user=user, password=password)})
        return harness.get_instance('note').note_stash


def main(args: List[str] = sys.argv, **kwargs: Dict[str, Any]) -> ActionResult:
    harness: CliHarness = ApplicationFactory.create_harness(relocate=False)
    harness.invoke(args, **kwargs)
