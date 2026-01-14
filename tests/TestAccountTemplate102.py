import unittest
from config import config
from ok.test.TaskTestCase import TaskTestCase
from src.task.DailyTask import DailyTask

config['debug'] = True


class TestAccountTemplate102(TaskTestCase):
    task_class = DailyTask
    config = config

    def test_match_account_button_on_title(self):
        self.set_image('tests/images/分辨率1.png')
        box = self.task.find_one('account_switch_button', threshold=0.7)
        self.assertIsNotNone(box)


if __name__ == '__main__':
    unittest.main()
