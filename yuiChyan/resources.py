import os

from rocksdict import Rdict

# 基础资源路径
base_res_path = os.path.join(os.path.dirname(__file__), 'res')
os.makedirs(base_res_path, exist_ok=True)
# 本项目使用高性能并发数据库 rocksdict 底层为 rocksdb | YuiChyanBot 结束时会自动触发 db.close()
base_db_path = os.path.join(base_res_path, 'db')
os.makedirs(base_db_path, exist_ok=True)
# 基础图片路径
base_img_path = os.path.join(base_res_path, 'img')
os.makedirs(base_img_path, exist_ok=True)
# XQA资源路径
xqa_img_path = os.path.join(base_img_path, 'xqa')
os.makedirs(xqa_img_path, exist_ok=True)


# 授权管理数据库
auth_db_ = Rdict(os.path.join(base_db_path, 'auth.db'))
# 服务管理数据库
service_db_ = Rdict(os.path.join(base_db_path, 'service.db'))
# XQA数据库
xqa_db_ = Rdict(os.path.join(base_db_path, 'xqa.db'))
