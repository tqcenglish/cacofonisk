from .bridge import BridgeRegistry
from .channel import Channel, ChannelRegistry, MissingChannel, MissingUniqueid
from .constants import (
    AST_CAUSE_ANSWERED_ELSEWHERE,
    AST_CAUSE_CALL_REJECTED,
    AST_CAUSE_NORMAL_CLEARING,
    AST_CAUSE_NO_ANSWER,
    AST_CAUSE_NO_USER_RESPONSE,
    AST_CAUSE_UNKNOWN,
    AST_CAUSE_USER_BUSY,
    AST_STATE_DOWN)


class EventHandler(object):
    """
    The EventHandler translates AMI events to high level call events.

    Usage::

        class MyEventHandler(EventHandler):
            def on_b_dial(self, call_id, caller, callee):
                # Your code here.
                # call_id is a unique identifying string of a conversation.
                # Caller and callee are of type CallerId.
                pass

            def on_up(self, call_id, caller, callee):
                # Your code here.
                # call_id is a unique identifying string of a conversation.
                # Caller and callee are of type CallerId.
                pass

            def on_hangup(self, call_id, caller, callee, reason):
                # Your code here.
                # call_id is a unique identifying string of a conversation.
                # Caller and callee are of type CallerId.
                # reason is a keyword to identify why a conversation ended.
                pass

            def on_warm_transfer(self, call_id, merged_id, transferor,
            party1, party1):
                # Your code here. call_id and merged_id are unique strings to
                # identify two conversations being merged into one.
                # transferor, party1 and party2 are of type CallerId.
                pass

            def on_cold_transfer(self, call_id, merged_id, transferor,
            party1, targets):
                # Your code here. call_id and merged_id are unique strings to
                # identify two conversations being merged into one.
                # transferor and caller are of type CallerId. targets is a
                # list of CallerID objects.
                pass

            def on_user_event(self, event):
                # Your code here. Process custom events. event is a dict-like
                # object.
                pass

        class MyReporter(object):
            def trace_ami(self, ami):
                print(ami)

            def trace_msg(self, msg):
                print(msg)

        manager = MyEventHandler(MyReporter())

        # events is a list of AMI-event-like dictionaries.
        for event in events:
            if ('*' in manager.INTERESTING_EVENTS or
                    event['Event'] in manager.INTERESTING_EVENTS):
                # After some of the events, one of the event hook methods
                # is called.
                manager.on_event(event)
    """
    # We require all of these events to function properly. (Except
    # perhaps the FullyBooted one.)
    INTERESTING_EVENTS = (
        # This tells us that we're connected. We should probably
        # flush our channels at this point, because they aren't up
        # to date.
        'FullyBooted',
        # Event related to channel setup.
        'Newchannel', 'Newstate', 'NewCallerid', 'NewAccountCode',
        'NewConnectedLine',
        # Events used when setting up a call.
        'DialBegin', 'DialEnd', 'LocalBridge', 'Hangup',
        # Events about bridges and their contents.
        'BridgeCreate', 'BridgeEnter', 'BridgeLeave', 'BridgeDestroy',
        # Events about transfers.
        'BlindTransfer', 'AttendedTransfer',
        # UserEvents
        'UserEvent'
    )

    def __init__(self, reporter):
        """
        Create a EventHandler instance.

        Args:
            reporter (Reporter): A reporter with trace_msg and trace_ami
                methods.
        """
        self._reporter = reporter
        self._registry = ChannelRegistry()
        self._bridge_registry = BridgeRegistry(self)

    def on_event(self, event):
        """
        on_event calls `_on_event` with `event`. If `_on_event` raise an
        exception this is logged.

        Args:
            event (dict): A dictionary containing an AMI event.
        """
        try:
            self._on_event(event)
        except MissingChannel as e:
            # If this is after a recent FullyBooted and/or start of
            # self, it is reasonable to expect that certain events will
            # fail.
            self._reporter.trace_msg(
                'Channel with name {} not in mem when processing event: '
                '{!r}'.format(e.args[0], event))
        except MissingUniqueid as e:
            # This too is reasonably expected.
            self._reporter.trace_msg(
                'Channel with Uniqueid {} not in mem when processing event: '
                '{!r}'.format(e.args[0], event))

        self._reporter.on_event(event)

    def _on_event(self, event):
        """
        on_event takes an event, extract and store the appropriate state
        updates and if possible fire an event ourself.

        Args:
            event (Dict): A dictionary with Asterisk AMI data.
        """
        # Write message to reporter, for debug/test purposes.
        self._reporter.trace_ami(event)

        event_name = event['Event']

        if 'Uniqueid' in event:
            try:
                channel = self._registry.get_by_uniqueid(event['Uniqueid'])
            except MissingUniqueid:
                # It's OK if we don't know this channel, it might be a
                # Newchannel event.
                pass
            else:
                channel.sync_data(event)

        if event_name == 'FullyBooted':
            # Time to clear our channels because they are stale?
            self._reporter.trace_msg('Connected to Asterisk')
        elif event_name == 'Newchannel':
            channel = Channel(event, channel_manager=self)
            self._registry.add(channel)
        elif event_name == 'Newstate':
            channel = self._registry.get_by_name(event['Channel'])
            channel.set_state(event)
        elif event_name == 'NewCallerid':
            channel = self._registry.get_by_name(event['Channel'])
            channel.set_callerid(event)
        elif event_name == 'NewAccountCode':
            channel = self._registry.get_by_name(event['Channel'])
            channel.set_accountcode(event)
        elif event_name == 'NewConnectedLine':
            channel = self._registry.get_by_name(event['Channel'])
            channel.set_connected_line(event)
        elif event_name == 'LocalBridge':
            channel = self._registry.get_by_name(event.get('LocalOneChannel'))
            other = self._registry.get_by_name(event.get('LocalTwoChannel'))
            channel.do_localbridge(other)

        elif event_name == 'Hangup':
            channel = self._registry.get_by_name(event['Channel'])
            self._raw_hangup(channel, event)

        elif event_name == 'DialBegin':
            source = self._registry.get_by_uniqueid(event['Uniqueid'])
            target = self._registry.get_by_uniqueid(event['DestUniqueid'])

            # Verify target is not being dialed already.
            assert not target.back_dial

            # _fwd_dials is a list of channels being dialed by A.
            source.fwd_dials.append(target)

            # _back_dial is the channel dialing B.
            target.back_dial = source

        elif event_name == 'DialEnd':
            source = self._registry.get_by_uniqueid(event['Uniqueid'])
            target = self._registry.get_by_uniqueid(event['DestUniqueid'])

            # Verify target actually has an active dial.
            assert target.back_dial

            # _fwd_dials is a list of channels being dialed by A.
            source.fwd_dials.remove(target)

            # _back_dial is the channel dialing B.
            target.back_dial = None

        elif event_name == 'AttendedTransfer':
            # Both TargetChannel and TargetUniqueid can be used to match
            # the target channel; they can be used interchangeably.
            orig_transferer = self._registry.get_by_name(
                event['OrigTransfererChannel'])
            second_transferer = self._registry.get_by_name(
                event['SecondTransfererChannel'])

            if event['DestType'] == 'Bridge':
                self._raw_attended_transfer(
                    orig_transferer, second_transferer, event)
            elif event['DestType'] == 'App' and event['DestApp'] == 'Dial':
                self._raw_blonde_transfer(
                    orig_transferer, second_transferer, event)
            else:
                raise NotImplementedError(event)

        elif event_name == 'BlindTransfer':
            self._raw_blind_transfer(event)

        elif event_name == 'BridgeCreate':
            self._bridge_registry.create(event)

        elif event_name == 'BridgeEnter':
            bridge = self._bridge_registry.get_by_uniqueid(
                event['BridgeUniqueid'])
            bridge.enter(event)

            channel = self._registry.get_by_uniqueid(event['Uniqueid'])
            channel._bridge = bridge

            if channel.is_sip and not channel._is_picked_up:
                self._raw_in_call(channel, bridge, event)

        elif event_name == 'BridgeLeave':
            bridge = self._bridge_registry.get_by_uniqueid(
                event['BridgeUniqueid'])
            bridge.leave(event)

            channel = self._registry.get_by_uniqueid(event['Uniqueid'])
            channel._bridge = None

        elif event_name == 'BridgeDestroy':
            self._bridge_registry.destroy(event)

        elif event_name == 'UserEvent':
            self.on_user_event(event)
        else:
            pass

    # ===================================================================
    # Event handler translators
    # ===================================================================

    def _raw_a_dial(self, channel):
        """
        Handle the event where the caller phone hears the ring tone.

        We don't want this. It's work to get all the values right, and
        when we do, this would look just like on_b_dial.
        Further, the work we do to get on_transfer right makes getting
        consistent on_a_dials right even harder.

        Args:
            channel (Channel):
        """
        channel._side = 'A'
        pass

    def _raw_b_dial(self, channel):
        """
        Handle the event where the callee phone starts to ring.

        Args:
            channel (Channel): The channel of the B side.
        """
        channel._side = 'B'

        if channel.is_sip:
            if 'ignore_b_dial' in channel.custom:
                # Notifications were already sent for this channel.
                # Unset the flag and move on.
                del (channel.custom['ignore_b_dial'])
                return

            a_chan = channel.get_dialing_channel()
            a_chan._side = 'A'

            if 'raw_blind_transfer' in a_chan.custom:
                # This is an interesting exception: we got a Blind
                # Transfer message earlier and recorded it in this
                # attribute. We'll translate this b_dial to first a
                # on_b_dial and then the on_transfer event.
                transferer = a_chan.custom.pop('raw_blind_transfer')

                target_chans = a_chan.get_dialed_channels()
                targets = [party.callerid for party in target_chans]

                for target in target_chans:
                    # To prevent notifications from being sent multiple times,
                    # we set a flag on all other channels except for the one
                    # starting to ring right now.
                    if target != channel:
                        target.custom['ignore_b_dial'] = True

                # We're going to want to simulate a pre-flight dial event for
                # consistency with blonde transfers. In this dial, the
                # transferer supposedly calls the person to who the call is
                # going to be redirected to.
                #
                # We need to use something for an substitute linkedid.
                # From Channel, we know for sure it's not the original
                # master channel, so we can use it's Uniqueid.
                self.on_b_dial(
                    call_id=channel.uniqueid,
                    caller=transferer.callerid,
                    to_number=a_chan.exten,
                    targets=targets,
                )

                self.on_cold_transfer(
                    call_id=channel.linkedid,
                    merged_id=channel.uniqueid,
                    redirector=transferer.callerid,
                    caller=a_chan.callerid,
                    to_number=transferer.exten,
                    targets=targets,
                )
            elif a_chan.is_connectab:
                # Since both A and B are being called and Asterisk itself is
                # calling, we need some special logic to make it work.
                caller, callee = a_chan.connectab_participants()
                real_a_chan = a_chan._fwd_local_bridge
                real_a_chan._callerid = a_chan.callerid.replace(
                    code=caller.callerid.code)

                self.on_b_dial(
                    call_id=a_chan._fwd_local_bridge.uniqueid,
                    # Use the data from the local a_chan, but pull the account
                    # code from the "caller" dialed by Asterisk.
                    caller=real_a_chan.callerid,
                    to_number=channel.callerid.number,
                    targets=[channel.callerid],
                )
            elif a_chan.is_sip:
                # We'll want to send one ringing event for all targets. So
                # let's figure out to whom a_chan has open dials. To ensure
                # only one event is raised, we'll check all the uniqueids and
                # only send an event for the channel with the lowest uniqueid.
                # if not a_chan.is_up:
                open_dials = a_chan.get_dialed_channels()
                targets = [dial.callerid for dial in open_dials]

                for b_chan in open_dials:
                    if b_chan == channel:
                        # Ensure a notification is only sent once.
                        self.on_b_dial(
                            call_id=channel.linkedid,
                            caller=a_chan.callerid,
                            to_number=a_chan.exten,
                            targets=targets,
                        )
                    else:
                        # To prevent notifications from being sent multiple
                        # times, we set a flag on all other channels except
                        # for the one starting to ring right now.
                        b_chan.custom['ignore_b_dial'] = True

    def _raw_in_call(self, channel, bridge, event):
        """
        Post-process a BridgeEnter event to notify of a call in progress.

        This function will check if the bridge already contains other SIP
        channels. If so, it's interpreted as a call between two channels
        being connected.

        WARNING: This function does not behave as desired for bridges with 3+
        parties, e.g. conference calls.

        Args:
            channel (Channel): The channel entering the bridge.
            bridge (Bridge): The bridge the channel enters.
            event (dict): The BridgeEnter event.
        """
        sip_peers = [peer for peer in bridge.peers if
                     peer.is_sip and peer != channel]

        if sip_peers:
            # Only calling channels have extensions, and Asterisk's exten 's'
            # means no extension.
            if channel.exten == 's':
                b_chan = channel

                a_chan = None
                for chan in sip_peers:
                    if chan.exten != 's':
                        a_chan = chan
                        break

                assert a_chan, ('Bridge {} does not have any calling '
                                'channels: {}'.format(
                                bridge.uniqueid, bridge.peers)
                                )
            else:
                a_chan = channel
                b_chan = sip_peers[0]

            # Set a flag to prevent the event from being fired again.
            # FIXME: Checking and setting is done on different channels?
            a_chan._is_picked_up = True

            self.on_up(
                call_id=event['Linkedid'],
                caller=a_chan.callerid,
                to_number=a_chan.exten,
                callee=b_chan.callerid,
            )

    def _raw_blonde_transfer(self, orig_transferer, second_transferer, event):
        """
        Handle the attended transfer event.

        Args:
            orig_transferer (Channel): The original channel is the channel
            which the redirector used to talk with the person who's being
            transferred.
            second_transferer (Channel): The target channel is the channel
            which the redirector used to set up the call to the person to
            whom the call is being transferred.
        """
        peer_one, peer_two = self._bridge_registry.get_by_uniqueid(
            event['OrigBridgeUniqueid']
        ).peers

        if peer_one.uniqueid == orig_transferer.uniqueid:
            transfer_source = peer_two
        elif peer_two.uniqueid == orig_transferer.uniqueid:
            transfer_source = peer_one
        else:
            raise AssertionError(
                'The OrigTransferer is not in the OrigBridge: {}'.format(event)
            )

        transfer_source._side = 'A'

        targets = [c_chan.callerid for c_chan
                   in second_transferer.get_dialed_channels()]

        self.on_cold_transfer(
            call_id=orig_transferer.linkedid,
            merged_id=second_transferer.linkedid,
            redirector=second_transferer.callerid,
            caller=transfer_source.callerid,
            to_number=transfer_source.exten,
            targets=targets,
        )

        orig_transferer.custom['suppress_hangup'] = True
        second_transferer.custom['suppress_hangup'] = True

    def _raw_attended_transfer(self, orig_transferer, second_transferer,
                               event):
        """
        Handle an attended transfer.

        Args:
            orig_transferer (Channel): The original channel is the channel
            which the redirector used to talk with the person who's being
            transferred.
            second_transferer (Channel): The target channel is the channel
            which the redirector used to set up the call to the person to
            whom the call is being transferred.
            event (dict): The data of the AttendedTransfer event.
        """
        target_bridge = self._bridge_registry.get_by_uniqueid(
            event['SecondBridgeUniqueid'])
        peer_one, peer_two = target_bridge.peers

        # The transfer is done, the original bridge is empty and SecondBridge
        # contain the channel we've transferred and the transfer target.
        if peer_one.linkedid == event['OrigTransfererLinkedid']:
            transfer_source = peer_one
            transfer_target = peer_two
        elif peer_two.linkedid == event['OrigTransfererLinkedid']:
            transfer_source = peer_two
            transfer_target = peer_one
        else:
            raise AssertionError()

        transfer_source._side = 'A'

        self.on_warm_transfer(
            call_id=transfer_source.linkedid,
            merged_id=transfer_target.linkedid,
            redirector=orig_transferer.callerid,
            caller=transfer_source.callerid,
            destination=transfer_target.callerid,
        )

        orig_transferer.custom['suppress_hangup'] = True
        second_transferer.custom['suppress_hangup'] = True

    def _raw_blind_transfer(self, event):
        """
        Handle a blind (cold) transfer event.

        This Transfer event is earlier than the dial. We mark it and
        wait for the b_dial event. In on_b_dial we send out both the
        on_b_dial and the on_transfer.

        Args:
            event (dict): The data of the BlindTransfer event.
        """
        transferer = self._registry.get_by_uniqueid(
            event['TransfererUniqueid'])
        transferee = self._registry.get_by_uniqueid(
            event['TransfereeUniqueid'])

        transferee.custom['raw_blind_transfer'] = transferer
        transferee._is_picked_up = False

        # Mark the original channel as ignored, so we don't report a hangup
        # just after the transfer.
        transferer.custom['suppress_hangup'] = True
        transferee._exten = event['Extension']

    def _raw_hangup(self, channel, event):
        """
        Handle a Hangup event from Asterisk.

        Args:
            channel (Channel): The channel which is hung up.
            event (Event): The data of the event.
        """
        if channel.is_sip:
            a_chan = channel.get_dialing_channel()

            if 'raw_blind_transfer' in channel.custom:
                # Panic! This channel had a blind transfer coming up but it's
                # being hung up! That probably means the blind transfer target
                # could not be reached.
                # Ideally, we would simulate a full blind transfer having been
                # completed but hanged up with an error. However, no channel
                # to the third party has been created.
                redirector = channel.custom.pop('raw_blind_transfer')

                if redirector.is_calling_chan:
                    a_chan = redirector
                    b_chan = channel
                else:
                    a_chan = channel
                    b_chan = redirector

                # TODO: Maybe give another status code than 'completed' here?
                self.on_a_hangup(a_chan.uniqueid, a_chan.callerid, b_chan.callerid.number, 'completed')

            elif 'ignore_a_hangup' in channel.custom:
                # This is a calling channel which performed an attended
                # transfer. Because the call has already been "hanged up"
                # with the transfer, we shouldn't send a hangup notification.
                pass

            elif 'suppress_hangup' in channel.custom:
                pass

            elif a_chan.is_connectab:
                # A called channel, in connectab both sip channels are 'called'.
                caller, callee = channel.connectab_participants()

                if callee.state != AST_STATE_DOWN:
                    # Depending on who hangs up, we get a different order of events,
                    # Setting these markers ensures only the first hangup is sent.
                    callee.custom['ignore_a_hangup'] = True
                    caller.custom['ignore_a_hangup'] = True

                    self.on_a_hangup(
                        a_chan._fwd_local_bridge.uniqueid,
                        caller.callerid.replace(number=a_chan.callerid.number),
                        callee.exten,
                        self._hangup_reason(callee, event)
                    )

            elif channel.is_calling_chan:
                # The caller is being disconnected, so we should notify the
                # user.
                self.on_a_hangup(
                    call_id=channel.linkedid,
                    caller=channel.callerid,
                    to_number=channel.exten,
                    reason=self._hangup_reason(channel, event),
                )

        # We've sent all relevant notifications regarding the channel
        # being gone, so we can forget it ourselves now as well.

        # Disconnect all channels linked to this channel.
        channel.do_hangup(event)

        # Remove the channel from our own list.
        self._registry.remove(channel)

        # If we don't have any channels, check whether we're completely clean.
        if not len(self._registry):
            self._reporter.trace_msg('(no channels left)')

    def _hangup_reason(self, channel, event):
        """
        Map the Asterisk hangup causes to easy to understand strings.

        Args:
            channel (Channel): The channel which is hung up.
            event (Event): The data of the event.
        """
        hangup_cause = int(event['Cause'])

        # See https://wiki.asterisk.org/wiki/display/AST/Hangup+Cause+Mappings
        if hangup_cause == AST_CAUSE_NORMAL_CLEARING:
            # If channel is not up, the call never really connected.
            # This happens when call confirmation is unsuccessful.
            if channel.is_up:
                return 'completed'
            else:
                return 'no-answer'
        elif hangup_cause == AST_CAUSE_USER_BUSY:
            return 'busy'
        elif hangup_cause in (AST_CAUSE_NO_USER_RESPONSE, AST_CAUSE_NO_ANSWER):
            return 'no-answer'
        elif hangup_cause == AST_CAUSE_ANSWERED_ELSEWHERE:
            return 'answered-elsewhere'
        elif hangup_cause == AST_CAUSE_CALL_REJECTED:
            return 'rejected'
        elif hangup_cause == AST_CAUSE_UNKNOWN:
            # Sometimes Asterisk doesn't set a proper hangup cause.
            # If our a_chan is already up, this probably means the
            # call was successful. If not, that means A hanged up,
            # which we assign the "cancelled" status.
            if channel.is_up:
                return 'completed'
            else:
                return 'cancelled'
        else:
            return 'failed'

    # ===================================================================
    # Actual event handlers you should override
    # ===================================================================

    def on_b_dial(self, call_id, caller, to_number, targets):
        """
        Gets invoked when the B side of a call is initiated.

        In the common case, calls in Asterisk consist of two sides: A
        calls Asterisk and Asterisk calls B. This event is fired when
        Asterisk performs the second step.

        Args:
            call_id (str): Unique call ID string.
            caller (CallerId): The initiator of the call.
            to_number (str): The number which was dialed by the user.
            targets (list): A list of recipients of the call.
        """
        self._reporter.trace_msg('{} ringing: {} --> {} ({})'.format(
            call_id, caller, to_number, targets))
        self._reporter.on_b_dial(call_id, caller, to_number, targets)

    def on_warm_transfer(self, call_id, merged_id, redirector, caller,
                         destination):
        """
        Gets invoked when an attended transfer is completed.

        In an attended transfer, one of the participants of a conversation
        calls a third participant, waits for the third party to answer, talks
        to the third party and then transfers their original conversation
        partner to the third party.

        Args:
            call_id (str): The unique ID of the resulting call.
            merged_id (str): The unique ID of the call which will end.
            redirector (CallerId): The caller ID of the party performing the
                transfer.
            caller (CallerId): The caller ID of the party which has been
                transferred.
            destination (CallerId): The caller ID of the party which
            received the
                transfer.
        """
        self._reporter.trace_msg(
            '{} <== {} attn xfer: {} <--> {} (through {})'.format(
                call_id, merged_id, caller, destination, redirector),
        )
        self._reporter.on_warm_transfer(
            call_id, merged_id, redirector, caller, destination)

    def on_cold_transfer(self, call_id, merged_id, redirector, caller,
                         to_number, targets):
        """
        Gets invoked when a blind or blonde transfer is completed.

        In a blind transfer, one of the call participant transfers their
        conversation partner to a third party. However, unlike with an
        attended transfer, the redirector doesn't wait for the other end to
        pick up, but just punches in the number and sends their conversation
        party away. Because of this, multiple phones may actually be addressed
        by this transfer, hence the multiple targets. The real participant can
        be recovered later on when someone answers the transferred call.

        A blonde is a middle road between blind transfers and attended
        transfers. With a blond transfer, the redirector requests an attended
        transfer but doesn't wait for the receiving end to pick up. Since the
        data of blind and blonde transfers looks identical, they don't have
        special hooks.

        Args:
            call_id (str): The unique ID of the resulting call.
            merged_id (str): The unique ID of the call which will end.
            redirector (CallerId): The caller ID of the party performing the
                transfer.
            caller (CallerId): The caller ID of the party which has been
                transferred.
            to_number (str): The number which was dialed by the user.
            targets (list): A list of CallerId objects whose phones are
                ringing for this transfer.
        """
        self._reporter.trace_msg(
            '{} <== {} bld xfer: {} <--> {} (through {})'.format(
                call_id, merged_id, caller, targets, redirector))

        self._reporter.on_cold_transfer(
            call_id, merged_id, redirector, caller, to_number, targets)

    def on_user_event(self, event):
        """Handle custom UserEvent messages from Asterisk.

        Adding user events to a dial plan is a useful way to send additional
        information to Cacofonisk. You could add additional user info,
        parameters used for processing the events and more.

        Args:
            event (Message): Dict-like object with all attributes in the event.
        """
        self._reporter.trace_msg('user_event: {}'.format(event))
        self._reporter.on_user_event(event)

    def on_up(self, call_id, caller, to_number, callee):
        """Gets invoked when a call is connected.

        When two sides have connected and engaged in a conversation, an "up"
        event is sent. Usually, this event is sent after a b_dial event
        (i.e. a phone is picked up after ringing) but after a blind or blonde
        transfer an "up" is sent for the two *remaining* parties.

        Args:
            call_id (str): Unique call ID string.
            caller (CallerId): The initiator of the call.
            to_number (str): The number which was dialed by the user.
            callee (CallerId): The recipient of the call.
        """
        self._reporter.trace_msg('{} up: {} --> {} ({})'.format(
            call_id, caller, to_number, callee))
        self._reporter.on_up(call_id, caller, to_number, callee)

    def on_a_hangup(self, call_id, caller, to_number, reason):
        """Gets invoked when a call is completed.

        There are two types of events which should be monitored to determine
        whether a call has ended: transfer and hangup. A hangup event is
        raised when the call is fully disconnected (no parties are connected).
        However, after a transfer has completed, the redirector of the
        transfer is also disconnected (as they quit the transfer).

        Args:
            call_id (str): Unique call ID string.
            caller (CallerId): The initiator of the call.
            to_number (str): The number which was dialed by the user.
            reason (str): Why the call ended (completed, no-answer, busy,
                failed, answered-elsewhere).
        """
        self._reporter.trace_msg('{} hangup: {} --> {} (reason: {})'.format(
            call_id, caller, to_number, reason))
        self._reporter.on_hangup(call_id, caller, to_number, reason)


class DebugEventHandler(EventHandler):
    """
    DebugChannel functions exactly like the default class:`EventHandler`. The
    only difference is that this EventHandler acts on all events, instead of
    dropping all events that are deemed 'not interesting'. This is usefull for
    creating debug logs.
    """
    INTERESTING_EVENTS = ('*',)


class NoOpEventHandler(DebugEventHandler):
    """
    NoOpEventHandler is a simple EventHandler which simply passes the events to
    the reporter without further processing. This is useful for generating
    logs, if regular event processing is not desired.
    """
    def on_event(self, event):
        self._reporter.trace_ami(event)


class NoOpSilentEventHandler(EventHandler):
    """
    NoOpEventHandler is a simple EventHandler which simply passes the events to
    the reporter without further processing. This is useful for generating
    logs, if regular event processing is not desired.
    """
    def on_event(self, event):
        self._reporter.trace_ami(event)
