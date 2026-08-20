import logging
import allure
import pytest
import os
import json
import traceback
import pathlib

path = pathlib.Path(__file__).resolve()

logging_lever = 'INFO'
LOGGING_FORMAT = '[%(asctime)s][%(levelname)-6s][%(name)s:%(lineno)d]: %(message)s'


def get_logger(name):
    if hasattr(name, '__module__') and hasattr(name, '__name__'):
        logger = logging.getLogger(name.__module__ + '.' + name.__name__)
    else:
        logger = logging.getLogger(str(name))

    return logger


def log(content, title=None):
    """
        使用這個 function 的話, log 會隔別記錄在大 function 下面, 而不會像 _logging.info 一樣出現在 Terminal,
        建議如果是開發使用的話, 使用 _logging 會比較適合, 若是需要在 Jenkins 上執行來確認結果的話, 使用 log。

    :param content: 如果是 json 的話, 會直接轉成 json tree, 方便觀看
    :param title:

    :return:
    """
    tb = traceback.format_stack()
    tb_line = 0

    while str(tb[tb_line]).find(str(path)) == -1:
        tb_line = tb_line + 1

    err_text = tb[tb_line - 1].split(", ")
    file_name = os.path.split(err_text[0])[1]
    line_no = err_text[1]

    message = json.dumps(content, indent=1, default=str, ensure_ascii=False)

    if title is None:
        step_name = f"[Log]"
    else:
        step_name = f"[Log]: [ {title} ]"

    with allure.step(step_name):
        allure.attach(message, name=f'[ {file_name}:{line_no} ]', attachment_type=allure.attachment_type.TEXT)
