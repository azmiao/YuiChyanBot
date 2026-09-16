import logging
import os
import sys

from yuiChyan.resources import current_dir

log_dir = os.path.join(current_dir, 'logs')
os.makedirs(log_dir, exist_ok=True)
error_file = os.path.abspath(os.path.join(log_dir, 'errors.log'))

formatter = logging.Formatter('[%(asctime)s %(name)s] %(levelname)s: %(message)s')
default_handler = logging.StreamHandler(sys.stdout)
default_handler.setFormatter(formatter)

error_handler = logging.FileHandler(error_file, encoding='utf-8')
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)


class AioCqhttpEventFilter(logging.Filter):
    """过滤 aiocqhttp 自带的低信息量事件日志（`received event: xxx`）。

    aiocqhttp 会复用 server_app.logger 输出该日志，但只包含事件类型、缺乏群号和消息内容，
    屏蔽后由项目在 DEBUG 模式下打印事件与消息的真实内容。
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return not record.getMessage().startswith('received event: ')


def new_logger(name: str, debug: bool = True) -> logging.Logger:
    _logger = logging.getLogger(name)
    _logger.addHandler(default_handler)
    _logger.addHandler(error_handler)
    _logger.setLevel(logging.DEBUG if debug else logging.INFO)
    _logger.propagate = False
    return _logger
