# -*- coding: utf-8 -*-

# Create your views here.
#import os
#PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))
# import sys
# os.environ["DJANGO_SETTINGS_MODULE"] = 'admin.settings.settings'
# import django
# django.setup()

import datetime
import json
from django.http import HttpResponseRedirect,JsonResponse
from django.http import HttpResponseRedirect,JsonResponse
from django.shortcuts import render
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse

from taskdo.utils.ansible_api import ANSRunner
from taskdo.utils.aes import prpcrypt
from taskdo.utils.MgCon import *
from taskdo.utils.RedisCon import *

from taskdo.models import ConnectionInfo
# from apps.test import test2
# from taskdo.utils.base.tools import CJsonEncoder


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.__str__()
        return json.JSONEncoder.default(self, obj)

def adhoc_task(request):
    if request.method == "POST":
        result = {}
        jobs = request.body
        #print(type(request.body))
        init_jobs = json.loads(jobs.decode("utf-8"))

        #接口数据校验
        mod_type = init_jobs.get("mod_type") if not init_jobs.get("mod_type") else "shell" # mod_type:ad_hoc模块类型
        sn_keys = init_jobs.get("sn_key") #sn_key: 设备唯一标识，标识宿主机、虚拟机唯一标识
        exec_args = init_jobs.get("exec_args") #exec_args: 执行参数，执行模块类型所需要传入的指令或者选项
        group_name = init_jobs.get("group_name", "test")
        taskid = init_jobs.get("taskid") #任务id

        if not sn_keys or not exec_args or not taskid:
            result = {"status":"failed", "code":"002", "info":"传入的参数mod_type不匹配！"}
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            rlog = InsertAdhocLog(taskid=taskid)

        if mod_type not in ("shell", "yum", "copy"): #这里只写了3个常用的模块，这里可以多写一些，做限制，限制只能使用哪些模块
            result = {"status":"failed", "code":"003", "info":"传入的参数不完整！"}
            rlog.record(id=10008) #记录日志
        else:
            try:
                sn_keys = set(sn_keys)
                # ssh登录基础数据提取
                hosts_obj = ConnectionInfo.objects.filter(sn_key__in=sn_keys)
                rlog.record(id=10000)

                if len(sn_keys) != len(hosts_obj):
                    rlog.record(id=40004)
                else:
                    rlog.record(id=10002)
                    resource = {}
                    hosts_list = []
                    vars_dic = {}
                    cn = prpcrypt("okeqwnk2987#$%ql")
                    hosts_ip = []
                    for host in hosts_obj:
                        sshpasswd = cn.decrypt(host.ssh_userpasswd)
                        if host.ssh_type in (1, 2):
                            """
                            resource =  {
                                "dynamic_host": {
                                    "hosts": [
                                                {"hostname": "192.168.1.108", "port": "22", "username": "root", "ssh_key": "/etc/ansible/ssh_keys/id_rsa"},
                                                {"hostname": "192.168.1.109", "port": "22", "username": "root","ssh_key": "/etc/ansible/ssh_keys/id_rsa"}
                                              ],
                                    "vars": {
                                             "var1":"ansible",
                                             "var2":"saltstack"
                                             }
                                }
                            }
                            """
                            hosts_list.append({"hostname":host.sn_key, "ip":host.ssh_hostip, "port":host.ssh_host_port,
                                 "username":host.ssh_username, "ssh_key":host.ssh_rsa})
                            hosts_ip.append(host.sn_key)
                        elif host.ssh_type in (0, 4):
                            hosts_list.append({"hostname":host.sn_key, "ip":host.ssh_hostip, "port":host.ssh_host_port,
                                               "username":host.ssh_username, "password":sshpasswd})
                            hosts_ip.append(host.sn_key)
                        elif host.ssh_type == 3:
                            hosts_list.append({"hostname":host.sn_key, "ip":host.ssh_hostip, "port":host.ssh_host_port,
                                               "username":host.ssh_username,"ssh_key":host.ssh_rsa,"password":sshpasswd})
                            hosts_ip.append(host.sn_key)

                    resource[group_name] = {"hosts":hosts_list, "vars":vars_dic}
                    rlog.record(id=10004)
                    #任务锁检查
                    lockstatus = DsRedis.get(rkey="tasklock")
                    if lockstatus is False or lockstatus == '1':
                        # 已经有任务在执行
                        rlog.record(id=40005)
                    else:
                        # 开始执行任务
                        DsRedis.setlock("tasklock", 1) #加锁
                        jdo = ANSRunner(resource=resource, redisKey='1')
                        jdo.run_model(host_list=hosts_ip, module_name=mod_type, module_args=exec_args)
                        # 返回执行结果
                        res = jdo.get_model_result()
                        rlog.record(id=19999, input_con=res)
                        rlog.record(id=20000)
                        DsRedis.setlock("tasklock", 0) #解锁
                        result = {"status":"success", "info":res}

            except Exception as e:
                import traceback
                print(traceback.print_exc())
                DsRedis.setlock("tasklock",0)
                result = {"status":"failed", "code":"005", "info":e}
            finally:
                return HttpResponse(json.dumps(result), content_type="application/json")

def adhoc_task_log(request):
    """获取日志"""
    if request.method == "GET":
        taskid = request.GET.get("taskid")
        result = {}
        if taskid:
            rlog = InsertAdhocLog(taskid=taskid) #根据taskid获取与该taskid相关的事件日志
            res = rlog.getrecord()
            result = {"status":"success",'taskid':taskid,"info":res}
        else:
            result = {"status":"failed", "info":"没有传入taskid值"}
        res = json.dumps(result, cls=DateEncoder)
        return HttpResponse(res, content_type="application/json")

