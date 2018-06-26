from cacofonisk.callerid import CallerId
from .replaytest import ChannelEventsTestCase


class TestQueue(ChannelEventsTestCase):

    def test_queue_simple(self):
        """
        Test a simple call through a queue to a single account.
        """
        fixture_file = 'fixtures/queue/queue_simple.json'
        events = self.run_and_get_events(fixture_file)

        call_id = '195176c06ab8-1529939196.518'
        caller = CallerId(code=15001, number='+31150010001')
        target = CallerId(code=150010002, number='+31150010004')

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

    def test_queue_group(self):
        """
        Test a simple call through a queue to a group.
        """
        fixture_file = 'fixtures/queue/queue_group.json'
        events = self.run_and_get_events(fixture_file)

        call_id = '195176c06ab8-1529938920.367'
        caller = CallerId(code=15001, number='+31150010001')
        target = CallerId(code=150010002, number='+31150010004')
        target_2 = CallerId(code=150010003, number='+31150010004')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': call_id,
                'caller': caller,
                'to_number': '+31150010004',
                'targets': [target, target_2],
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

    def test_queue_a_cancel(self):
        """
        Test a call where A exits the queue before B can pick up.
        """
        events = self.run_and_get_events('fixtures/queue/queue_a_cancel.json')

        call_id = '195176c06ab8-1529939079.449'
        caller = CallerId(code=15001, number='+31150010001')
        target = CallerId(code=150010002, number='+31150010004')
        target_2 = CallerId(code=150010003, number='+31150010004')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': call_id,
                'caller': caller,
                'to_number': '+31150010004',
                'targets': [target, target_2],
            }),
            ('on_hangup', {
                'call_id': call_id,
                'caller': caller,
                'to_number': '+31150010004',
                # FIXME this is wrong, should be cancelled.
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_queue_attn_xfer(self):
        """
        Test an attended transfer with someone coming through a queue.
        """
        events = self.run_and_get_events('fixtures/queue/queue_attn_xfer.json')

        call_id_one = 'f29ea68048f6-1530022819.2433'
        call_id_two = 'f29ea68048f6-1530022836.2474'
        a_party = CallerId(code=15001, number='+31260010001')
        b_party_called = CallerId(code=150010001, number='+31150010001')
        b_party_calling = CallerId(code=150010001, name='Andrew Garza',
                                   number='201')
        c_party = CallerId(code=150010002, number='202')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '+31150010001',
                'targets': [b_party_called],
            }),
            ('on_up', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '+31150010001',
                'target': b_party_called,
            }),
            ('on_b_dial', {
                'call_id': call_id_two,
                'caller': b_party_calling,
                'to_number': '202',
                'targets': [c_party],
            }),
            ('on_up', {
                'call_id': call_id_two,
                'caller': b_party_calling,
                'to_number': '202',
                'target': c_party,
            }),
            ('on_attended_transfer', {
                'new_id': call_id_one,
                'merged_id': call_id_two,
                'caller': a_party,
                'redirector': b_party_calling,
                'target': c_party,
            }),
            ('on_hangup', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '+31150010001',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_queue_blind_xfer(self):
        """
        Test a blind transfer with someone from a queue.
        """
        events = self.run_and_get_events('fixtures/queue/queue_blind_xfer.json')

        call_id_one = 'f29ea68048f6-1530023464.2539'
        call_id_two = 'f29ea68048f6-1530023472.2593'
        a_party = CallerId(code=15001, number='+31260010001')
        b_party = CallerId(code=150010001, number='+31150010001')
        c_party = CallerId(code=150010002, number='202')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '+31150010001',
                'targets': [b_party],
            }),
            ('on_up', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '+31150010001',
                'target': b_party,
            }),
            ('on_b_dial', {
                'call_id': call_id_two,
                'caller': b_party,
                'to_number': '202',
                'targets': [c_party],
            }),
            ('on_cold_transfer', {
                'new_id': call_id_one,
                'merged_id': call_id_two,
                'caller': a_party,
                'redirector': b_party,
                'targets': [c_party],
                'to_number': '202',
            }),
            ('on_up', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '202',
                'target': c_party,
            }),
            ('on_hangup', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '202',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)
