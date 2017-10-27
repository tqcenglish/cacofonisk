from datetime import datetime
import sys

from cacofonisk import AmiRunner, BaseReporter
from cacofonisk.channel import DebugChannelManager


class DebugReporter(BaseReporter):

    def trace_ami(self, event):
        sys.stdout.write('{}: {}\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), event))
        sys.stdout.flush()


reporter = DebugReporter()
runner = AmiRunner([
    # {'host': '127.0.0.1', 'username': 'cacofonisk', 'password': 'bard', 'port': 5039},
    {'host': '172.20.0.12', 'username': 'cacofonisk', 'password': 'bard', 'port': 5038},
], reporter, DebugChannelManager)
runner.run()
