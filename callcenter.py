"""
This example connects to the specified AMI hosts and prints a message when an
account is ringing and when a call is transferred.
"""
from cacofonisk import AmiRunner, BaseReporter


class TransferSpammer(BaseReporter):
    def on_b_dial(self, call_id, caller, to_number, targets):
        callee_codes = [target.code for target in targets]
        caller_number = caller.number
        print("{} is now ringing {} on number {}".format( caller_number, ', '.join('%s'%code for code in callee_codes), to_number))

    def on_up(self, call_id, caller, to_number, callee):
        callee_account_code = callee.code
        caller_number = caller.number
        print("{} is now in conversation with {}".format(caller_number, callee_account_code))

    def on_warm_transfer(self, call_id, merged_id, redirector, caller, destination):
        print('{} is now calling with {} (was calling {})'.format(caller, destination, redirector))

    def on_cold_transfer(self, call_id, merged_id, redirector, caller, to_number, targets):
        print('{} tried to transfer the call from {} to number {} (ringing {})'.format(
            redirector, caller, to_number, ', '.join(targets),
        ))

    def on_hangup(self, call_id, caller, to_number, reason):
        print("{} is no longer calling number {} (reason: {})".format(caller, to_number, reason))

if __name__ == '__main__':
    ami_host1 = {'host': '192.168.11.65', 'username': 'admin', 'password': 'admin', 'port': 5038}
    ami_hosts = (ami_host1,)

    reporter = TransferSpammer()
    runner = AmiRunner(ami_hosts, reporter)
    runner.run()
