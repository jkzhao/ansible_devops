from django.db import models

# Create your models here.
# 用户登录信息表(服务器、虚拟机)
class ConnectionInfo(models.Model):
    # 用户连接相关信息
    ssh_username = models.CharField(max_length=10, default='', verbose_name='ssh用户名', null=True)
    ssh_userpasswd = models.CharField(max_length=40, default='', verbose_name='ssh用户密码', null=True)
    ssh_hostip = models.CharField(max_length=40, default='', verbose_name='ssh登录的ip', null=True)
    ssh_host_port = models.CharField(max_length=10, default='', verbose_name='ssh登录的端口', null=True)
    ssh_rsa = models.CharField(max_length=64, default='', verbose_name='ssh私钥')
    rsa_pass = models.CharField(max_length=64, default='', verbose_name='私钥的密钥')
    # 0-登录失败,1-登录成功
    ssh_status = models.IntegerField(default=0, verbose_name='用户连接状态,0-登录失败,1-登录成功')
    # 1-rsa登录,2-dsa登录,3-普通用户_rsa登录,4-docker成功,5-docker无法登录
    ssh_type = models.IntegerField(default=0, verbose_name='用户连接类型, 1-rsa登录,2-dsa登录,'
                                                           '3-ssh_rsa登录,4-docker成功,5-docker无法登录')
    # 唯一对象标识
    sn_key = models.CharField(max_length=256, verbose_name="唯一设备ID", default="")

    class Meta:
        verbose_name = '用户登录信息表'
        verbose_name_plural = verbose_name
        db_table = "connectioninfo"
