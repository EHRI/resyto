# -*- coding: utf-8 -*-

import gettext
import locale
import os


def get_languages():
    found_languages = []
    for dirname in os.listdir(path=LOCALE_DIR):
        if os.path.isdir(os.path.join(LOCALE_DIR, dirname)):
            found_languages.append(dirname)
    return found_languages


def set_language(lang):
    languages.clear()
    languages.append(lang)
    # print(languages)
    # print(gettext.find(APP_NAME, LOCALE_DIR, languages=[lang]))
    gettext.translation(APP_NAME, LOCALE_DIR, languages=[lang], fallback=True).install()
    # print("in set_language: "+_("browse"))


def get_languages():
    found_languages = []
    for dirname in os.listdir(path=LOCALE_DIR):
        if os.path.isdir(os.path.join(LOCALE_DIR, dirname)):
            found_languages.append(dirname)
    return found_languages


# Change this variable to your app name!
#  The translation files will be under
#  @LOCALE_DIR@/@LANGUAGE@/LC_MESSAGES/@APP_NAME@.mo
APP_NAME = "resyto"
# TODO: weird way to find the current module ...
APP_DIR = os.path.join(os.curdir, "..")
# print(os.path.abspath(APP_DIR))

LOCALE_DIR = os.path.join(APP_DIR, 'i18n') # .mo files will then be located in APP_Dir/i18n/LANGUAGECODE/LC_MESSAGES/

# Now we need to choose the language. We will provide a list, and gettext
# will use the first translation available in the list
# on desktop is usually LANGUAGES
DEFAULT_LANGUAGES = get_languages()

lc, encoding = locale.getdefaultlocale()
# if lc:
#    languages = [lc]

# Concat all languages (env + default locale),
#  and here we have the languages and location of the translations
languages = DEFAULT_LANGUAGES
mo_location = LOCALE_DIR
# print("translations will be searched in: " + os.path.abspath(mo_location))

# Lets tell those details to gettext
gettext.translation(APP_NAME, LOCALE_DIR, languages, fallback=True)

gettext.install(True, localedir=mo_location)

gettext.textdomain(APP_NAME)

gettext.bind_textdomain_codeset(APP_NAME, "UTF-8")
