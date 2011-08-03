from django.db.models.signals import post_init, pre_save, post_save
from django.dispatch import receiver
from oscar.apps.catalogue.abstract_models import ProductAttributesContainer
from django.conf import settings

if getattr(settings, 'OSCAR_ENABLE_ATTRIBUTE_BINDING', False):
    @receiver(post_init)
    def attr_post_init(sender, **kwargs):
        model = '%s.%s' % (sender._meta.app_label, sender._meta.object_name)
        if model == 'catalogue.Product':
            instance = kwargs['instance']
            container = ProductAttributesContainer(product=instance)
            instance.attr = container
    
    @receiver(pre_save)
    def attr_pre_save(sender, **kwargs):
        model = '%s.%s' % (sender._meta.app_label, sender._meta.object_name)
        if model == 'catalogue.Product':
            instance = kwargs['instance']
            instance.attr.validate_attributes()
    
    @receiver(post_save)
    def attr_post_save(sender, **kwargs):
        model = '%s.%s' % (sender._meta.app_label, sender._meta.object_name)
        if model == 'catalogue.Product':    
            instance = kwargs['instance']
            instance.attr.save()                
