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
# host_dict = inventory.get_groups_dict() #读取主机组和主机
# print(host_dict)
# host_list = inventory.get_hosts()
# print(host_list)
# hosts = inventory.get_hosts(pattern="test")
# print(hosts)
# host = inventory.get_host(hostname='172.16.7.151')
# print(host)
# inventory.add_host(host='172.16.7.153', port='22', group='test')
# print(inventory.get_groups_dict())
# print("===========")

# VariableManager类
variableManager = VariableManager(loader=loader, inventory=inventory)
# print(variableManager.get_vars(host=host)) #获取某个主机的变量
# variableManager.set_host_variable(host=host, varname="ansible_ssh_pass", value='654321')  #设置或修改变量
# print(variableManager.get_vars(host=host))
# variableManager.extra_vars = {"myweb":"node1", "myname":"tom"} #设置额外的变量，这个设置的变量是全局的
# print(variableManager.get_vars(host=host))
# print(variableManager.get_vars()) #不传入具体主机，也可以获得上面设置的extra_vars

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

# Play() 执行对象和模块
play_source = dict(name="Ansible Play ad-hoc demo",
                   hosts='172.16.206.30',
                   gather_facts='no',
                   tasks=[
                       dict(action=dict(module='shell', args='touch /tmp/e.txt')),
                   ]
                   )
play = Play().load(play_source, variable_manager=variableManager, loader=loader)

# actually run it
passwords = dict()
try:
    tqm = TaskQueueManager(
        inventory=inventory,
        variable_manager=variableManager,
        loader=loader,
        options=options,
        passwords=passwords,
    )
    result = tqm.run(play)
    print(type(result))
    print(result)
finally:
    if tqm is not None:
        tqm.cleanup()

