from django.template.defaultfilters import date


class ReportGenerator(object):
    """
    Top-level class that needs to be subclassed to provide a 
    report generator.
    """
    filename_template = 'report-%s-to-%s.csv'
    mimetype = 'text/csv'
    code = ''
    description = '<insert report description>'
    
    def __init__(self, **kwargs):
        if 'start_date' in kwargs and 'end_date' in kwargs:
            self.start_date = kwargs['start_date']
            self.end_date = kwargs['end_date']
    
    def generate(self, response):
        pass
 
    def filename(self):
        """
        Returns the filename for this report
        """
        return self.filename_template % (self.start_date, self.end_date)
    
    def is_available_to(self, user):
        """
        Checks whether this report is available to this user
        """
        return user.is_staff

    def format_datetime(self, dt):
        return date(dt, 'DATETIME_FORMAT')

    def format_date(self, d):
        return date(d, 'DATE_FORMAT')