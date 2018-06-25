from cacofonisk.callerid import CallerId
from .replaytest import ChannelEventsTestCase


class TestQueue(ChannelEventsTestCase):

    def test_queue_simple(self):
        """
        Test a simple call through a queue to a single account.
        """
        fixture_file = 'fixtures/queue/queue_simple.json'
        events = self.run_and_get_events(fixture_file)

        outbound_caller = CallerId(code=150010001, number='+31150010001')
        outbound_target = CallerId(code=150010001, number='+31150010004')

        inbound_caller = CallerId(code=15001, number='+31150010001')
        inbound_target = CallerId(code=150010002, number='+31150010004')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': '195176c06ab8-1529939196.508',
                'caller': outbound_caller,
                'to_number': '0150010004',
                'targets': [outbound_target],
            }),
            ('on_up', {
                'call_id': '195176c06ab8-1529939196.508',
                'caller': outbound_caller,
                'to_number': '0150010004',
                'target': outbound_target,
            }),
            ('on_b_dial', {
                'call_id': '195176c06ab8-1529939196.518',
                'caller': inbound_caller,
                'to_number': '+31150010004',
                'targets': [inbound_target],
            }),
            ('on_up', {
                'call_id': '195176c06ab8-1529939196.518',
                'caller': inbound_caller,
                'to_number': '+31150010004',
                'target': inbound_target,
            }),
            ('on_hangup', {
                'call_id': '195176c06ab8-1529939196.518',
                'caller': inbound_caller,
                'to_number': '+31150010004',
                'reason': 'completed',
            }),
            ('on_hangup', {
                'call_id': '195176c06ab8-1529939196.508',
                'caller': outbound_caller,
                'to_number': '0150010004',
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

        outbound_caller = CallerId(code=150010001, number='+31150010001')
        outbound_target = CallerId(code=150010001, number='+31150010004')

        inbound_caller = CallerId(code=15001, number='+31150010001')
        inbound_target = CallerId(code=150010002, number='+31150010004')
        inbound_target_2 = CallerId(code=150010003, number='+31150010004')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': '195176c06ab8-1529938920.357',
                'caller': outbound_caller,
                'to_number': '0150010004',
                'targets': [outbound_target],
            }),
            ('on_up', {
                'call_id': '195176c06ab8-1529938920.357',
                'caller': outbound_caller,
                'to_number': '0150010004',
                'target': outbound_target,
            }),
            ('on_b_dial', {
                'call_id': '195176c06ab8-1529938920.367',
                'caller': inbound_caller,
                'to_number': '+31150010004',
                'targets': [inbound_target, inbound_target_2],
            }),
            ('on_up', {
                'call_id': '195176c06ab8-1529938920.367',
                'caller': inbound_caller,
                'to_number': '+31150010004',
                'target': inbound_target,
            }),
            ('on_hangup', {
                'call_id': '195176c06ab8-1529938920.367',
                'caller': inbound_caller,
                'to_number': '+31150010004',
                'reason': 'completed',
            }),
            ('on_hangup', {
                'call_id': '195176c06ab8-1529938920.357',
                'caller': outbound_caller,
                'to_number': '0150010004',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_queue_a_cancel(self):
        """
        Test a call where A exits the queue before B can pick up.
        """
        events = self.run_and_get_events('fixtures/queue/queue_a_cancel.json')

        outbound_caller = CallerId(code=150010001, number='+31150010001')
        outbound_target = CallerId(code=150010001, number='+31150010004')

        inbound_caller = CallerId(code=15001, number='+31150010001')
        inbound_target = CallerId(code=150010002, number='+31150010004')
        inbound_target_2 = CallerId(code=150010003, number='+31150010004')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': '195176c06ab8-1529939079.439',
                'caller': outbound_caller,
                'to_number': '0150010004',
                'targets': [outbound_target],
            }),
            ('on_up', {
                'call_id': '195176c06ab8-1529939079.439',
                'caller': outbound_caller,
                'to_number': '0150010004',
                'target': outbound_target,
            }),
            ('on_b_dial', {
                'call_id': '195176c06ab8-1529939079.449',
                'caller': inbound_caller,
                'to_number': '+31150010004',
                'targets': [inbound_target, inbound_target_2],
            }),
            ('on_hangup', {
                'call_id': '195176c06ab8-1529939079.439',
                'caller': outbound_caller,
                'to_number': '0150010004',
                'reason': 'completed',
            }),
            ('on_hangup', {
                'call_id': '195176c06ab8-1529939079.449',
                'caller': inbound_caller,
                'to_number': '+31150010004',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_queue_attn_xfer(self):
        """
        Test an attended transfer with someone coming through a queue.
        """
        events = self.run_and_get_events('fixtures/queue/queue_attn_xfer.json')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': 'e83df36bebbe-1507037906.116',
                'caller': CallerId(code=15001, number='+31150010001', is_public=True),
                'to_number': '+31150010004',
                'targets': [CallerId(code=150010002, number='+31150010004', is_public=True)],
            }),
            ('on_up', {
                'call_id': 'e83df36bebbe-1507037906.116',
                'caller': CallerId(code=15001, number='+31150010001', is_public=True),
                'to_number': '+31150010004',
                'callee': CallerId(code=150010002, number='+31150010004', is_public=True),
            }),
            ('on_b_dial', {
                'call_id': 'e83df36bebbe-1507037917.120',
                'caller': CallerId(code=150010002, number='202', name="Samantha Graham", is_public=True),
                'to_number': '203',
                'targets': [CallerId(code=150010003, number='203', is_public=True)],
            }),
            ('on_up', {
                'call_id': 'e83df36bebbe-1507037917.120',
                'caller': CallerId(code=150010002, number='202', name="Samantha Graham", is_public=True),
                'to_number': '203',
                'callee': CallerId(code=150010003, number='203', is_public=True),
            }),
            ('on_attended_transfer', {
                'new_id': 'e83df36bebbe-1507037917.120',
                'merged_id': 'e83df36bebbe-1507037906.116',
                'caller': CallerId(code=15001, number='+31150010001', is_public=True),
                'callee': CallerId(code=150010003, number='203', is_public=True),
                'redirector': CallerId(code=150010002, number='202', name="Samantha Graham", is_public=True),
            }),
            ('on_hangup', {
                'call_id': 'e83df36bebbe-1507037917.120',
                'caller': CallerId(code=15001, number='+31150010001', is_public=True),
                'to_number': '203',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_queue_blind_xfer(self):
        """
        Test a blind transfer with someone from a queue.
        """
        events = self.run_and_get_events('fixtures/queue/queue_blind_xfer.json')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': 'e83df36bebbe-1507042413.128',
                'caller': CallerId(code=15001, number='+31150010001', is_public=True),
                'to_number': '+31150010004',
                'targets': [CallerId(code=150010002, number='+31150010004', is_public=True)],
            }),
            ('on_up', {
                'call_id': 'e83df36bebbe-1507042413.128',
                'caller': CallerId(code=15001, number='+31150010001', is_public=True),
                'to_number': '+31150010004',
                'callee': CallerId(code=150010002, number='+31150010004', is_public=True),
            }),
            ('on_b_dial', {
                'call_id': 'e83df36bebbe-1507042415.129',
                'caller': CallerId(code=150010002, number='+31150010004', is_public=True),
                'to_number': '203',
                'targets': [CallerId(code=150010003, number='203', is_public=True)],
            }),
            ('on_cold_transfer', {
                'new_id': 'e83df36bebbe-1507042413.128',
                'merged_id': 'e83df36bebbe-1507042415.129',
                'caller': CallerId(code=15001, number='+31150010001', is_public=True),
                'targets': [CallerId(code=150010003, number='203', is_public=True)],
                'redirector': CallerId(code=150010002, number='+31150010004', name="", is_public=True),
                'to_number': '203',
            }),
            ('on_up', {
                'call_id': 'e83df36bebbe-1507042413.128',
                'caller': CallerId(code=15001, number='+31150010001', is_public=True),
                'to_number': '203',
                'callee': CallerId(code=150010003, number='203', is_public=True),
            }),
            ('on_hangup', {
                'call_id': 'e83df36bebbe-1507042413.128',
                'caller': CallerId(code=15001, number='+31150010001', is_public=True),
                'to_number': '203',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)
