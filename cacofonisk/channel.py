from .callerid import CallerId
from .constants import (
    AST_STATE_DIALING,
    AST_STATE_DOWN,
    AST_STATE_RING,
    AST_STATE_RINGING,
    AST_STATE_UP)


class MissingChannel(KeyError):
    pass


class MissingUniqueid(KeyError):
    pass


class Channel(object):
    """
    A Channel holds Asterisk channel state.

    It can be renamed, linked, tied to other channels, bridged,
    masqueraded and so on. All of the above is typical low level
    Asterisk channel behaviour.
    """

    def __init__(self, event, channel_manager):
        """
        Create a new channel instance.

        Takes a channel manager managing it as argument for callbacks.

        Args:
            event (Dict): A dictionary with Asterisk AMI data. Only the
                Newchannel event should be passed. The EventHandler
                does the other translations.
            channel_manager (EventHandler): The channel manager that takes
                the AMI events and passes state changes to individual channels
                or groups of channels at once.

        Example::

            channel = Channel(
                event={
                    "AccountCode": "126680001",
                    "CallerIDName": "<unknown>",
                    "CallerIDNum": "126680001",
                    "Channel": "SIP/126680001-0000000a",
                    "ChannelState": "0",
                    "ChannelStateDesc": "Down",
                    "ConnectedLineName": "<unknown>",
                    "ConnectedLineNum": "<unknown>",
                    "Context": "osvpi_account",
                    "Event": "Newchannel",
                    "Exten": "202",
                    "Language": "en",
                    "Linkedid": "07764b6803cf-1528985135.175",
                    "Priority": "1",
                    "Privilege": "call,all",
                    "SystemName": "07764b6803cf",
                    "Uniqueid": "07764b6803cf-1528985135.175",
                    "content": ""
                },
                channel_manager=channel_manager)
        """
        self._channel_manager = channel_manager

        # Uses of this instance may put data in the custom dict.
        self.custom = {}

        self._name = event['Channel']
        self._id = event['Uniqueid']
        self._linkedid = event['Linkedid']
        self._fwd_local_bridge = None
        self._back_local_bridge = None
        self.back_dial = None
        self.fwd_dials = []
        self._bridge = None

        self._state = int(event['ChannelState'])  # 0, Down
        self._exten = event['Exten']

        self._side = None
        self._is_picked_up = False

        self._callerid = CallerId(
            code=int(event['AccountCode'] or 0),
            name=event['CallerIDName'],
            number=event['CallerIDNum'],
        )

        self._connected_line = CallerId(
            name=event['ConnectedLineName'],
            number=event['ConnectedLineNum']
        )

        self._trace('new {!r}'.format(self))

    def __repr__(self):
        return (
            '<Channel('
            'name={self._name!r} '
            'id={self._id!r} '
            'linkedid={self._linkedid!r} '
            'forward_local_bridge={next} '
            'backward_local_bridge={prev} '
            'state={self._state} '
            'cli={self.callerid!r} '
            'exten={self._exten!r})>').format(
            self=self,
            next=(self._fwd_local_bridge and self._fwd_local_bridge.name),
            prev=(self._back_local_bridge and self._back_local_bridge.name))

    def _trace(self, msg):
        """
        _trace can be used to follow interesting events.
        """
        pass

    @property
    def is_connectab(self):
        """
        Check if this channel is part of a ConnectAB call.

        Returns:
            bool: True if this is the origin channel of ConnectAB.
        """
        # ConnectAB is a channel setup specific to VoIPGRID, which
        # is used for click-to-dial and call-me-now functionality.
        # Basically, an ORIGINATE call is sent to Asterisk, which
        # will then dial participant 1, wait for the participant to
        # pick up, then call participant 2 and link the two together.
        #
        # Since both A and B are being called and Asterisk itself is
        # calling, we need some special logic to make it work.
        # local_a is the origin channel of the dial to our caller.
        local_a = self.get_dialing_channel()

        # With a regular call, the dialing channel is a SIP channel, but with
        # a ConnectAB call, the dialing channel is created by Asterisk so it's
        # a local channel.
        # This dialing channel is locally bridged with another channel and both
        # local channels have outbound dials to both legs of a conversation.
        return (
                local_a._fwd_local_bridge and
                local_a.fwd_dials and
                local_a._fwd_local_bridge.fwd_dials
        )

    @property
    def is_local(self):
        """
        Whether the current channel is a local channel.

        A connection to Asterisk consist of two parts, an internal connection
        and an external connection. The internal connection is prefixed
        with 'Local/', whereas a external connection is prefixed with 'SIP/'.

        Returns:
            bool: True if the channel is local, false otherwise.
        """
        return self.name.startswith('Local/')

    @property
    def uniqueid(self):
        return self._id

    @property
    def linkedid(self):
        return self._linkedid

    @property
    def name(self):
        return self._name

    @property
    def callerid(self):
        return self._callerid

    @property
    def is_up(self):
        return self._state == AST_STATE_UP

    @property
    def state(self):
        return self._state

    @property
    def exten(self):
        """
        Get the extension of the channel.

        For calling channels, the extension is the phone number which was
        dialed by the user.

        Returns:
            str: The channel extension.
        """
        return self._exten

    @property
    def is_calling_chan(self):
        """
        Check whether this channel is a calling other channels.

        Returns:
            bool: True if this channel is calling other channels, else False.
        """
        return self._side == 'A'

    @property
    def is_called_chan(self):
        """
        Check whether this channel is being called by other channels.

        Returns:
            bool: True if this channel is being called, False otherwise.
        """
        return self._side == 'B'

    def set_state(self, event):
        """
        Update the ChannelState of this channel from the given event.

        Reads the ChannelState from the given event and write it to this
        channel. It will also call any relevant methods on EventHandler.

        Args:
            event (dict): A dictionary containing an AMI event.

        Example event:

            <Message CallerIDName='Foo bar' CallerIDNum='+31501234567'
            Channel='SIP/voipgrid-siproute-dev-0000000c' ChannelState='4'
            ChannelStateDesc='Ring' ConnectedLineName=''
            ConnectedLineNum='' Event='Newstate' Privilege='call,all'
            Uniqueid='vgua0-dev-1442239323.24' content=''>

        Asterisk ChannelStates:

            AST_STATE_DOWN = 0,
            AST_STATE_RESERVED = 1,
            AST_STATE_OFFHOOK = 2,
            AST_STATE_DIALING = 3,
            AST_STATE_RING = 4,
            AST_STATE_RINGING 5,
            AST_STATE_UP = 6,
            AST_STATE_BUSY = 7,
            AST_STATE_DIALING_OFFHOOK = 8,
            AST_STATE_PRERING = 9
        """
        old_state = self._state
        self._state = int(event['ChannelState'])  # 4=Ring, 6=Up
        assert old_state != self._state
        self._trace('set_state {} -> {}'.format(old_state, self._state))

        if not self.is_local:
            if (
                    old_state == AST_STATE_DOWN and
                    self._state in (
                        AST_STATE_DIALING, AST_STATE_RING, AST_STATE_UP
                    )
            ):
                self._channel_manager._raw_a_dial(self)
            elif (
                    old_state == AST_STATE_DOWN and
                    self._state == AST_STATE_RINGING
            ):
                self._channel_manager._raw_b_dial(self)

    def set_callerid(self, event):
        """
        set_callerid sets a class:`CallerId` object as attr:`_callerid`
        according to the relevant variables in `event`.

        Args:
            event (dict): A dictionary containing an AMI event.

        Example event:

            <Message CID-CallingPres='1 (Presentation Allowed, Passed
            Screen)' CallerIDName='Foo bar' CallerIDNum='+31501234567'
            Channel='SIP/voipgrid-siproute-dev-0000000c'
            Event='NewCallerid' Privilege='call,all'
            Uniqueid='vgua0-dev-1442239323.24' content=''>
        """
        old_cli = str(self._callerid)
        if event['CallerIDNum'] == str(self._callerid.code):
            # If someone uses call pickups, the CallerIDNum will be the
            # same as the AccountCode. However, broadcasting that is a bit
            # of a security leak.
            # Instead, we ignore this new number and use whatever we already
            # have.
            caller_id_number = self._callerid.number
        else:
            caller_id_number = event['CallerIDNum']

        self._callerid = self._callerid.replace(
            name=event['CallerIDName'],
            number=caller_id_number,
            is_public=('Allowed' in event['CID-CallingPres']),
        )

        self._trace('set_callerid {} -> {}'.format(old_cli, self._callerid))

    def set_connected_line(self, event):
        """
        Update the ConnectedLine information of this call.

        Args:
            event (Event): A NewConnectedLine event about this channel.
        """
        old_connected_line = self._connected_line

        self._connected_line = self._connected_line.replace(
            name=event['ConnectedLineName'],
            number=event['ConnectedLineNum'],
        )

        self._trace('set_connected_line {} -> {}'.format(
            old_connected_line, self._connected_line)
        )

    def set_accountcode(self, event):
        """
        set_accountcode sets the code of the _callerid to the 'Accountcode'
        defined
        in `event`.

        Args:
            event (dict): A dictionary containing an AMI event.

        Example event:

            <Message AccountCode='12668'
            Channel='SIP/voipgrid-siproute-dev-0000000c'
            Event='NewAccountCode' Privilege='call,all'
            Uniqueid='vgua0-dev-1442239323.24' content=''>
        """
        if not self._callerid.code:
            old_accountcode = self._callerid.code
            self._callerid = self._callerid.replace(
                code=int(event['AccountCode']))
            self._trace('set_accountcode {} -> {}'.format(
                old_accountcode, self._callerid.code))
        else:
            self._trace('set_accountcode ignored {} -> {}'.format(
                self._callerid.code, event['AccountCode'])
            )

    def connectab_participants(self):
        """
        Extract the real caller and callee channels of a ConnectAB call.
        """
        # First, we need to find the local channels which Asterisk uses to
        # dial out of the participants.
        local_a = self.get_dialing_channel()
        local_b = local_a._fwd_local_bridge

        # Then, we can get the channels being dialed by Asterisk.
        callee = local_a.fwd_dials[0]
        caller = local_b.fwd_dials[0]
        return caller, callee

    def do_hangup(self, event):
        """
        do_hangup clears clears all related channel and raises an error if any
        channels were bridged.

        Args:
            event (dict): A dictionary containing an AMI event.
        """
        # Remove the bridges.
        if self._fwd_local_bridge:
            self._fwd_local_bridge._back_local_bridge = None

        if self._back_local_bridge:
            self._back_local_bridge._fwd_local_bridge = None

        # Remove the dials.
        # if self.back_dial:
        #     self.back_dial.fwd_dials.remove(self)
        #     self.back_dial = None

    def do_localbridge(self, other):
        """
        do_localbridge sets `self` as attr:`_back_local_bridge` on `other`
        and other as attr:`_fwd_local_bridge` on `self`.

        Args:
            other (Channel): An instance of class:`Channel`.

        Example event:

            <Message
            Channel1='Local/ID2@osvpi_route_phoneaccount-00000006;1'
            Channel2='Local/ID2@osvpi_route_phoneaccount-00000006;2'
            Context='osvpi_route_phoneaccount' Event='LocalBridge'
            Exten='ID2' LocalOptimization='Yes' Privilege='call,all'
            Uniqueid1='vgua0-dev-1442239323.25'
            Uniqueid2='vgua0-dev-1442239323.26' content=''>
        """
        assert self._fwd_local_bridge is None, self._fwd_local_bridge
        assert self._back_local_bridge is None, self._back_local_bridge
        assert other._fwd_local_bridge is None, other._fwd_local_bridge
        assert other._back_local_bridge is None, other._back_local_bridge

        self._fwd_local_bridge = other
        other._back_local_bridge = self

        self._trace('do_localbridge -> {!r}'.format(other))

    def get_dialing_channel(self):
        """
        Figure out on whose channel's behalf we're calling.

        When a channel is not bridged yet, you can use this on the
        B-channel to figure out which A-channel initiated the call.
        """
        if self.back_dial:
            # Check if we are being dialed.
            a_chan = self.back_dial
        else:
            # This is the root channel.
            a_chan = None

        # If our a_chan has a local bridge, use the back part of that bridge
        # to check for further dials.
        if a_chan and a_chan._back_local_bridge:
            a_chan = a_chan._back_local_bridge

        # If we have an incoming channel, recurse through the channels to find
        # the true origin channel. If we don't have one, it means we're the
        # origin channel.
        return a_chan.get_dialing_channel() if a_chan else self

    def get_dialed_channels(self):
        """
        Figure out which channels are calling on our behalf.

        When a channel is not bridged yet, you can use this on the
        A-channel to find out which channels are dialed on behalf of
        this channel.

        It works like this:

        * A-channel (this) has a list of _fwd_dials items (open
          dials).
        * We loop over those (a list of uniqueids) and find the
          corresponding channels.
        * Those channels may be SIP channels, or they can be local
          channels, in which case we have to look further (by calling
          this function on those channels).
        """
        b_channels = set()

        if self._fwd_local_bridge:
            b_chans = self._fwd_local_bridge.fwd_dials
        else:
            b_chans = self.fwd_dials

        for b_chan in b_chans:
            # Likely, b_chan._fwd_local_bridge is None, in which case we're
            # looking at a real tech channel (non-Local).
            # Or, the b_chan has one _fwd_local_bridge, after which we have
            # to call this function again.
            if b_chan._fwd_local_bridge:
                b_chan = b_chan._fwd_local_bridge

                assert not b_chan._fwd_local_bridge, (
                    'Since when does asterisk do double links? b_chan={!r}'
                    .format(b_chan)
                )

                b_channels.update(b_chan.get_dialed_channels())
            else:
                assert not b_chan.fwd_dials
                b_channels.add(b_chan)

        return b_channels

    def sync_data(self, event):
        if 'Linkedid' in event:
            self._linkedid = event['Linkedid']

        if 'CallerIDNum' in event:
            self._callerid = self._callerid.replace(
                name=event['CallerIDName'],
                number=event['CallerIDNum'],
            )

        if 'CID-CallingPres' in event:
            self._callerid = self._callerid.replace(
                is_public=('Allowed' in event['CID-CallingPres']),
            )

        if 'ConnectedLineNum' in event:
            self._connected_line = self._connected_line.replace(
                name=event['ConnectedLineName'],
                number=event['ConnectedLineNum'],
            )


