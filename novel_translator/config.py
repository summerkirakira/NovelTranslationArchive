from dotenv import load_dotenv
import os
from pydantic import BaseModel


load_dotenv()


class Config(BaseModel):
    init_prompt: str = os.getenv('INIT_PROMPT', '接下来你要扮演一个资深日语翻译家，把我发送的文本转换为简体中文。\n 翻译时请遵守以[中文名, 日文名, 性别, 简介]整理的人名csv对照表: %name_bind% \n 同时请遵守以[中文名, 日文名, 简介]整理的译名对照表: %item_bind%\n 同时注意以下内容:\n%other_requirement%\n 请勿在回复中加入任何与翻译无关的内容，谢谢！包括但不限于“会将这段日语文本翻译成简体中文”，“以下是翻译”这些语句。')
    name_bind_prompt: str = os.getenv('NAME_BIND_PROMPT', '请把这段文章中出现的人名以[中文名, 日文名, 性别, 简介]整理为csv译名对照表(包含表头)(请勿使用md格式)，并不附带任何其他内容')
    item_bind_prompt: str = os.getenv('ITEM_BIND_PROMPT', '请把这段文章中出现的专有名词(不包含人名)以[中文名, 日文名, 简介]整理为csv译名对照表(包含表头)(请勿使用md格式)，并不附带任何其他内容')
    brief_prompt: str = os.getenv('BRIEF_PROMPT', '请简要描述这段文本的内容')
    other_requirement: str = os.getenv('OTHER_REQUIREMENT', '')


def get_config() -> Config:
    return Config()
