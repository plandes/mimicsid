#!/usr/bin/env python

from zensols import deepnlp


# initialize the NLP system
deepnlp.init()


# command line entry point
if (__name__ == '__main__'):
    from zensols.cli import CliHarness
    harness = CliHarness(
        src_dir_name='src',
        app_factory_class='zensols.mimicsid.ApplicationFactory',
        proto_args='proto -c config/glove300.conf',
        proto_factory_kwargs={
            'reload_pattern': r'^zensols.mimicsid.(?!domain)'},
    )
    result = harness.run()