class ChannelRegistry(object):
    """
    ChannelRegistry stores the channels tracked by EventHandler.

    ChannelRegistry exposes methods to add and remove channels and to
    retrieve them by attributes like their name and uniqueid.
    """

    def __init__(self):
        self._channels_by_name = {}
        self._channels_by_uniqueid = {}

    def add(self, channel):
        """
        Add the channel to the registry.

        Args:
            channel (Channel): The channel to register.
        """
        self._channels_by_name[channel.name] = channel
        self._channels_by_uniqueid[channel.uniqueid] = channel

    def get_by_uniqueid(self, uniqueid):
        """
        Get the channel with the given UniqueID.

        Args:
            uniqueid (string): The UniqueID to look up.

        Returns:
            Channel: The channel with the given ID.
        """
        if uniqueid in self._channels_by_uniqueid:
            return self._channels_by_uniqueid[uniqueid]
        else:
            raise MissingUniqueid(uniqueid)

    def get_by_name(self, name):
        """
        Get the channel with the given channel name.

        Args:
            name (string): The name of the channel.

        Returns:
            Channel: The channel with the given name.
        """
        if name in self._channels_by_name:
            return self._channels_by_name[name]
        else:
            raise MissingChannel(name)

    def remove(self, channel):
        """
        Remove a channel from the registry.

        Args:
            channel (Channel): The channel to remove.
        """
        if channel.name in self._channels_by_name:
            del (self._channels_by_name[channel.name])

        if channel.uniqueid in self._channels_by_uniqueid:
            del (self._channels_by_uniqueid[channel.uniqueid])

        if not self._channels_by_name:
            assert not self._channels_by_uniqueid

    def __len__(self):
        """
        Get the number of channels currently in the registry.

        Returns:
            int: The number of channels.
        """
        return len(self._channels_by_name)
