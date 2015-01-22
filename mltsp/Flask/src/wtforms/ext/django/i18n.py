from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
from django.utils.translation import ugettext, ungettext
from wtforms import form

class DjangoTranslations(object):
    """
    A translations object for WTForms that gets its messages from django's
    translations providers.
    """
    def gettext(self, string):
        return ugettext(string)

    def ngettext(self, singular, plural, n):
        return ungettext(singular, plural, n)


class Form(form.Form):
    """
    A Form derivative which uses the translations engine from django.
    """
    _django_translations = DjangoTranslations()

    def _get_translations(self):
        return self._django_translations
