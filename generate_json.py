from cacofonisk import AmiRunner, JsonReporter
from cacofonisk.channel import DebugChannelManager

reporter = JsonReporter('tests/fixtures/xfer_blind/xfer_blind_reject.json')
runner = AmiRunner([
    {'host': '172.20.0.12', 'username': 'cacofonisk', 'password': 'bard', 'port': 5038},
], reporter, channel_manager=DebugChannelManager)
runner.run()
