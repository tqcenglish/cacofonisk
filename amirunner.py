from cacofonisk import AmiRunner, DebugReporter
from cacofonisk.channel import DebugChannelManager

reporter = DebugReporter()
# To attach the AmiRunner
runner = AmiRunner([
    {'host': '172.20.0.12', 'username': 'cacofonisk', 'password': 'bard', 'port': 5038},
], reporter)
# runner = FileRunner('tests/examples/Response302XferManual.replay.json', reporter)
runner.run()
