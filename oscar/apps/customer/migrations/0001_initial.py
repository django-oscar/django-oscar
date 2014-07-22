# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import oscar.models.fields.autoslugfield
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CommunicationEventType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(populate_from=b'name', editable=False, max_length=128, separator='_', blank=True, help_text='Code used for looking up this event programmatically', unique=True, verbose_name='Code')),
                ('name', models.CharField(help_text='This is just used for organisational purposes', max_length=255, verbose_name='Name')),
                ('category', models.CharField(default='Order related', max_length=255, verbose_name='Category')),
                ('email_subject_template', models.CharField(max_length=255, null=True, verbose_name='Email Subject Template', blank=True)),
                ('email_body_template', models.TextField(null=True, verbose_name='Email Body Template', blank=True)),
                ('email_body_html_template', models.TextField(help_text='HTML template', null=True, verbose_name='Email Body HTML Template', blank=True)),
                ('sms_template', models.CharField(help_text='SMS template', max_length=170, null=True, verbose_name='SMS Template', blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date Created')),
                ('date_updated', models.DateTimeField(auto_now=True, verbose_name='Date Updated')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Communication event type',
                'verbose_name_plural': 'Communication event types',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('subject', models.TextField(max_length=255, verbose_name='Subject')),
                ('body_text', models.TextField(verbose_name='Body Text')),
                ('body_html', models.TextField(verbose_name='Body HTML', blank=True)),
                ('date_sent', models.DateTimeField(auto_now_add=True, verbose_name='Date Sent')),
                ('user', models.ForeignKey(verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Email',
                'verbose_name_plural': 'Emails',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('subject', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('category', models.CharField(max_length=255, blank=True)),
                ('location', models.CharField(default=b'Inbox', max_length=32, choices=[(b'Inbox', 'Inbox'), (b'Archive', 'Archive')])),
                ('date_sent', models.DateTimeField(auto_now_add=True)),
                ('date_read', models.DateTimeField(null=True, blank=True)),
                ('recipient', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': (b'-date_sent',),
                'abstract': False,
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductAlert',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(db_index=True, max_length=75, verbose_name='Email', blank=True)),
                ('key', models.CharField(db_index=True, max_length=128, verbose_name='Key', blank=True)),
                ('status', models.CharField(default=b'Active', max_length=20, verbose_name='Status', choices=[(b'Unconfirmed', 'Not yet confirmed'), (b'Active', 'Active'), (b'Cancelled', 'Cancelled'), (b'Closed', 'Closed')])),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('date_confirmed', models.DateTimeField(null=True, verbose_name='Date confirmed', blank=True)),
                ('date_cancelled', models.DateTimeField(null=True, verbose_name='Date cancelled', blank=True)),
                ('date_closed', models.DateTimeField(null=True, verbose_name='Date closed', blank=True)),
                ('product', models.ForeignKey(to='catalogue.Product')),
                ('user', models.ForeignKey(verbose_name='User', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Product alert',
                'verbose_name_plural': 'Product alerts',
            },
            bases=(models.Model,),
        ),
    ]
