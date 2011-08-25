from django.db import models


class CommunicationTypeManager(models.Manager):
    
    def get_and_render(self, code, context):
        """
        Return a dictionary of rendered messages, ready for sending
        """
        try:
            commtype = self.get(code=code)
        except self.model.DoesNotExist:
            commtype = self.model(code=code)
        return commtype.get_messages(context)
