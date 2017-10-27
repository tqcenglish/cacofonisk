from cacofonisk.callerid import CallerId
from .replaytest import ChannelEventsTestCase


class TestBlindXferOrig(ChannelEventsTestCase):

    def test_xfer_blind_abbcac(self):
        """Test a blind transfer where B initiates the transfer.
        """
        events = self.run_and_get_events('fixtures/xfer_blind/xfer_blind_abbcac.json')

        expected_events = self.events_from_tuples((
            # 203 calls 202
            ('on_b_dial', {
                'call_id': '63f2f9ce924a-1501834121.34',
                'caller': CallerId(code=150010003, name='Julia Rhodes', number='203', is_public=True),
                'targets': [CallerId(code=150010002, number='202', is_public=True)],
            }),
            # 202 picks up
            ('on_up', {
                'call_id': '63f2f9ce924a-1501834121.34',
                'caller': CallerId(code=150010003, name='Julia Rhodes', number='203', is_public=True),
                'callee': CallerId(code=150010002, number='202', is_public=True),
            }),
            # 202 dials 201...
            ('on_b_dial', {
                'call_id': '63f2f9ce924a-1501834121.35',
                'caller': CallerId(code=150010002, number='202', is_public=True),
                'targets': [CallerId(code=150010001, number='201', is_public=True)],
            }),
            # ... and immediately transfers 203 to 201
            ('on_blind_transfer', {
                'redirector': CallerId(code=150010002, number='202', is_public=True),
                'party1': CallerId(code=150010003, number='203', is_public=True),
                'targets': [CallerId(code=150010001, number='201', is_public=True)],
                'new_id': '63f2f9ce924a-1501834121.34',
                'merged_id': '63f2f9ce924a-1501834121.35'
            }),
            # The initial call is disconnected
            ('on_hangup', {
                'call_id': '63f2f9ce924a-1501834121.35',
                'caller': CallerId(code=150010002, number='202', is_public=True),
                'callee': CallerId(code=150010001, number='201', is_public=True),
                'reason': 'transferred',
            }),
            # 201 picks up to talk to 203
            ('on_up', {
                'call_id': '63f2f9ce924a-1501834121.34',
                'caller': CallerId(code=150010003, number='203', is_public=True),
                'callee': CallerId(code=150010001, number='201', is_public=True),
            }),
            # 203 and 201 are done
            ('on_hangup', {
                'call_id': '63f2f9ce924a-1501834121.34',
                'caller': CallerId(code=150010003, number='203', is_public=True),
                'callee': CallerId(code=150010001, number='201', is_public=True),
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_xfer_blind_abacbc(self):
        """Test a blind transfer where A initiates the transfer.
        """
        events = self.run_and_get_events('fixtures/xfer_blind/xfer_blind_abacbc.json')

        expected_events = self.events_from_tuples((
            # 202 calls 203
            ('on_b_dial', {
                'call_id': '63f2f9ce924a-1501834972.41',
                'caller': CallerId(code=150010002, name='Robert Murray', number='202', is_public=True),
                'targets': [CallerId(code=150010003, number='203', is_public=True)],
            }),
            # 203 picks up
            ('on_up', {
                'call_id': '63f2f9ce924a-1501834972.41',
                'caller': CallerId(code=150010002, name='Robert Murray', number='202', is_public=True),
                'callee': CallerId(code=150010003, number='203', is_public=True),
            }),
            # 202 dials 201...
            # (CLI for 150010002 is how it was reached externally,
            # that's okay.)
            ('on_b_dial', {
                'call_id': '63f2f9ce924a-1501834980.45',
                'caller': CallerId(code=150010002, name='Robert Murray', number='202', is_public=True),
                'targets': [CallerId(code=150010001, name='Robert Murray', number='201', is_public=True)],
            }),
            # ... and immediately transfers 203 to 201
            ('on_blind_transfer', {
                'redirector': CallerId(code=150010002, name='Robert Murray', number='202', is_public=True),
                'party1': CallerId(code=150010003, number='203', is_public=True),
                'targets': [CallerId(code=150010001, name='Robert Murray', number='201', is_public=True)],
                'new_id': '63f2f9ce924a-1501834980.45',
                'merged_id': '63f2f9ce924a-1501834972.41'
            }),
            # The original call 202 <-> 203 is disconnected
            ('on_hangup', {
                'call_id': '63f2f9ce924a-1501834972.41',
                'caller': CallerId(code=150010002, name='Robert Murray', number='202', is_public=True),
                'callee': CallerId(code=150010001, name='Robert Murray', number='201', is_public=True),
                'reason': 'transferred',
            }),
            # 201 picks up to talk to 203
            ('on_up', {
                'call_id': '63f2f9ce924a-1501834980.45',
                'caller': CallerId(code=150010003, number='203', is_public=True),
                'callee': CallerId(code=150010001, name='Robert Murray', number='201', is_public=True),
            }),
            # 203 and 201 are done
            ('on_hangup', {
                'call_id': '63f2f9ce924a-1501834980.45',
                'caller': CallerId(code=150010003, number='203', is_public=True),
                'callee': CallerId(code=150010001, name='Robert Murray', number='201', is_public=True),
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_xfer_blind_complex(self):
        """Test a complex blind transfer.

        Test a blind transfer with call groups where B initiates the transfer.
        """
        events = self.run_and_get_events('fixtures/xfer_blind/xfer_blind.json')

        expected_events = self.events_from_tuples((
            # +31501234567 calls 202/205, 202 picks up, blind xfer to 205
            # => 202
            ('on_b_dial', {
                'call_id': 'vgua0-dev-1443449049.124',
                'caller': CallerId(number='+31501234567', is_public=True),
                'targets': [
                    CallerId(code=126680002, number='+31507001918', is_public=True),
                    CallerId(code=126680005, number='+31507001918', is_public=True),
                ],
            }),

            # => 202 picks up
            ('on_up', {
                'call_id': 'vgua0-dev-1443449049.124',
                'caller': CallerId(number='+31501234567', is_public=True),
                'callee': CallerId(code=126680002, number='+31507001918', is_public=True),
            }),

            # (CLI for 126680002 is how it was reached externally,
            # that's okay.)
            ('on_b_dial', {
                'call_id': 'vgua0-dev-1443449049.125',
                'caller': CallerId(code=126680002, number='+31507001918', is_public=True),
                'targets': [CallerId(code=126680005, number='205', is_public=True)],
            }),

            # Blind xfer.
            # (CLI for 126680002 is how it was reached externally,
            # that's okay.)
            ('on_blind_transfer', {
                'redirector': CallerId(code=126680002, number='+31507001918', is_public=True),
                'party1': CallerId(number='+31501234567', is_public=True),
                'targets': [CallerId(code=126680005, number='205', is_public=True)],
                'new_id': 'vgua0-dev-1443449049.124',
                'merged_id': 'vgua0-dev-1443449049.125',
            }),

            # The call 202 <-> 205 is disconnected
            ('on_hangup', {
                'call_id': 'vgua0-dev-1443449049.125',
                'caller': CallerId(code=126680002, number='+31507001918', is_public=True),
                'callee': CallerId(code=126680005, number='205', is_public=True),
                'reason': 'transferred',
            }),

            ('on_up', {
                'call_id': 'vgua0-dev-1443449049.124',
                'caller': CallerId(number='+31501234567', is_public=True),
                'callee': CallerId(code=126680005, number='205', is_public=True),
            }),

            ('on_hangup', {
                'call_id': 'vgua0-dev-1443449049.124',
                'caller': CallerId(number='+31501234567', is_public=True),
                'callee': CallerId(code=126680005, number='205', is_public=True),
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_xfer_blind_a_no_answer(self):
        """
        Test a blind transfer from A where the transfer target is down.
        """
        events = self.run_and_get_events('fixtures/xfer_blind/xfer_blind_a_no_answer.json')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': '0f00dcaa884f-1509114500.0',
                'caller': CallerId(code=150010002, name='David Meadows', number='202', is_public=True),
                'targets': [CallerId(code=150010004, number='204', is_public=True)],
            }),
            ('on_up', {
                'call_id': '0f00dcaa884f-1509114500.0',
                'caller': CallerId(code=150010002, name='David Meadows', number='202', is_public=True),
                'callee': CallerId(code=150010004, number='204', is_public=True),
            }),
            ('on_hangup', {
                'call_id': '0f00dcaa884f-1509114500.0',
                # TODO: The name is missing on the caller. Weird, no disaster.
                'caller': CallerId(code=150010002, number='202', is_public=True),
                'callee': CallerId(code=150010004, number='204', is_public=True),
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_xfer_blind_b_no_answer(self):
        """
        Test a blind transfer from B where the transfer target is down.
        """
        events = self.run_and_get_events('fixtures/xfer_blind/xfer_blind_b_no_answer.json')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': '0f00dcaa884f-1509115795.11',
                'caller': CallerId(code=150010002, name='David Meadows', number='202', is_public=True),
                'targets': [CallerId(code=150010004, number='204', is_public=True)],
            }),
            ('on_up', {
                'call_id': '0f00dcaa884f-1509115795.11',
                'caller': CallerId(code=150010002, name='David Meadows', number='202', is_public=True),
                'callee': CallerId(code=150010004, number='204', is_public=True),
            }),
            ('on_hangup', {
                'call_id': '0f00dcaa884f-1509115795.11',
                'caller': CallerId(code=150010002, name='David Meadows', number='202', is_public=True),
                'callee': CallerId(code=150010004, number='204', is_public=True),
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_xfer_blind_reject(self):
        """
        Test a blind transfer from where the target rejects the transfer.
        """
        events = self.run_and_get_events('fixtures/xfer_blind/xfer_blind_reject.json')

        expected_events = self.events_from_tuples((
            ('on_b_dial', {
                'call_id': '0f00dcaa884f-1509116084.19',
                'caller': CallerId(code=150010002, name='David Meadows', number='202', is_public=True),
                'targets': [CallerId(code=150010004, number='204', is_public=True)],
            }),
            ('on_up', {
                'call_id': '0f00dcaa884f-1509116084.19',
                'caller': CallerId(code=150010002, name='David Meadows', number='202', is_public=True),
                'callee': CallerId(code=150010004, number='204', is_public=True),
            }),
            ('on_b_dial', {
                'call_id': '0f00dcaa884f-1509116084.20',
                'caller': CallerId(code=150010004, number='204', is_public=True),
                'targets': [CallerId(code=150010003, number='203', is_public=True)],
            }),
            ('on_blind_transfer', {
                'redirector': CallerId(code=150010004, number='204', is_public=True),
                'party1': CallerId(code=150010002, number='202', is_public=True),
                'targets': [CallerId(code=150010003, number='203', is_public=True)],
                'new_id': '0f00dcaa884f-1509116084.19',
                'merged_id': '0f00dcaa884f-1509116084.20',
            }),
            ('on_hangup', {
                'call_id': '0f00dcaa884f-1509116084.20',
                'caller': CallerId(code=150010004, number='204', is_public=True),
                'callee': CallerId(code=150010003, number='203', is_public=True),
                'reason': 'transferred',
            }),
            ('on_hangup', {
                'call_id': '0f00dcaa884f-1509116084.19',
                'caller': CallerId(code=150010002, number='202', is_public=True),
                'callee': CallerId(code=150010003, number='203', is_public=True),
                'reason': 'rejected',
            }),
        ))

        self.assertEqual(expected_events, events)