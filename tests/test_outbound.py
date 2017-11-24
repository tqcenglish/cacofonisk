from cacofonisk.callerid import CallerId
from tests.replaytest import ChannelEventsTestCase


class OutboundTestCase(ChannelEventsTestCase):

    def test_outbound_success(self):
        """
        Test a simple outbound call where A calls external number B.
        """
        events = self.run_and_get_events('fixtures/outbound/success.json')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': 'f1149f88180f-1511529983.40',
                'direction': 'outbound',
                'caller': CallerId(code=260010001, number='+31260010001', is_public=True),
                'to_number': '0150010002',
                'targets': [CallerId(code=0, number='+31150010002', is_public=True)],
            }),
            ('on_up', {
                'call_id': 'f1149f88180f-1511529983.40',
                'direction': 'outbound',
                'caller': CallerId(code=260010001, number='+31260010001', is_public=True),
                'to_number': '0150010002',
                'callee': CallerId(code=260010001, number='+31150010002', is_public=True),
            }),
            ('on_hangup', {
                'call_id': 'f1149f88180f-1511529983.40',
                'direction': 'outbound',
                'caller': CallerId(code=260010001, number='+31260010001', is_public=True),
                'to_number': '0150010002',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_outbound_busy(self):
        """
        Test an outbound call where the destination is busy.
        """
        events = self.run_and_get_events('fixtures/outbound/busy.json')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': 'f1149f88180f-1511530498.48',
                'direction': 'outbound',
                'caller': CallerId(code=260010001, number='+31260010001', is_public=True),
                'to_number': '0150010002',
                'targets': [CallerId(code=0, number='+31150010002', is_public=True)],
            }),
            ('on_hangup', {
                'call_id': 'f1149f88180f-1511530498.48',
                'direction': 'outbound',
                'caller': CallerId(code=260010001, number='+31260010001', is_public=True),
                'to_number': '0150010002',
                'reason': 'busy',
            }),
        ))

        self.assertEqual(expected_events, events)
