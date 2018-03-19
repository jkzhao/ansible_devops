# -*- coding: utf-8 -*-

#核心类
from collections import namedtuple

from ansible.parsing.dataloader import DataLoader  #用于读取yaml、json格式的文件，所在模块ansible.parsing.dataloader
from ansible.vars.manager import VariableManager  #用于存储各类变量信息
from ansible.inventory.manager import InventoryManager #用于导入inventory文件
from ansible.inventory.host import Host #操作单个主机或者主机组信息
from ansible.inventory.group import Group
from ansible.playbook.play import Play  #用于存储执行hosts的角色信息，所在模块ansible.playbook.play
from ansible.executor.task_queue_manager import TaskQueueManager #ansible底层用到的任务队列
from ansible.plugins.callback import CallbackBase #状态回调，各种成功失败的状态
from ansible.executor.playbook_executor import PlaybookExecutor #核心类执行playbook副本

# InventoryManager类
loader = DataLoader()
inventory = InventoryManager(loader=loader, sources=['hosts']) #资产配置文件可以填写相对路径和绝对路径，如果有多个，列表中用逗号隔开

# VariableManager类
variableManager = VariableManager(loader=loader, inventory=inventory)

# Options 执行选项
Options = namedtuple('Options',
                    ['connection',
                      'remote_user',
                      'ask_sudo_pass',
                      'verbosity',
                      'ask_pass',
                      'module_path',
                      'forks', #控制并发多少个
                      'become',
                      'become_method',
                      'become_user',
                      'check',
                      'listhosts',
                      'listtasks',
                      'listtags',
                      'syntax',
                      'sudo_user',
                      'sudo',
                     'diff'])
options = Options(connection='smart', #local：该连接类型将在控制机本身上执行剧本。
                  remote_user=None,
                  ask_pass=None,
                  sudo_user=None,
                  forks=5,
                  sudo=None,
                  ask_sudo_pass=False,
                  verbosity=5,
                  module_path=None,
                  become=None,
                  become_method=None,
                  become_user=None,
                  check=False,
                  diff=False,
                  listhosts=None,
                  listtasks=None,
                  listtags=None,
                  syntax=None)

class PlayBookResultsCollector(CallbackBase):
    CALLBACK_VERSION = 2.0
    def __init__(self, *args, **kwargs):
        super(PlayBookResultsCollector, self).__init__(*args, **kwargs)
        self.task_ok = {}
        self.task_skipped = {}
        self.task_failed = {}
        self.task_status = {}
        self.task_unreachable = {}

    def v2_runner_on_ok(self, result, *args, **kwargs):
        self.task_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.task_failed[result._host.get_name()] = result

    def v2_runner_on_unreachable(self, result, *args, **kwargs):
        self.task_unreachable[result._host.get_name()] = result

    def v2_runner_on_skipped(self, result, *args, **kwargs):
        self.task_skipped[result._host.get_name()] = result

    def v2_playbook_on_stats(self, stats):
        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)
            self.task_status[h] = {
                "ok":t['ok'],
                "changed":t['changed'],
                "unreachable":t['unreachable'],
                "skipped":t['skipped'],
                "failed":t['failures']
            }

callback = PlayBookResultsCollector()

# PlaybookExecutor 执行playbook
passwords = dict()
playbook = PlaybookExecutor(playbooks=['test.yml'],
                            inventory=inventory,
                            variable_manager=variableManager,
                            loader=loader,
                            options=options,
                            passwords=passwords)
playbook._tqm._stdout_callback = callback
playbook.run()

results_raw = {'skipped':{}, 'failed':{}, 'ok':{}, 'status':{}, 'unreachable':{}, 'changed':{}}
for host,result in callback.task_ok.items():
    #results_raw['ok'][host] = result
    results_raw['ok'][host] = result._result
for host,result in callback.task_failed.items():
    results_raw['failed'][host] = result._result
for host,result in callback.task_unreachable.items():
    results_raw['unreachable'][host] = result._result
for host,result in callback.task_skipped.items():
    results_raw['skipped'][host] = result._result
results_raw['status'] = callback.task_status
print(results_raw)
