from django.utils.translation import ngettext_lazy
from django_tables2 import Table
from django.utils.safestring import mark_safe

class DashboardTable(Table):
    caption = None  # Keep default caption as None
    icon_svg = None

    def get_caption_display(self):
        try:
            if hasattr(self, 'caption_text'):
                caption = self.caption_text
            else:
                caption = str(self.caption) if self.caption else ''
                
            count = f"<span>({self.paginator.count})</span>" if self.paginator else "<span>(0)</span>"
            
            if self.icon_svg:
                return mark_safe(f'{self.icon_svg}&nbsp;&nbsp;{caption}&nbsp;{count}')
            return f'{caption} {count}'
        except TypeError:
            return self.caption

    class Meta:
        template_name = "oscar/dashboard/table.html"
        attrs = {"class": "table table-striped table-bordered"}