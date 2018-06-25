from cacofonisk.callerid import CallerId
from .replaytest import ChannelEventsTestCase


class TestSimple(ChannelEventsTestCase):

    def test_ab_success_a_hangup(self):
        """
        Test a simple, successful call where A hangs up.
        """
        fixture_file = 'fixtures/simple/ab_success_a_hangup.json'
        events = self.run_and_get_events(fixture_file)

        caller = CallerId(code=150010001, name='Andrew Garza', number='201')
        target = CallerId(code=150010002, number='202')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': '195176c06ab8-1529936170.42',
                'caller': caller,
                'to_number': '202',
                'targets': [target],
            }),
            ('on_up', {
                'call_id': '195176c06ab8-1529936170.42',
                'caller': caller,
                'to_number': '202',
                'target': target,
            }),
            ('on_hangup', {
                'call_id': '195176c06ab8-1529936170.42',
                'caller': caller,
                'to_number': '202',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_ab_success_b_hangup(self):
        """
        Test a simple, successful call where B hangs up.
        """
        fixture_file = 'fixtures/simple/ab_success_b_hangup.json'
        events = self.run_and_get_events(fixture_file)

        caller = CallerId(code=150010001, name='Andrew Garza', number='201')
        target = CallerId(code=150010002, number='202')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': '195176c06ab8-1529936710.252',
                'caller': caller,
                'to_number': '202',
                'targets': [target],
            }),
            ('on_up', {
                'call_id': '195176c06ab8-1529936710.252',
                'caller': caller,
                'to_number': '202',
                'target': target,
            }),
            ('on_hangup', {
                'call_id': '195176c06ab8-1529936710.252',
                'caller': caller,
                'to_number': '202',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_ab_success_twoclients(self):
        """
        Test a simple, successful call with calls through a proxy.

        Account 260010001 using +31260010001 as outdialing number, dials
        +31150010001 which is connected to account 150010001 with internal
        number 201 the call is picked up and completed successfully.
        """
        fixture_file = 'fixtures/simple/ab_success_twoclients.json'
        events = self.run_and_get_events(fixture_file)

        outbound_caller = CallerId(code=260010001, number='+31260010001')
        outbound_target = CallerId(code=260010001, number='+31150010001')

        inbound_caller = CallerId(code=15001, number='+31260010001')
        inbound_target = CallerId(code=150010001, number='+31150010001')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': '195176c06ab8-1529936734.287',
                'caller': outbound_caller,
                'to_number': '0150010001',
                'targets': [outbound_target],
            }),
            ('on_b_dial', {
                'call_id': '195176c06ab8-1529936734.297',
                'caller': inbound_caller,
                'to_number': '+31150010001',
                'targets': [inbound_target],
            }),
            ('on_up', {
                'call_id': '195176c06ab8-1529936734.287',
                'caller': outbound_caller,
                'to_number': '0150010001',
                'target': outbound_target,
            }),
            ('on_up', {
                'call_id': '195176c06ab8-1529936734.297',
                'caller': inbound_caller,
                'to_number': '+31150010001',
                'target': inbound_target,
            }),
            ('on_hangup', {
                'call_id': '195176c06ab8-1529936734.297',
                'caller': inbound_caller,
                'to_number': '+31150010001',
                'reason': 'completed',
            }),
            ('on_hangup', {
                'call_id': '195176c06ab8-1529936734.287',
                'caller': outbound_caller,
                'to_number': '0150010001',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(events, expected_events)

    def test_ab_reject(self):
        """
        Test a simple call where B rejects the call.
        """
        fixture_file = 'fixtures/simple/ab_reject.json'
        events = self.run_and_get_events(fixture_file)

        caller = CallerId(code=150010001, name='Andrew Garza', number='201')
        target = CallerId(code=150010002, number='202')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': '195176c06ab8-1529936241.98',
                'caller': caller,
                'to_number': '202',
                'targets': [target],
            }),
            ('on_hangup', {
                'call_id': '195176c06ab8-1529936241.98',
                'caller': caller,
                'to_number': '202',
                'reason': 'busy',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_ab_dnd(self):
        """
        Test a simple call where B is set to Do Not Disturb.
        """
        fixture_file = 'fixtures/simple/ab_dnd.json'
        events = self.run_and_get_events(fixture_file)

        caller = CallerId(code=150010001, name='Andrew Garza', number='201')

        expected_events = self.events_from_tuples((
            ('on_hangup', {
                'call_id': '195176c06ab8-1529936189.77',
                'caller': caller,
                'to_number': '202',
                'reason': 'busy',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_ab_a_cancel_hangup(self):
        """
        Test a call where A hangs up before B can pick up.
        """
        fixture_file = 'fixtures/simple/ab_a_cancel.json'
        events = self.run_and_get_events(fixture_file)

        caller = CallerId(code=150010001, name='Andrew Garza', number='201')
        target = CallerId(code=150010002, number='202')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': '195176c06ab8-1529936141.21',
                'caller': caller,
                'to_number': '202',
                'targets': [target],
            }),
            ('on_hangup', {
                'call_id': '195176c06ab8-1529936141.21',
                'caller': caller,
                'to_number': '202',
                'reason': 'cancelled',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_ab_callgroup(self):
        """
        Test a simple call to a group where one phone is picked up.
        """
        fixture_file = 'fixtures/simple/ab_callgroup.json'
        events = self.run_and_get_events(fixture_file)

        caller = CallerId(code=150010001, name='Andrew Garza', number='201')
        target = CallerId(code=150010002, number='401')
        other_target = CallerId(code=150010003, number='401')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': '195176c06ab8-1529936598.168',
                'caller': caller,
                'to_number': '401',
                'targets': [target, other_target],
            }),
            ('on_up', {
                'call_id': '195176c06ab8-1529936598.168',
                'caller': caller,
                'to_number': '401',
                'target': target,
            }),
            ('on_hangup', {
                'call_id': '195176c06ab8-1529936598.168',
                'caller': caller,
                'to_number': '401',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_ab_callgroup_no_answer(self):
        """
        Test a call to a group where no target picks up.
        """
        fixture_file = 'fixtures/simple/ab_callgroup_no_answer.json'
        events = self.run_and_get_events(fixture_file)

        caller = CallerId(code=150010001, name='Andrew Garza', number='201')
        target = CallerId(code=150010002, number='401')
        other_target = CallerId(code=150010003, number='401')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': '195176c06ab8-1529936670.217',
                'caller': caller,
                'to_number': '401',
                'targets': [target, other_target],
            }),
            ('on_hangup', {
                'call_id': '195176c06ab8-1529936670.217',
                'caller': caller,
                'to_number': '401',
                'reason': 'no-answer',
            }),
        ))

        self.assertEqual(expected_events, events)
