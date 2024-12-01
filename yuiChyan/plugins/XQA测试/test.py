from sqlitedict import SqliteDict
import json
import os

FILE_PATH = os.path.dirname(__file__)

def get_database():
    # 创建目录
    img_path = os.path.join(FILE_PATH, 'img/')
    if not os.path.exists(img_path):
        os.makedirs(img_path)
    db_path = os.path.join(FILE_PATH, 'data.sqlite')
    # 替换默认的pickle为josn的形式读写数据库
    db = SqliteDict(db_path, encode=json.dumps, decode=json.loads, autocommit=True)
    return db

db = dict(get_database())
db_path = os.path.join(os.path.dirname(__file__), 'db.json')
with open(db_path, 'w', encoding='UTF-8') as f:
    json.dump(db, f, indent=4, ensure_ascii=False)
