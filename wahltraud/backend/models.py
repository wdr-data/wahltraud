from django.db import models
from django.utils import timezone


class Entry(models.Model):

    class Meta:
        verbose_name = 'Eintrag'
        verbose_name_plural = 'Einträge'

    title = models.CharField('Titel', max_length=200, null=False)
    text = models.CharField('Text', max_length=640, null=False)
    link_one_title = models.CharField('Link 1 - Titel', max_length=20, null=True, blank=True)
    link_one_url = models.CharField('Link 1 - URL', max_length=256, null=True, blank=True)
    link_two_title = models.CharField('Link 2 - Titel', max_length=20, null=True, blank=True)
    link_two_url = models.CharField('Link 2 - URL', max_length=256, null=True, blank=True)
    link_three_title = models.CharField('Link 3 - Titel', max_length=20, null=True, blank=True)
    link_three_url = models.CharField('Link 3 - URL', max_length=256, null=True, blank=True)
    media = models.FileField('Medien-Anhang', null=True, blank=True)
    pub_date = models.DateTimeField('Veröffentlicht am', default=timezone.now)

    def __str__(self):
        return '%s - %s' % (self.pub_date.strftime('%d.%m.%Y'), self.title)
