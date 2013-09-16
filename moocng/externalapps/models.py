# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from moocng.courses.models import Course
from moocng.externalapps.exceptions import InstanceLimitReached
from moocng.externalapps.registry import ExternalAppRegistry
from moocng.externalapps.validators import validate_slug, validate_forbidden_words


externalapps = ExternalAppRegistry()

def get_instance_types():
    return [(key, key) for key in settings.MOOCNG_EXTERNALAPPS.keys()]


class ExternalApp(models.Model):

    CREATED = 1
    NOT_CREATED = 2
    IN_PROGRESS = 3
    ERROR = 4

    STATUSES = (
        (CREATED, _('Created')),
        (NOT_CREATED, _('Not Created')),
        (IN_PROGRESS, _('In Progress')),
        (ERROR, _('Error')),
    )

    course = models.ForeignKey(
        Course,
        verbose_name=_('Course'),
        related_name='external_apps',
        blank=False,
        null=True)

    app_name = models.CharField(
        verbose_name=_('External app name'),
        max_length=200,
        null=False,
        blank=False,
    )

    base_url = models.TextField(
        verbose_name=_('Base url of the instance'),
        null=False,
        blank=False,
    )

    ip_address = models.IPAddressField(
        verbose_name=_('IP address of the instance'),
        null=False,
        blank=False,
    )

    slug = models.SlugField(
        verbose_name=_('Slug for the instance'),
        null=False,
        blank=False,
        unique=True,
        validators=[validate_slug, validate_forbidden_words]
    )

    status = models.SmallIntegerField(
        verbose_name=_('Creation status of the instance'),
        null=False,
        blank=False,
        choices=STATUSES,
        default=NOT_CREATED,
    )

    instance_type = models.CharField(
        verbose_name=_('Type of instance'),
        null=False,
        blank=False,
        max_length=50,
        choices=get_instance_types(),
        default='askbot',
    )


    class Meta:
        verbose_name = _('external app')
        verbose_name_plural = _('external apps')

    def __unicode__(self):
        return u'%s:%s' % (self.app_name, self.ip_address)

    def url(self):
        return u'%s/%s' % (self.base_url, self.slug)

    def clean(self):
        external_app = externalapps.get_app_by_name(self.instance_type)
        if external_app:
            try:
                if not self.id:
                    instance_assigned = external_app.get_instance(self)
                    self.ip_address = instance_assigned[0]
                    self.base_url = instance_assigned[1]
                    self.status = self.IN_PROGRESS
                    self.instance_type = external_app._meta.instance_type
            except InstanceLimitReached:
                raise ValidationError(_('There are no instances available'))
        else:
            msg = _('There is no registered class to manage "%s" external app' % self.app_name)
            raise ValidationError(msg)
