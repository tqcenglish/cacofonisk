from cacofonisk.callerid import CallerId
from .replaytest import ChannelEventsTestCase


class TestAttnXfer(ChannelEventsTestCase):
    def test_xfer_abacbc(self):
        """
        Test attended transfer where A transfers B to C.

        First of all, we need to get notifications that calls are being
        made:
        - 201 (126680001) calls 202
        - 201 calls 203 (126680003)

        Secondly, we need notifications that an (attended) transfer has
        happened:
        - 201 joins the other channels (202 <--> 203)
        """
        events_file = 'fixtures/xfer_attended/xfer_abacbc.json'
        events = self.run_and_get_events(events_file)

        call_id_one = '195176c06ab8-1529941216.590'
        call_id_two = '195176c06ab8-1529941225.617'
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
            ('on_up', {
                'call_id': call_id_two,
                'caller': a_party,
                'to_number': '203',
                'target': c_party,
            }),
            ('on_attended_transfer', {
                'new_id': call_id_one,
                'merged_id': call_id_two,
                'caller': b_party,
                'redirector': a_party,
                'target': c_party,
            }),
            ('on_hangup', {
                'call_id': call_id_one,
                'caller': b_party,
                'to_number': '202',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_xfer_abbcac(self):
        """
        Test attended transfer where B transfers A to C.

        First of all, we need to get notifications that calls are being
        made:
        - +31501234567 calls 201 (126680001)
        - 201 calls 202

        Secondly, we need notifications that an (attended) transfer has
        happened:
        - 201 joins the other channels (+31501234567 <--> 202)
        """
        events_file = 'fixtures/xfer_attended/xfer_abbcac.json'
        events = self.run_and_get_events(events_file)

        call_id_one = '195176c06ab8-1529941338.663'
        call_id_two = '195176c06ab8-1529941342.690'
        a_party = CallerId(code=150010001, name='Andrew Garza', number='201')
        b_party_called = CallerId(code=150010002, number='202')
        b_party_calling = b_party_called.replace(name='Christina Arroyo')
        c_party = CallerId(code=150010003, number='203')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '202',
                'targets': [b_party_called],
            }),
            ('on_up', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '202',
                'target': b_party_called,
            }),
            ('on_b_dial', {
                'call_id': call_id_two,
                'caller': b_party_calling,
                'to_number': '203',
                'targets': [c_party],
            }),
            ('on_up', {
                'call_id': call_id_two,
                'caller': b_party_calling,
                'to_number': '203',
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
                'to_number': '202',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_xfer_abbcac_anonymous(self):
        """
        Test that an attended transfer where the caller is anonymous works.
        """
        events_file = 'fixtures/xfer_attended/xfer_abbcac_anon.json'
        events = self.run_and_get_events(events_file)

        call_id_one = '07b796be1962-1530001217.664'
        call_id_two = '07b796be1962-1530001225.708'
        a_party = CallerId(code=15001, number='+31260xxxxxx', is_public=False)
        b_party_called = CallerId(code=150010001, number='+31150010001')
        b_party_calling = b_party_called.replace(
            number='201', name='Andrew Garza')
        c_party = CallerId(code=150010003, number='203')

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
                'to_number': '203',
                'targets': [c_party],
            }),
            ('on_up', {
                'call_id': call_id_two,
                'caller': b_party_calling,
                'to_number': '203',
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
