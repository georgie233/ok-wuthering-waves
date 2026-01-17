import re

from qfluentwidgets import FluentIcon

from ok import Logger, TaskDisabledException
from src.task.BaseWWTask import number_re, stamina_re
from src.task.FarmEchoTask import FarmEchoTask
from src.task.ForgeryTask import ForgeryTask
from src.task.NightmareNestTask import NightmareNestTask
from src.task.TacetTask import TacetTask
from src.task.SimulationTask import SimulationTask
from src.task.WWOneTimeTask import WWOneTimeTask
from src.task.BaseCombatTask import BaseCombatTask

logger = Logger.get_logger(__name__)


class DailyTask(WWOneTimeTask, BaseCombatTask):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "Daily Task"
        self.group_name = "Daily"
        self.group_icon = FluentIcon.CALENDAR
        self.icon = FluentIcon.CAR
        self.support_tasks = ["Tacet Suppression", "Forgery Challenge", "Simulation Challenge"]
        self.default_config = {
            'Which to Farm': self.support_tasks[0],
            'Which Tacet Suppression to Farm': 1,  # starts with 1
            'Which Forgery Challenge to Farm': 1,  # starts with 1
            'Material Selection': 'Shell Credit',
            'Auto Farm all Nightmare Nest': False,
            'Farm Nightmare Nest for Daily Echo': True,
            'Enable Multi Accounts': False,
            'Account Count': '1',
        }
        self.config_description = {
            'Which Tacet Suppression to Farm': 'The Tacet Suppression number in the F2 list.',
            'Which Forgery Challenge to Farm': 'The Forgery Challenge number in the F2 list.',
            'Material Selection': 'Resonator EXP / Weapon EXP / Shell Credit',
            'Farm Nightmare Nest for Daily Echo': 'Farm 1 Echo from Nightmare Nest to complete Daily Task when needed.',
            'Enable Multi Accounts': 'Enable Multi Accounts for Daily Task (Sequential run)',
            'Account Count': 'Account Count (1–4, sequential order)',
        }
        material_option_list = ['Resonator EXP', 'Weapon EXP', 'Shell Credit']
        self.config_type = {
            'Which to Farm': {
                'type': "drop_down",
                'options': self.support_tasks
            },
            'Material Selection': {
                'type': 'drop_down',
                'options': material_option_list
            },
            'Account Count': {
                'type': 'drop_down',
                'options': ['1', '2', '3', '4']
            },
        }
        self.description = "Login, claim monthly card, farm echo, and claim daily reward"

    def run(self):
        WWOneTimeTask.run(self)
        enable_multi = self.config.get('Enable Multi Accounts')
        count = self.config.get('Account Count')
        try:
            count_int = int(str(count)) if count is not None else 1
        except Exception:
            count_int = 1
        self.log_info(f'Multi Accounts: enable={enable_multi} count={count_int}')
        if enable_multi and count_int > 1:
            for i in range(1, count_int + 1):
                self.log_info(f'Multi Accounts: begin account {i}')
                self.ensure_main(time_out=180)
                texts = self.ocr()
                start = self.find_boxes(texts, boundary='bottom_right', match=["开始游戏", re.compile("进入游戏")])
                if start:
                    self.click(start, after_sleep=1)
                    self.wait_until(lambda: self.in_team_and_world(),
                                    post_action=lambda: self.click_relative(0.5, 0.9, after_sleep=2), time_out=10)
                self._run_daily_one_account()
                if i < count_int:
                    if not self.exit_login():
                        self.log_info('Exit Login Failed')
                        break
                    self.sleep(20)
                    from src.win.DialogLoginHelper import click_account_and_login
                    self.log_info(f'Multi Accounts: switch to account {i+1}')
                    click_account_and_login(i + 1)
                    self.sleep(3)
                    self.click_relative(0.5, 0.95, after_sleep=0.5)
                    self.log_info('Multi Accounts: clicked bottom area to raise login form')
                    self.wait_until(lambda: self.in_team_and_world(),
                                    post_action=lambda: self.click_relative(0.5, 0.9, after_sleep=2), time_out=20)
                else:
                    self.log_info('Multi Accounts: last account reached, finish without exit')
            self.log_info('Task completed', notify=True)
            return
        self.ensure_main(time_out=180)
        texts = self.ocr()
        start = self.find_boxes(texts, boundary='bottom_right', match=["开始游戏", re.compile("进入游戏")])
        if start:
            self.click(start, after_sleep=1)
            self.wait_until(lambda: self.in_team_and_world(),
                            post_action=lambda: self.click_relative(0.5, 0.9, after_sleep=2), time_out=10)
            self._run_daily_one_account()
        if not self.exit_login():
            self.log_info('Exit Login Failed')
        self.log_info('Task completed', notify=True)
    def _run_daily_one_account(self):
        condition1 = self.config.get('Auto Farm all Nightmare Nest')
        condition2 = self.config.get('Farm Nightmare Nest for Daily Echo')
        if condition1 or condition2:
            try:
                if condition1:
                    self.log_debug('Auto Farm all Nightmare Nest')
                    self.run_task_by_class(NightmareNestTask)
                elif condition2 and self.config.get('Which to Farm', self.support_tasks[0]) != self.support_tasks[0]:
                    self.log_debug('Farm Nightmare Nest for Daily Echo')
                    self.get_task_by_class(NightmareNestTask).run_capture_mode()
            except TaskDisabledException:
                raise
            except Exception as e:
                self.log_error("NightmareNestTask Failed", e)
                self.ensure_main(time_out=180)
        used_stamina, completed = self.open_daily()
        self.send_key('esc', after_sleep=1)
        if not completed:
            if used_stamina < 180:
                target = self.config.get('Which to Farm', self.support_tasks[0])
                if target == self.support_tasks[0]:
                    self.get_task_by_class(TacetTask).farm_tacet(daily=True, used_stamina=used_stamina,
                                                                 config=self.config)
                elif target == self.support_tasks[1]:
                    self.get_task_by_class(ForgeryTask).farm_forgery(daily=True, used_stamina=used_stamina,
                                                                     config=self.config)
                else:
                    self.get_task_by_class(SimulationTask).farm_simulation(daily=True, used_stamina=used_stamina,
                                                                           config=self.config)
                self.sleep(4)
            self.claim_daily()
        self.claim_mail()
        self.sleep(1)
        self.claim_battle_pass()

    def claim_battle_pass(self):
        self.log_info('battle pass')
        self.send_key_down('alt')
        self.sleep(0.05)
        self.click_relative(0.86, 0.05)
        self.send_key_up('alt')
        if not self.wait_ocr(0.2, 0.13, 0.32, 0.22, match=re.compile(r'\d+'), settle_time=1, raise_if_not_found=False):
            self.log_error('can not battle pass, maybe ended')
        else:
            self.click(0.04, 0.3, after_sleep=1)
            self.click(0.68, 0.91, after_sleep=3)
            self.click(0.04, 0.17, after_sleep=2)
            self.click(0.68, 0.91, after_sleep=2)
            self.wait_ocr(0.2, 0.13, 0.32, 0.22, match=re.compile(r'\d+'),
                          post_action=lambda: self.click(0.68, 0.91, after_sleep=1), settle_time=1,
                          raise_if_not_found=False)
        self.ensure_main()

    def open_daily(self):
        self.log_info('open_daily')
        gray_book_quest = self.openF2Book("gray_book_quest")
        self.click_box(gray_book_quest, after_sleep=1.5)
        progress = self.ocr(0.1, 0.1, 0.5, 0.75, match=re.compile(r'^(\d+)/180$'))
        if not progress:
            self.click(0.961, 0.6, after_sleep=1)
            progress = self.ocr(0.1, 0.1, 0.5, 0.75, match=re.compile(r'^(\d+)/180$'))
        if progress:
            current = int(progress[0].name.split('/')[0])
        else:
            current = 0
        self.info_set('current daily progress', current)
        return current, self.get_total_daily_points() >= 100

    def get_total_daily_points(self):
        points_boxes = self.ocr(0.19, 0.8, 0.30, 0.93, match=number_re)
        if points_boxes:
            points = int(points_boxes[0].name)
        else:
            points = 0
        self.info_set('total daily points', points)
        return points

    def claim_daily(self):
        self.info_set('current task', 'claim daily')
        self.ensure_main(time_out=5)
        self.open_daily()

        self.click(0.87, 0.17, after_sleep=0.5)
        self.sleep(1)

        total_points = self.get_total_daily_points()
        self.info_set('daily points', total_points)
        if total_points < 100:
            self.log_info("Can't complete daily task, may need to increase stamina manually!")
            return

        self.click(0.89, 0.85, after_sleep=1)
        self.ensure_main(time_out=10)

    def claim_mail(self):
        self.info_set('current task', 'claim mail')
        self.back(after_sleep=1.5)
        self.click(0.64, 0.95, after_sleep=1)
        self.click(0.14, 0.9, after_sleep=1)
        self.ensure_main(time_out=5)
