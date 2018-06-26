class Bridge(object):
    def __init__(self, event, channel_manager):
        """
        Create a new bridge object.

        Args:
            event (Event):
            channel_manager (EventHandler):
        """
        self._channel_manager = channel_manager

        self._id = event['BridgeUniqueid']
        self._peers = set()

    def enter(self, event):
        channel = self._channel_manager._registry.get_by_uniqueid(event['Uniqueid'])
        self._peers.add(channel)

    def leave(self, event):
        channel = self._channel_manager._registry.get_by_uniqueid(event['Uniqueid'])

        assert channel in self._peers

        self._peers.remove(channel)

    @property
    def peers(self):
        return self._peers

    @property
    def uniqueid(self):
        return self._id

    def __len__(self):
        return len(self._peers)

    def __repr__(self):
        return '<Bridge(id={self._id},peers={peers})>'.format(
            self=self,
            peers=','.join([chan.name for chan in self._peers]),
        )


class BridgeRegistry(object):
    def __init__(self, channel_manager):
        self._channel_manager = channel_manager
        self._bridges = {}

    def create(self, event):
        assert event['BridgeUniqueid'] not in self._bridges

        self._bridges[event['BridgeUniqueid']] = Bridge(event, self._channel_manager)

    def destroy(self, event):
        bridge = self.get_by_uniqueid(event['BridgeUniqueid'])

        assert len(bridge) == 0

        del self._bridges[event['BridgeUniqueid']]

    def get_by_uniqueid(self, uniqueid):
        try:
            return self._bridges[uniqueid]
        except KeyError:
            raise MissingBridgeUniqueid(uniqueid)


class MissingBridgeUniqueid(KeyError):
    pass
