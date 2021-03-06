#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest, os, platform, sys
from model.config import Configuration


class TestConfiguration(unittest.TestCase):

    def test01_set_test_config(self):
        print("\n>>> Testing set_test_config")
        Configuration._set_configuration_filename(None)
        assert not Configuration._configuration_filename
        assert Configuration._get_configuration_filename() == "rsync.cfg"

        Configuration._set_configuration_filename("foo.bar")
        assert Configuration._get_configuration_filename() == "foo.bar"
        Configuration._set_configuration_filename(None)
        assert Configuration._get_configuration_filename() == "rsync.cfg"

    def test02_instance(self):
        print("\n>>> Testing _instance")
        Configuration._set_configuration_filename("rsync_test.cfg")

        config1 = Configuration()
        config2 = Configuration()

        assert config1 == config2

        path1 = config1.config_path
        if platform.system() == "Darwin":
            assert path1 == os.path.expanduser("~") + "/.config/rsync"
        elif platform.system() == "Windows":
            path_expected = os.path.join(os.path.expanduser("~"), "AppData", "Local", "rsync")
            assert path1 == path_expected
        elif platform.system() == "Linux":
            assert path1 == os.path.expanduser("~") + "/.config/rsync"
        else:
            assert path1 == os.path.expanduser("~") + "/rsync"

        assert config1.cfg_resource_dir() == os.path.expanduser("~")
        config1.set_cfg_resource_dir("foo/bar/baz")
        assert config2.cfg_resource_dir() == "foo/bar/baz"

        config2.persist()
        config1 = None
        config2 = None
        Configuration._set_configuration_filename(None)

    # No control over garbage collect, so read cannot be tested.
    def test03_read(self):
        print("\n>>> Testing read")
        Configuration._set_configuration_filename("rsync_test.cfg")
        config1 = Configuration()
        config2 = Configuration()

        assert config1.cfg_resource_dir() == "foo/bar/baz"
        assert config2.cfg_resource_dir() == "foo/bar/baz"

    def test04_set_get_language(self):
        print("\n>>> Testing language")
        Configuration._set_configuration_filename("rsync_test.cfg")
        config1 = Configuration()

        print("current language: " + config1.settings_language())
        config1.set_settings_language("foo-BR")
        print("now the language is: " + config1.settings_language())


    def test99_cleanup(self):
        print("\n>>> Cleaning up")
        Configuration._set_configuration_filename("rsync_test.cfg")
        config1 = Configuration()

        os.remove(config1.config_file)
        assert not os.path.exists(config1.config_file)
        config1._instance = None
        Configuration._set_configuration_filename(None)







