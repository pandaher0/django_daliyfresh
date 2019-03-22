# Author:hxj
# 自定义存储类
from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FdfsStorage(Storage):
    def __init__(self, client_conf=None, base_url=None):
        if client_conf is None:
            client_conf = settings.CLIENT_CONF
        if base_url is None:
            base_url = settings.NGINX_URL

        self.client_conf = client_conf
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        """打开文件时使用"""
        pass

    def _save(self, name, content):
        """保存文件时使用"""
        # name：上传文件的名字
        # content:包含上传文件内容的file类对象

        # 创建fdfs_client文件
        client = Fdfs_client(self.client_conf)
        # 上传文件
        # dict {
        #             'Group name'      : group_name,
        #             'Remote file_id'  : remote_file_id,
        #             'Status'          : 'Upload successed.',
        #             'Local file name' : '',
        #             'Uploaded size'   : upload_size,
        #             'Storage IP'      : storage_ip
        #         }
        res = client.upload_by_buffer(content.read())
        if res.get('Status') != 'Upload successed.':
            # 上传失败
            raise Exception('上传文件到fdfs失败')

        # 获取filename
        filename = res.get('Remote file_id')
        return filename

    def exists(self, name):
        """判断文件名是否可用"""
        return False

    def url(self, name):
        # name = name.replace('\\', '/')
        return self.base_url + name
