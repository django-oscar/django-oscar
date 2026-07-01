# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models, migrations
import oscar.models.fields.autoslugfield
from django.utils.module_loading import import_string
from django.conf import settings

models_AutoField = import_string(settings.DEFAULT_AUTO_FIELD)



class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CommunicationEventType',
            fields=[
                ('id', models_AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(populate_from='name', unique=True, verbose_name='Code', editable=False, separator='_', max_length=128, help_text='Code used for looking up this event programmatically', blank=True)),
                ('name', models.CharField(verbose_name='Name', max_length=255, help_text='This is just used for organisational purposes')),
                ('category', models.CharField(default='Order related', max_length=255, verbose_name='Category', choices=[('Order related', 'Order related'), ('User related', 'User related')])),
                ('email_subject_template', models.CharField(verbose_name='Email Subject Template', max_length=255, blank=True, null=True)),
                ('email_body_template', models.TextField(blank=True, verbose_name='Email Body Template', null=True)),
                ('email_body_html_template', models.TextField(verbose_name='Email Body HTML Template', blank=True, help_text='HTML template', null=True)),
                ('sms_template', models.CharField(verbose_name='SMS Template', max_length=170, help_text='SMS template', blank=True, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('date_updated', models.DateTimeField(auto_now=True, verbose_name='Date Updated')),
            ],
            options={
                'verbose_name_plural': 'Communication event types',
                'verbose_name': 'Communication event type',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models_AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.TextField(max_length=255, verbose_name='Subject')),
                ('body_text', models.TextField(verbose_name='Body Text')),
                ('body_html', models.TextField(verbose_name='Body HTML', blank=True)),
                ('date_sent', models.DateTimeField(auto_now_add=True, verbose_name='Date Sent')),
                ('user', models.ForeignKey(verbose_name='User', related_name='emails', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'Emails',
                'verbose_name': 'Email',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models_AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('category', models.CharField(max_length=255, blank=True)),
                ('location', models.CharField(default='Inbox', max_length=32, choices=[('Inbox', 'Inbox'), ('Archive', 'Archive')])),
                ('date_sent', models.DateTimeField(auto_now_add=True)),
                ('date_read', models.DateTimeField(blank=True, null=True)),
                ('recipient', models.ForeignKey(related_name='notifications', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('sender', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('-date_sent',),
                'verbose_name_plural': 'Notifications',
                'verbose_name': 'Notification',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductAlert',
            fields=[
                ('id', models_AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=75, db_index=True, verbose_name='Email', blank=True)),
                ('key', models.CharField(max_length=128, db_index=True, verbose_name='Key', blank=True)),
                ('status', models.CharField(default='Active', max_length=20, verbose_name='Status', choices=[('Unconfirmed', 'Not yet confirmed'), ('Active', 'Active'), ('Cancelled', 'Cancelled'), ('Closed', 'Closed')])),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('date_confirmed', models.DateTimeField(blank=True, verbose_name='Date confirmed', null=True)),
                ('date_cancelled', models.DateTimeField(blank=True, verbose_name='Date cancelled', null=True)),
                ('date_closed', models.DateTimeField(blank=True, verbose_name='Date closed', null=True)),
                ('product', models.ForeignKey(to='catalogue.Product', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(null=True, verbose_name='User', related_name='alerts', to=settings.AUTH_USER_MODEL, blank=True, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'Product alerts',
                'verbose_name': 'Product alert',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
