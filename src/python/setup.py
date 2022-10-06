from pathlib import Path
from zensols.pybuild import SetupUtil

su = SetupUtil(
    setup_path=Path(__file__).parent.absolute(),
    name="zensols.mimicsid",
    package_names=['zensols', 'resources'],
    package_data={'': ['*.conf', '*.json', '*.yml']},
    description='Use the MedSecId section annotations with MIMIC-III corpus parsing.',
    user='plandes',
    project='mimicsid',
    keywords=['tooling'],
    # has_entry_points=False,
).setup()
