from cacofonisk.callerid import CallerId
from .replaytest import ChannelEventsTestCase


class TestBlindXfer(ChannelEventsTestCase):

    def test_xfer_blind_abbcac(self):
        """
        Test a blind transfer where B initiates the transfer.
        """
        events_file = 'fixtures/xfer_blind/xfer_blind_abbcac.json'
        events = self.run_and_get_events(events_file)

        call_id_one = '07b796be1962-1529998959.65'
        call_id_two = '07b796be1962-1529998966.104'
        a_party = CallerId(code=150010001, name='Andrew Garza', number='201')
        a_party_updated = a_party.replace(name='')
        b_party = CallerId(code=150010002, number='202')
        c_party = CallerId(code=150010003, number='203')

        expected_events = self.events_from_tuples((
            # 201 calls 202
            ('on_b_dial', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '202',
                'targets': [b_party],
            }),
            # 202 picks up
            ('on_up', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '202',
                'target': b_party,
            }),
            # 202 dials 203...
            ('on_b_dial', {
                'call_id': call_id_two,
                'caller': b_party,
                'to_number': '203',
                'targets': [c_party],
            }),
            # ... and immediately transfers 201 to 203
            ('on_cold_transfer', {
                'new_id': call_id_one,
                'merged_id': call_id_two,
                'to_number': '203',
                'redirector': b_party,
                # TODO: The name is missing on the caller. Weird, no disaster.
                'caller': a_party_updated,
                'targets': [c_party],
            }),
            # 203 picks up to talk to 201
            ('on_up', {
                'call_id': call_id_one,
                'caller': a_party_updated,
                'to_number': '203',
                'target': c_party,
            }),
            # 201 and 203 are done
            ('on_hangup', {
                'call_id': call_id_one,
                'caller': a_party_updated,
                'to_number': '203',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_xfer_blind_abacbc(self):
        """
        Test a blind transfer where A initiates the transfer.
        """
        events_file = 'fixtures/xfer_blind/xfer_blind_abacbc.json'
        events = self.run_and_get_events(events_file)

        call_id_one = '07b796be1962-1529998985.130'
        call_id_two = '07b796be1962-1529998993.169'
        a_party = CallerId(code=150010001, name='Andrew Garza', number='201')
        b_party = CallerId(code=150010002, number='202')
        # TODO: The blind transfer target gets the name of the caller.
        c_party = CallerId(code=150010003, name='Andrew Garza', number='203')

        expected_events = self.events_from_tuples((
            # 201 calls 202
            ('on_b_dial', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '202',
                'targets': [b_party],
            }),
            # 202 picks up
            ('on_up', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '202',
                'target': b_party,
            }),
            # 201 dials 203...
            ('on_b_dial', {
                'call_id': call_id_two,
                'caller': a_party,
                'to_number': '203',
                'targets': [c_party],
            }),
            # ... and immediately transfers 201 to 203
            ('on_cold_transfer', {
                'new_id': call_id_one,
                'merged_id': call_id_two,
                'to_number': '203',
                'redirector': a_party,
                'caller': b_party,
                'targets': [c_party],
            }),
            # 203 picks up to talk to 201
            ('on_up', {
                'call_id': call_id_one,
                'caller': b_party,
                'to_number': '203',
                'target': c_party,
            }),
            # 201 and 203 are done
            ('on_hangup', {
                'call_id': call_id_one,
                'caller': b_party,
                'to_number': '203',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_xfer_blind_a_no_answer(self):
        """
        Test a blind transfer from A where the transfer target is down.
        """
        events_file = 'fixtures/xfer_blind/xfer_blind_a_no_answer.json'
        events = self.run_and_get_events(events_file)

        call_id_one = '07b796be1962-1530000279.351'
        a_party = CallerId(code=150010001, name='Andrew Garza', number='201')
        b_party = CallerId(code=150010002, number='202')

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
            ('on_hangup', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '202',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_xfer_blind_b_no_answer(self):
        """
        Test a blind transfer from B where the transfer target is down.
        """
        events_file = 'fixtures/xfer_blind/xfer_blind_b_no_answer.json'
        events = self.run_and_get_events(events_file)

        call_id_one = '07b796be1962-1530000295.403'
        a_party = CallerId(code=150010001, name='Andrew Garza', number='201')
        # TODO The name is removed from the party after the transfer.
        a_party_updated = a_party.replace(name='')
        b_party = CallerId(code=150010002, number='202')

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
            ('on_hangup', {
                'call_id': call_id_one,
                'caller': a_party_updated,
                'to_number': '202',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_xfer_blind_reject(self):
        """
        Test a blind transfer from where the target rejects the transfer.
        """
        events_file = 'fixtures/xfer_blind/xfer_blind_reject.json'
        events = self.run_and_get_events(events_file)

        call_id_one = '07b796be1962-1530000704.455'
        call_id_two = '07b796be1962-1530000709.494'
        a_party = CallerId(code=150010001, name='Andrew Garza', number='201')
        a_party_updated = a_party.replace(name='')
        b_party = CallerId(code=150010002, number='202')
        c_party = CallerId(code=150010003, number='203')

        expected_events = self.events_from_tuples((
            # 201 calls 202
            ('on_b_dial', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '202',
                'targets': [b_party],
            }),
            # 202 picks up
            ('on_up', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '202',
                'target': b_party,
            }),
            # 202 dials 203...
            ('on_b_dial', {
                'call_id': call_id_two,
                'caller': b_party,
                'to_number': '203',
                'targets': [c_party],
            }),
            # ... and immediately transfers 201 to 203
            ('on_cold_transfer', {
                'new_id': call_id_one,
                'merged_id': call_id_two,
                'to_number': '203',
                'redirector': b_party,
                # TODO: The name is missing on the caller. Weird, no disaster.
                'caller': a_party_updated,
                'targets': [c_party],
            }),
            # 201 and 203 are done
            ('on_hangup', {
                'call_id': call_id_one,
                'caller': a_party_updated,
                'to_number': '203',
                'reason': 'no-answer',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_xfer_blind_group(self):
        """
        Test a blind transfer where the call is transferred to a group.
        """
        events_file = 'fixtures/xfer_blind/xfer_blind_group.json'
        events = self.run_and_get_events(events_file)

        call_id_one = 'f29ea68048f6-1530014341.278'
        call_id_two = 'f29ea68048f6-1530014347.341'
        a_party = CallerId(code=15001, number='+31260010001')
        b_party = CallerId(code=150010001, number='+31150010001')
        c_party_one = CallerId(code=150010002, number='401')
        c_party_two = CallerId(code=150010003, number='401')

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
                'to_number': '401',
                'targets': [c_party_one, c_party_two],
            }),
            ('on_cold_transfer', {
                'new_id': call_id_one,
                'merged_id': call_id_two,
                'to_number': '401',
                'redirector': b_party,
                'caller': a_party,
                'targets': [c_party_one, c_party_two],
            }),
            ('on_up', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '401',
                'target': c_party_two,
            }),
            ('on_hangup', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '401',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)

    def test_xfer_blind_group_no_answer(self):
        """
        Test a blind transfer where the call is transferred to a group.
        """
        events_file = 'fixtures/xfer_blind/xfer_blind_group_no_answer.json'
        events = self.run_and_get_events(events_file)

        call_id_one = 'f29ea68048f6-1530015089.506'
        a_party = CallerId(code=15001, number='+31260010001')
        b_party = CallerId(code=150010001, number='+31150010001')

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
            ('on_hangup', {
                'call_id': call_id_one,
                'caller': a_party,
                'to_number': '+31150010001',
                'reason': 'completed',
            }),
        ))

        self.assertEqual(expected_events, events)
