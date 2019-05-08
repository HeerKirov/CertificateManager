# CERTIFICATE MANAGER
竞赛证书上传与审核系统
> CODING...

## Description
后端。仅包括API。  
技术栈：
* python3
* django
* django REST framework
* postgreSQL

## Build
1. 配置文件
```bash
cp config.py.example config.py
```
将模版复制一份，然后编辑`config.py`文件：
```python
URL_PREFIX = 'manager/'     # 在URL中添加在后续地址前的前缀

DEBUG = True                        # debug模式
SECRET_KEY = ''                     # 密钥

DATABASE = {                        # postgreSQL数据库的配置
    'DATABASE': 'certificate_manager',  # 数据库的名称
    'USERNAME': 'postgres',         # 数据库用户名
    'PASSWORD': '',                 # 密码
    'HOST': 'localhost',            # 连接的主机HOST
    'PORT': '5432'                  # 连接的端口PORT
}

INITIAL_ADMIN_USER = {              # 初始化数据库时，会使用这些信息创建第一个管理员
    'username': 'admin',            # 管理员的用户名
    'password': 'admin',            # 管理员的密码
    'name': 'Administrator'         # 管理员的昵称
}
```
2. 安装
```bash
pip3 install -r requirements.txt
python3 manage.py migrate
```
3. 测试运行
```bash
python3 manage.py runserver 0.0.0.0:8000    # 启动测试服务器
```