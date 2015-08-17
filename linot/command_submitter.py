import interfaces


class CommandSubmitter:
    def __init__(self, if_name, code):
        self.interface_name = if_name
        self.code = code

    def send_message(self, msg):
        interface = interfaces.get(self.interface_name)
        return interface.send_message(self, msg)

    def get_display_name(self):
        interface = interfaces.get(self.interface_name)
        return interface.get_display_name(self)

    def __unicode__(self):
        return unicode(self.get_display_name())

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash(str(self.interface_name) + str(self.code))
