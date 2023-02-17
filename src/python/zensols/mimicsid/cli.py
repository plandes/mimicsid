"""Command line entry point to the application.

"""
__author__ = 'Paul Landes'

from typing import List, Any, Dict
import sys
from zensols.config import ConfigFactory
from zensols.mimic import Corpus
from zensols.cli import ActionResult, CliHarness
from zensols.cli import ApplicationFactory as CliApplicationFactory
from . import SectionPredictor, NoteStash, AnnotationResource


class ApplicationFactory(CliApplicationFactory):
    """The application factory for section identification.

    """
    def __init__(self, *args, **kwargs):
        kwargs['package_resource'] = 'zensols.mimicsid'
        super().__init__(*args, **kwargs)

    @classmethod
    def instance(cls, name: str) -> ConfigFactory:
        """Return the section predictor using the app context."""
        harness: CliHarness = cls.create_harness()
        fac: ConfigFactory = harness.get_config_factory()
        return fac(name)

    @classmethod
    def corpus(cls) -> Corpus:
        """Return the section predictor using the app context."""
        return cls.instance('mimic_corpus')

    @classmethod
    def section_predictor(cls) -> SectionPredictor:
        """Return the section predictor using the app context."""
        return cls.instance('mimicsid_section_predictor')

    @classmethod
    def annotation_resource(cls) -> AnnotationResource:
        """Contains resources to acces the MIMIC-III MedSecId annotations."""
        return cls.instance('mimicsid_anon_resource')

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
