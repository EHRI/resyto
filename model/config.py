#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, os, platform
from configparser import ConfigParser

logger = logging.getLogger(__name__)

# Location for configuration files on Windows: ﻿
# os.path.expanduser("~")\AppData\Local\Programs\rsync\rsync.cfg
#
# Location for configuration files on unix-based systems:
# os.path.expanduser("~")/.config/rsync/rsync.cfg
#
# platform.system() returns
# Mac:      'Darwin'
# Windows:  ﻿'Windows'
# CentOS:   'Linux'


CFG_FILENAME = "rsync.cfg"


class Configuration(object):

    _configuration_filename = CFG_FILENAME

    @staticmethod
    def _set_configuration_filename(cfg_filename):
        logger.info("Setting configuration filename to %s", cfg_filename)
        Configuration._configuration_filename = cfg_filename

    @staticmethod
    def _get_configuration_filename():
        if not Configuration._configuration_filename:
            Configuration._set_configuration_filename(CFG_FILENAME)

        return Configuration._configuration_filename

    @staticmethod
    def _get_config_path():

        c_path = os.path.expanduser("~")
        opsys = platform.system()
        if opsys == "Windows":
            win_path = os.path.join(c_path, "AppData", "Local")
            if os.path.exists(win_path): c_path = win_path
        elif opsys == "Darwin":
            dar_path = os.path.join(c_path, ".config")
            if not os.path.exists(dar_path): os.makedirs(dar_path)
            if os.path.exists(dar_path): c_path = dar_path
        elif opsys == "Linux":
            lin_path = os.path.join(c_path, ".config")
            if not os.path.exists(lin_path): os.makedirs(lin_path)
            if os.path.exists(lin_path): c_path = lin_path

        c_path = os.path.join(c_path, "rsync")
        if not os.path.exists(c_path): os.makedirs(c_path)
        logger.info("Configuration directory: %s", c_path)
        return c_path

    @staticmethod
    def _create_config_file(parser, location):
        f = open(location, "w")
        parser.read_dict({"config": {"resource_dir": os.path.expanduser("~"),
                                     "resync_dir": os.path.expanduser("~"),
                                     "sourcedesk": "http://www.example.com/rs/sourcedescription.xml",
                                     "urlprefix": "http://www.example.com/"
                                     },
                          "settings": {"language": "en-US"}
                          })
        parser.write(f)
        f.close()
        logger.info("Initial configuration file created at %s", location)

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            logger.info("Creating Configuration._instance")
            cls._instance = super(Configuration, cls).__new__(cls, *args, **kwargs)
            cls.config_path = cls._get_config_path()
            cls.config_file = os.path.join(cls.config_path, Configuration._get_configuration_filename())
            cls.parser = ConfigParser()
            if not os.path.exists(cls.config_file):
                cls._create_config_file(cls.parser, cls.config_file)
            else:
                logger.info("Reading configuration file: %s", cls.config_file)
                cls.parser.read(cls.config_file)

        return cls._instance

    def config_path(self):
        return self.config_path

    def config_file(self):
        return self.config_file

    def persist(self):
        f = open(self.config_file, "w")
        self.parser.write(f)
        f.close()
        logger.info("Persisted %s", self.config_file)

    def cfg_resource_dir(self):
        return self.parser.get("config", "resource_dir", fallback=os.path.expanduser("~"))

    def set_cfg_resource_dir(self, resource_dir):
        self.parser["config"]["resource_dir"] = resource_dir

    def cfg_resync_dir(self):
        return self.parser.get("config", "resync_dir", fallback=os.path.expanduser("~"))

    def set_cfg_resync_dir(self, resync_dir):
        self.parser["config"]["resync_dir"] = resync_dir

    def cfg_sourcedesc(self):
        return self.parser.get("config", "sourcedesc", fallback="http://www.example.com/rs/sourcedescription.xml")

    def set_cfg_sourcedesc(self, sourcedesc):
        self.parser["config"]["sourcedesc"] = sourcedesc

    def cfg_urlprefix(self):
        return self.parser.get("config", "urlprefix", fallback="http://www.example.com/")

    def set_cfg_urlprefix(self, urlprefix):
        self.parser["config"]["urlprefix"] = urlprefix

    def cfg_strategy(self):
        return int(self.parser.get("config", "strategy", fallback="0"))

    def set_cfg_strategy(self, id):
        self.parser.set("config", "strategy", str(id))

    def settings_language(self):
        return self.parser.get("settings", "language", fallback="en-US")

    def set_settings_language(self, language):
        self.parser["settings"]["language"] = language

    # window dimensions
    def window_width(self):
        return int(self.parser.get("window","width", fallback="700"))

    def set_window_width(self, width):
        if not self.parser.has_section("window"):
            self.parser.add_section("window")
        self.parser.set("window", "width", str(width))

    def window_height(self):
        return int(self.parser.get("window","height", fallback="400"))

    def set_window_height(self, height):
        if not self.parser.has_section("window"):
            self.parser.add_section("window")
        self.parser.set("window", "height", str(height))

    # explorer dimensions
    def explorer_width(self):
        return int(self.parser.get("explorer","width", fallback="630"))

    def set_explorer_width(self, width):
        if not self.parser.has_section("explorer"):
            self.parser.add_section("explorer")
        self.parser.set("explorer", "width", str(width))

    def explorer_height(self):
        return int(self.parser.get("explorer","height", fallback="400"))

    def set_explorer_height(self, height):
        if not self.parser.has_section("explorer"):
            self.parser.add_section("explorer")
        self.parser.set("explorer", "height", str(height))