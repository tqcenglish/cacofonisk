from cacofonisk.callerid import CallerId
from .replaytest import ChannelEventsTestCase


class TestBlondeXfer(ChannelEventsTestCase):
    """
    Test call state notifications for blonde transfers.

    A blonde transfer (also known as semi-attended transfer) is a type of
    transfer which looks like an attended transfer, but the transferer
    doesn't wait for person C to pick up.
    """

    def test_xfer_blonde_abacbc(self):
        """
        Test blonde transfer where A initiates the transfer.
        """
        events_file = 'fixtures/xfer_blonde/xfer_blonde_abacbc.json'
        events = self.run_and_get_events(events_file)

        call_id_one = 'f29ea68048f6-1530023922.2627'
        call_id_two = 'f29ea68048f6-1530023931.2654'
        a_party = CallerId(code=150010001, name='Andrew Garza', number='201')
        b_party = CallerId(code=150010002, number='202')
        c_party = CallerId(code=150010003, number='203')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '202',
                'targets': [b_party],
            }),
            ('on_up', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '202',
                'target': b_party,
            }),
            ('on_b_dial', {
                'call_id': call_id_two,
                'caller': a_party,
                'to_number': '203',
                'targets': [c_party],
            }),
            ('on_cold_transfer', {
                'new_id': call_id_one,
                'merged_id': call_id_two,
                'redirector': a_party,
                'caller': b_party,
                'to_number': '203',
                'targets': [c_party],
            }),
            ('on_up', {
                'call_id': call_id_one,
                'caller': b_party,
                'to_number': '203',
                'target': c_party,
            }),
            ('on_hangup', {
                'call_id': call_id_one,
                'caller': b_party,
                'to_number': '203',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_xfer_blonde_abbcac(self):
        """
        Test blonde transfer where B initiates the transfer.
        """
        events_file = 'fixtures/xfer_blonde/xfer_blonde_abbcac.json'
        events = self.run_and_get_events(events_file)

        call_id_one = 'f29ea68048f6-1530024929.2709'
        call_id_two = 'f29ea68048f6-1530024939.2753'
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
            ('on_cold_transfer', {
                'new_id': call_id_one,
                'merged_id': call_id_two,
                'redirector': b_party_calling,
                'caller': a_party,
                'to_number': '202',
                'targets': [c_party],
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

    def test_xfer_blonde_reject(self):
        """
        Test blonde transfer where the transfer target rejects the call.
        """
        events_file = 'fixtures/xfer_blonde/xfer_blonde_reject.json'
        events = self.run_and_get_events(events_file)

        call_id_one = 'f29ea68048f6-1530025486.2901'
        call_id_two = 'f29ea68048f6-1530025493.2945'
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
            ('on_cold_transfer', {
                'new_id': call_id_one,
                'merged_id': call_id_two,
                'redirector': b_party_calling,
                'caller': a_party,
                'to_number': '202',
                'targets': [c_party],
            }),
            ('on_hangup', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '202',
                'reason': 'busy',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_xfer_blonde_group_b(self):
        """
        Test blonde transfer where the call is transferred to a group by B.
        """
        events_file = 'fixtures/xfer_blonde/xfer_blonde_group_b.json'
        events = self.run_and_get_events(events_file)

        call_id_one = 'f29ea68048f6-1530026019.2993'
        call_id_two = 'f29ea68048f6-1530026028.3037'
        a_party = CallerId(code=15001, number='+31260010001')
        b_party_called = CallerId(code=150010001, number='+31150010001')
        b_party_calling = CallerId(code=150010001, name='Andrew Garza',
                                   number='201')
        c_party_one = CallerId(code=150010002, number='401')
        c_party_two = CallerId(code=150010003, number='401')

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
                'to_number': '401',
                'targets': [c_party_one, c_party_two],
            }),
            ('on_cold_transfer', {
                'new_id': call_id_one,
                'merged_id': call_id_two,
                'redirector': b_party_calling,
                'caller': a_party,
                'to_number': '401',
                'targets': [c_party_one, c_party_two],
            }),
            ('on_up', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '401',
                'target': c_party_one,
            }),
            ('on_hangup', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '401',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_xfer_blonde_group_a(self):
        """
        Test blonde transfer where the call is transferred to a group by A.
        """
        events_file = 'fixtures/xfer_blonde/xfer_blonde_group_a.json'
        events = self.run_and_get_events(events_file)

        call_id_one = 'f29ea68048f6-1530026204.3102'
        call_id_two = 'f29ea68048f6-1530026216.3156'
        a_party = CallerId(code=150010001, number='+31150010001')
        a_party_calling = a_party.replace(name='Andrew Garza', number='201')
        b_party = CallerId(code=150010001, number='+31260010001')
        c_party_one = CallerId(code=150010002, number='401')
        c_party_two = CallerId(code=150010003, number='401')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '0260010001',
                'targets': [b_party],
            }),
            ('on_up', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '0260010001',
                'target': b_party,
            }),
            ('on_b_dial', {
                'call_id': call_id_two,
                'caller': a_party_calling,
                'to_number': '401',
                'targets': [c_party_one, c_party_two],
            }),
            ('on_cold_transfer', {
                'new_id': call_id_one,
                'merged_id': call_id_two,
                'redirector': a_party_calling,
                'caller': b_party,
                'to_number': '401',
                'targets': [c_party_one, c_party_two],
            }),
            ('on_up', {
                'call_id': call_id_one,
                'caller': b_party,
                'to_number': '401',
                'target': c_party_one,
            }),
            ('on_hangup', {
                'call_id': call_id_one,
                'caller': b_party,
                'to_number': '401',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)
