from typing import Set
import unittest
from pathlib import Path
import zensols.mimicsid
from zensols.mimicsid import PredictedNote, ApplicationFactory
from zensols.mimicsid.pred import SectionPredictor


class TestParse(unittest.TestCase):
    def setUp(self):
        zensols.mimicsid._silence_zennlp_parser_warnings()
        self.maxDiff = 999999

    def test_parse(self):
        write: bool = False
        should_path: Path = Path('test-resources/should-section.txt')
        note_path: Path = Path('test-resources/note.txt')
        compare_section: str = 'history-of-present-illness'
        section_predictor: SectionPredictor = \
            ApplicationFactory.section_predictor()
        with open(note_path) as f:
            content = f.read()
        note: PredictedNote = section_predictor.predict([content])[0]
        if write:
            print()
            note.write_human()
        self.assertTrue(isinstance(note, PredictedNote))
        sections: Set[str] = set(note.sections_by_name.keys())
        self.assertTrue(len(sections) > 0)
        if not write:
            self.assertTrue(compare_section in sections)
        body_text: str = note.sections_by_name[compare_section][0].body
        if write:
            with open(should_path, 'w') as f:
                f.write(body_text)
        with open(should_path) as f:
            should: str = f.read().strip()
        self.assertEqual(should, body_text)
