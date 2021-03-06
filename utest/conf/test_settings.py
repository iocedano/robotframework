import unittest
import os
from os.path import abspath

from robot.conf.settings import _BaseSettings, RobotSettings, RebotSettings
from robot.errors import DataError
from robot.utils.asserts import assert_equals, assert_false


class SettingWrapper(_BaseSettings):

    def __init__(self):
        pass


class TestSplitArgsFromNameOrPath(unittest.TestCase):

    def setUp(self):
        self.method = SettingWrapper()._split_args_from_name_or_path

    def test_with_no_args(self):
        assert not os.path.exists('name'), 'does not work if you have name folder!'
        assert_equals(self.method('name'), ('name', []))

    def test_with_args(self):
        assert not os.path.exists('name'), 'does not work if you have name folder!'
        assert_equals(self.method('name:arg'), ('name', ['arg']))
        assert_equals(self.method('listener:v1:v2:v3'), ('listener', ['v1', 'v2', 'v3']))
        assert_equals(self.method('aa:bb:cc'), ('aa', ['bb', 'cc']))

    def test_empty_args(self):
        assert not os.path.exists('foo'), 'does not work if you have foo folder!'
        assert_equals(self.method('foo:'), ('foo', ['']))
        assert_equals(self.method('bar:arg1::arg3'), ('bar', ['arg1', '', 'arg3']))
        assert_equals(self.method('L:'), ('L', ['']))

    def test_with_windows_path_without_args(self):
        assert_equals(self.method('C:\\name.py'), ('C:\\name.py', []))
        assert_equals(self.method('X:\\APPS\\listener'), ('X:\\APPS\\listener', []))
        assert_equals(self.method('C:/varz.py'), ('C:/varz.py', []))

    def test_with_windows_path_with_args(self):
        assert_equals(self.method('C:\\name.py:arg1'), ('C:\\name.py', ['arg1']))
        assert_equals(self.method('D:\\APPS\\listener:v1:b2:z3'),
                      ('D:\\APPS\\listener', ['v1', 'b2', 'z3']))
        assert_equals(self.method('C:/varz.py:arg'), ('C:/varz.py', ['arg']))

    def test_existing_paths_are_made_absolute(self):
        path = 'robot-framework-unit-test-file-12q3405909qasf'
        open(path, 'w').close()
        try:
            assert_equals(self.method(path), (abspath(path), []))
            assert_equals(self.method(path+':arg'), (abspath(path), ['arg']))
        finally:
            os.remove(path)

    def test_existing_path_with_colons(self):
        # Colons aren't allowed in Windows paths (other than in "c:")
        if os.sep == '\\':
            return
        path = 'robot:framework:test:1:2:42'
        os.mkdir(path)
        try:
            assert_equals(self.method(path), (abspath(path), []))
        finally:
            os.rmdir(path)


class TestRobotAndRebotSettings(unittest.TestCase):

    def test_robot_and_rebot_settings_are_independent(self):
        # http://code.google.com/p/robotframework/issues/detail?id=881
        orig_opts = RobotSettings()._opts
        RebotSettings()
        assert_equals(RobotSettings()._opts, orig_opts)

    def test_extra_options(self):
        assert_equals(RobotSettings(name='My Name')['Name'], 'My Name')
        assert_equals(RobotSettings({'name': 'Override'}, name='Set')['Name'],'Set')

    def test_multi_options_as_single_string(self):
        assert_equals(RobotSettings({'test': 'one'})['TestNames'], ['one'])
        assert_equals(RebotSettings({'exclude': 'two'})['Exclude'], ['two'])

    def test_output_files_as_none_string(self):
        for name in 'Output', 'Report', 'Log', 'XUnit', 'DebugFile':
            attr = (name[:-4] if name.endswith('File') else name).lower()
            settings = RobotSettings({name.lower(): 'NoNe'})
            assert_equals(settings[name], None)
            if hasattr(settings, attr):
                assert_equals(getattr(settings, attr), None)

    def test_output_files_as_none_object(self):
        for name in 'Output', 'Report', 'Log', 'XUnit', 'DebugFile':
            attr = (name[:-4] if name.endswith('File') else name).lower()
            settings = RobotSettings({name.lower(): None})
            assert_equals(settings[name], None)
            if hasattr(settings, attr):
                assert_equals(getattr(settings, attr), None)

    def test_log_levels(self):
        self._verify_log_level('TRACE')
        self._verify_log_level('DEBUG')
        self._verify_log_level('INFO')
        self._verify_log_level('WARN')
        self._verify_log_level('NONE')

    def test_default_log_level(self):
        self._verify_log_levels(RobotSettings(), 'INFO')
        self._verify_log_levels(RebotSettings(), 'TRACE')

    def _verify_log_level(self, input, level=None, default=None):
        level = level or input
        default = default or level
        self._verify_log_levels(RobotSettings({'loglevel': input}), level, default)
        self._verify_log_levels(RebotSettings({'loglevel': input}), level, default)

    def _verify_log_levels(self, settings, level, default=None):
        assert_equals(settings['LogLevel'], level)
        assert_equals(settings['VisibleLogLevel'], default or level)

    def test_log_levels_with_default(self):
        self._verify_log_level('TRACE:INFO', level='TRACE', default='INFO')
        self._verify_log_level('TRACE:debug', level='TRACE', default='DEBUG')
        self._verify_log_level('DEBUG:INFO', level='DEBUG', default='INFO')

    def test_invalid_log_level(self):
        self._verify_invalid_log_level('kekonen')
        self._verify_invalid_log_level('DEBUG:INFO:FOO')
        self._verify_invalid_log_level('INFO:bar')
        self._verify_invalid_log_level('bar:INFO')

    def test_visible_level_higher_than_normal_level(self):
        self._verify_invalid_log_level('INFO:TRACE')
        self._verify_invalid_log_level('DEBUG:TRACE')

    def _verify_invalid_log_level(self, input):
        self.assertRaises(DataError, RobotSettings, {'loglevel': input})


if __name__ == '__main__':
    unittest.main()
