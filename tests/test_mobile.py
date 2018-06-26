from cacofonisk.callerid import CallerId
from .replaytest import ChannelEventsTestCase


class TestMobile(ChannelEventsTestCase):

    def test_simple_mobile(self):
        """
        Test a call from external which is routed to another number.
        """
        events_file = 'fixtures/mobile/simple_mobile.json'
        events = self.run_and_get_events(events_file)

        caller = CallerId(code=15001, number='+31150010001')
        target = CallerId(code=15001, number='+31260010001')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': 'f29ea68048f6-1530017224.892',
                'caller': caller,
                'to_number': '+31150010004',
                'targets': [target],
            }),
            ('on_up', {
                'call_id': 'f29ea68048f6-1530017224.892',
                'caller': caller,
                'to_number': '+31150010004',
                'target': target,
            }),
            ('on_hangup', {
                'call_id': 'f29ea68048f6-1530017224.892',
                'caller': caller,
                'to_number': '+31150010004',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_acceptance_simple(self):
        """
        Test a call routed to another number with call acceptance.

        Call Acceptance is a feature where the called channel first needs to
        complete a DTMF challenge in order to verify the call was picked up by
        a human (and not voicemail).
        """
        events_file = 'fixtures/mobile/acceptance_simple.json'
        events = self.run_and_get_events(events_file)

        call_id = 'f29ea68048f6-1530017933.1232'
        caller = CallerId(code=15001, number='+31150010001')
        target = CallerId(code=15001, number='+31260010001')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': call_id,
                'caller': caller,
                'to_number': '+31150010004',
                'targets': [target],
            }),
            ('on_up', {
                'call_id': call_id,
                'caller': caller,
                'to_number': '+31150010004',
                'target': target,
            }),
            ('on_hangup', {
                'call_id': call_id,
                'caller': caller,
                'to_number': '+31150010004',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_acceptance_reject(self):
        """
        Test call acceptance where target does not accept call.
        """
        events_file = 'fixtures/mobile/acceptance_reject.json'
        events = self.run_and_get_events(events_file)

        call_id = 'f29ea68048f6-1530020018.1761'
        caller = CallerId(code=26001, number='+31150010003')
        target = CallerId(code=26001, number='+31150010001')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': call_id,
                'caller': caller,
                'to_number': '+31260010001',
                'targets': [target],
            }),
            ('on_hangup', {
                'call_id': call_id,
                'caller': caller,
                'to_number': '+31260010001',
                'reason': 'no-answer',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_acceptance_group_pickup(self):
        """
        Test call acceptance to group with call acceptance and timeout.

        In this example, both targets are picked up, but only one can complete
        call confirmation. The other target is hanged up by Asterisk.
        """
        events_file = 'fixtures/mobile/acceptance_group_pickup.json'
        events = self.run_and_get_events(events_file)

        call_id = 'f29ea68048f6-1530020288.1855'
        caller = CallerId(code=26001, number='+31150010003')
        target_one = CallerId(code=26001, number='+31150010001')
        target_two = CallerId(code=26001, number='+31150010002')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': call_id,
                'caller': caller,
                'to_number': '+31260010001',
                'targets': [target_one, target_two],
            }),
            ('on_up', {
                'call_id': call_id,
                'caller': caller,
                'to_number': '+31260010001',
                'target': target_one,
            }),
            ('on_hangup', {
                'call_id': call_id,
                'caller': caller,
                'to_number': '+31260010001',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_acceptance_group_reject(self):
        """
        Test call acceptance to a group with call acceptance and reject.
        """
        events_file = 'fixtures/mobile/acceptance_group_reject.json'
        events = self.run_and_get_events(events_file)

        call_id = 'f29ea68048f6-1530020779.2044'
        caller = CallerId(code=26001, number='+31150010003')
        target_one = CallerId(code=26001, number='+31150010001')
        target_two = CallerId(code=26001, number='+31150010002')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': call_id,
                'caller': caller,
                'to_number': '+31260010001',
                'targets': [target_one, target_two],
            }),
            ('on_up', {
                'call_id': call_id,
                'caller': caller,
                'to_number': '+31260010001',
                'target': target_one,
            }),
            ('on_hangup', {
                'call_id': call_id,
                'caller': caller,
                'to_number': '+31260010001',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_acceptance_timeout(self):
        """
        Test call acceptance to a group with call acceptance and reject.
        """
        events_file = 'fixtures/mobile/acceptance_timeout.json'
        events = self.run_and_get_events(events_file)

        call_id = 'f29ea68048f6-1530021414.2233'
        caller = CallerId(code=26001, number='+31150010003')
        target = CallerId(code=26001, number='+31150010001')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': call_id,
                'caller': caller,
                'to_number': '+31260010001',
                'targets': [target],
            }),
            ('on_hangup', {
                'call_id': call_id,
                'caller': caller,
                'to_number': '+31260010001',
                'reason': 'no-answer',
            }),
        ))

        self.assertEqual(expected_events, events)
