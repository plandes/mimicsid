from typing import Dict, Any, List
import unittest
import yaml
import zensols.mimicsid
from zensols.mimicsid import PredictedNote, ApplicationFactory, Section
from zensols.mimicsid.pred import SectionPredictor


class TestParse(unittest.TestCase):
    def setUp(self):
        zensols.mimicsid._silence_zennlp_parser_warnings()
        self.maxDiff = 999999

    def test_parse(self):
        write: bool = False
        section_predictor: SectionPredictor = \
            ApplicationFactory.section_predictor()
        with open('test-resources/should-section.yml') as f:
            should: Dict[str, Any] = yaml.load(f, yaml.FullLoader)
        with open('test-resources/note.txt') as f:
            content: str = f.read()
        note: PredictedNote = section_predictor.predict([content])[0]
        if write:
            print()
            note.write_human()
        self.assertTrue(isinstance(note, PredictedNote))
        should_secs: Dict[str, str] = should['sections']
        should_heads: List[str] = should['headers']
        self.assertEqual(len(should_secs), len(note.sections_by_name))
        name: str
        content: str
        headers: List[str]
        for (name, content), headers in zip(should_secs.items(), should_heads):
            self.assertTrue(name in note.sections_by_name, f'missing {name}')
            self.assertEqual(1, len(note.sections_by_name[name]))
            sec: Section = note.sections_by_name[name][0]
            self.assertEqual(sec.body, content.strip())
            self.assertEqual(sec.headers, tuple(headers))
