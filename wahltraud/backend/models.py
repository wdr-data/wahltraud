from django.db import models
from django.utils import timezone


class Entry(models.Model):

    class Meta:
        verbose_name = 'Eintrag'
        verbose_name_plural = 'Einträge'

    title = models.CharField('Titel', max_length=200, null=False)
    text = models.CharField('Text', max_length=640, null=False)
    link_one = models.ForeignKey(
        'self', verbose_name='Link 1', related_name='+', null=True, blank=True)
    link_two = models.ForeignKey(
        'self', verbose_name='Link 2', related_name='+', null=True, blank=True)
    link_three = models.ForeignKey(
        'self', verbose_name='Link 3', related_name='+', null=True, blank=True)
    media = models.FileField('Medien-Anhang', null=True, blank=True)
    pub_date = models.DateTimeField('Veröffentlicht am', default=timezone.now)

    def __str__(self):
        return '%s (%s)' % (self.title, self.pub_date.strftime('%d.%m.%Y'))
