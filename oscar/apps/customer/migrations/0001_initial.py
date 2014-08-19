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
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('code', oscar.models.fields.autoslugfield.AutoSlugField(editable=False, verbose_name='Code', blank=True, max_length=128, separator='_', populate_from='name', help_text='Code used for looking up this event programmatically', unique=True)),
                ('name', models.CharField(verbose_name='Name', help_text='This is just used for organisational purposes', max_length=255)),
                ('category', models.CharField(verbose_name='Category', default='Order related', max_length=255)),
                ('email_subject_template', models.CharField(verbose_name='Email Subject Template', blank=True, null=True, max_length=255)),
                ('email_body_template', models.TextField(verbose_name='Email Body Template', blank=True, null=True)),
                ('email_body_html_template', models.TextField(verbose_name='Email Body HTML Template', blank=True, help_text='HTML template', null=True)),
                ('sms_template', models.CharField(verbose_name='SMS Template', blank=True, help_text='SMS template', null=True, max_length=170)),
                ('date_created', models.DateTimeField(verbose_name='Date Created', auto_now_add=True)),
                ('date_updated', models.DateTimeField(verbose_name='Date Updated', auto_now=True)),
            ],
            options={
                'verbose_name': 'Communication event type',
                'verbose_name_plural': 'Communication event types',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Email',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('subject', models.TextField(verbose_name='Subject', max_length=255)),
                ('body_text', models.TextField(verbose_name='Body Text')),
                ('body_html', models.TextField(verbose_name='Body HTML', blank=True)),
                ('date_sent', models.DateTimeField(verbose_name='Date Sent', auto_now_add=True)),
                ('user', models.ForeignKey(verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Email',
                'verbose_name_plural': 'Emails',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('subject', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('category', models.CharField(blank=True, max_length=255)),
                ('location', models.CharField(choices=[('Inbox', 'Inbox'), ('Archive', 'Archive')], default='Inbox', max_length=32)),
                ('date_sent', models.DateTimeField(auto_now_add=True)),
                ('date_read', models.DateTimeField(blank=True, null=True)),
                ('recipient', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('sender', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
                'ordering': ('-date_sent',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductAlert',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('email', models.EmailField(verbose_name='Email', blank=True, db_index=True, max_length=75)),
                ('key', models.CharField(verbose_name='Key', blank=True, db_index=True, max_length=128)),
                ('status', models.CharField(verbose_name='Status', choices=[('Unconfirmed', 'Not yet confirmed'), ('Active', 'Active'), ('Cancelled', 'Cancelled'), ('Closed', 'Closed')], default='Active', max_length=20)),
                ('date_created', models.DateTimeField(verbose_name='Date created', auto_now_add=True)),
                ('date_confirmed', models.DateTimeField(verbose_name='Date confirmed', blank=True, null=True)),
                ('date_cancelled', models.DateTimeField(verbose_name='Date cancelled', blank=True, null=True)),
                ('date_closed', models.DateTimeField(verbose_name='Date closed', blank=True, null=True)),
                ('product', models.ForeignKey(to='catalogue.Product')),
                ('user', models.ForeignKey(verbose_name='User', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'verbose_name': 'Product alert',
                'verbose_name_plural': 'Product alerts',
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
