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
        events = self.run_and_get_events('fixtures/xfer_attended/xfer_abacbc.json')

        a_party = CallerId(code=150010001, name='Andrew Garza', number='201')
        b_party = CallerId(code=150010002, number='202')
        c_party = CallerId(code=150010003, number='203')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': '195176c06ab8-1529941216.590',
                'caller': a_party,
                'to_number': '202',
                'targets': [b_party],
            }),
            ('on_up', {
                'call_id': '195176c06ab8-1529941216.590',
                'caller': a_party,
                'to_number': '202',
                'target': b_party,
            }),
            ('on_b_dial', {
                'call_id': '195176c06ab8-1529941225.617',
                'caller': a_party,
                'to_number': '203',
                'targets': [c_party],
            }),
            ('on_up', {
                'call_id': '195176c06ab8-1529941225.617',
                'caller': a_party,
                'to_number': '203',
                'target': c_party,
            }),
            ('on_attended_transfer', {
                'new_id': '195176c06ab8-1529941216.590',
                'merged_id': '195176c06ab8-1529941225.617',
                'caller': b_party,
                'redirector': a_party,
                'target': c_party,
            }),
            ('on_hangup', {
                'call_id': '195176c06ab8-1529941216.590',
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
        events = self.run_and_get_events(
            'fixtures/xfer_attended/xfer_abbcac.json')

        a_party = CallerId(code=150010001, name='Andrew Garza', number='201')
        b_party_called = CallerId(code=150010002, number='202')
        b_party_calling = CallerId(code=150010002, number='202',
                                   name='Christina Arroyo')
        c_party = CallerId(code=150010003, number='203')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': '195176c06ab8-1529941338.663',
                'caller': a_party,
                'to_number': '202',
                'targets': [b_party_called],
            }),
            ('on_up', {
                'call_id': '195176c06ab8-1529941338.663',
                'caller': a_party,
                'to_number': '202',
                'target': b_party_called,
            }),
            ('on_b_dial', {
                'call_id': '195176c06ab8-1529941342.690',
                'caller': b_party_calling,
                'to_number': '203',
                'targets': [c_party],
            }),
            ('on_up', {
                'call_id': '195176c06ab8-1529941342.690',
                'caller': b_party_calling,
                'to_number': '203',
                'target': c_party,
            }),
            ('on_attended_transfer', {
                'new_id': '195176c06ab8-1529941338.663',
                'merged_id': '195176c06ab8-1529941342.690',
                'caller': a_party,
                'redirector': b_party_calling,
                'target': c_party,
            }),
            ('on_hangup', {
                'call_id': '195176c06ab8-1529941338.663',
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
        self.skipTest('Supress CallerID doesn\'t work yet in the devstack.')
