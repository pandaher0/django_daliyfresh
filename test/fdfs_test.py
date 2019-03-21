# Author:hxj
from fdfs_client.client import Fdfs_client

# 指定client文件路径
client = Fdfs_client(r'C:\Users\Administrator\AppData\Local\Programs\Python\Python37\client.conf')

# 上传文件
ret = client.upload_by_filename(r'C:\Users\Administrator\Pictures\006E6mtPly1fzrtr1z5chj30v91iw7i3.jpg')

print(ret)
# {'Group name': 'group1', 'Remote file_id': 'group1\\M00/00/00/rBGEylyTGYqAHX63AANmSWua1uE190.jpg', 'Status': 'Upload successed.', 'Local file name': 'C:\\Users\\Administrator\\Pictures\\006E6mtPly1fzrtr1z5chj30v91iw7i3.jpg', 'Uploaded size': '217.00KB', 'Storage IP': '39.106.44.166'}
