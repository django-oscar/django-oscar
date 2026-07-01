from django.db import models


class CommunicationTypeManager(models.Manager):
    def get_and_render(self, code, context):
        """
        Return a dictionary of rendered messages, ready for sending.

        This method wraps around whether an instance of this event-type exists
        in the database.  If not, then an instance is created on the fly and
        used to generate the message contents.
        """
        try:
            commtype = self.get(code=code)
        except self.model.DoesNotExist:
            commtype = self.model(code=code)
        return commtype.get_messages(context)
