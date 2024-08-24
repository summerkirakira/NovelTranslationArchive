import pathlib
from typing import Optional
import csv
from .name_binding import load_name_binding_list, save_name_binding_list, dict_to_csv_text, csv_text_to_dict, remove_duplicate
from .config import get_config
from universe_ai import MonicaClient
from universe_ai.model import Message, MessageChain


class Translator:
    def __init__(self, cache_path: Optional[pathlib.Path] = None, source: str = 'monica', is_advanced: bool = False):
        if cache_path is None:
            cache_path = pathlib.Path('data')
        if not cache_path.exists():
            cache_path.mkdir(parents=True)
        self.name_bind_list = load_name_binding_list(cache_path / 'name_bind.csv')
        self.item_bind_list = load_name_binding_list(cache_path / 'item_bind.csv')
        self.config = get_config()
        self.client = MonicaClient()
        self.is_advanced = is_advanced
        self.start_up()
        self.is_send_system_prompt = False

    @property
    def _start_up_message(self) -> str:
        name_bind = dict_to_csv_text(self.name_bind_list)
        item_bind = dict_to_csv_text(self.item_bind_list)
        return self.config.init_prompt.replace('%name_bind%', name_bind).replace('%item_bind%', item_bind).replace('%other_requirement%', self.config.other_requirement)

    async def _handle_chat(self, message: str) -> str:
        reply = ''
        print()
        async for response in self.client.chat(message=MessageChain(messages=[Message(type="text", content=message)]), is_advanced=self.is_advanced, is_continue=True):
            reply += response.content
            print(response.content, end='')
        print()
        return reply

    def start_up(self):
        self.client.save_checkpoint('start_up')

    async def translate(self, data: str) -> str:
        is_refresh_prompt = False
        if is_refresh_prompt or not self.is_send_system_prompt:
            self.client.load_checkpoint('start_up')
            await self._handle_chat(self._start_up_message)
            self.client.save_checkpoint('send_system_prompt')
            self.is_send_system_prompt = True
        else:
            self.client.load_checkpoint('send_system_prompt')
        reply = await self._handle_chat(data)

        if '无法处理' in reply:
            raise Exception('无法处理')

        if is_refresh_prompt:
            self.client.save_checkpoint('after_translate')

            name_bind = await self.name_bind(self.config.name_bind_prompt)
            self.client.load_checkpoint('after_translate')
            item_bind = await self.item_bind(self.config.item_bind_prompt)

            new_name_bind_list = csv_text_to_dict(name_bind)
            new_item_bind_list = csv_text_to_dict(item_bind)

            formatted_name_bind_list = []
            for item in new_name_bind_list:
                new_item = {}
                for key, val in item.items():
                    new_item[key.strip()] = val.strip()
                formatted_name_bind_list.append(new_item)
            new_name_bind_list = formatted_name_bind_list

            formatted_item_bind_list = []
            for item in new_item_bind_list:
                new_item = {}
                for key, val in item.items():
                    new_item[key.strip()] = val.strip()
                formatted_item_bind_list.append(new_item)
            new_item_bind_list = formatted_item_bind_list

            self.name_bind_list = remove_duplicate(self.name_bind_list + new_name_bind_list, '中文名')
            self.item_bind_list = remove_duplicate(self.item_bind_list + new_item_bind_list, '中文名')

            save_name_binding_list(pathlib.Path('data/name_bind.csv'), self.name_bind_list)
            save_name_binding_list(pathlib.Path('data/item_bind.csv'), self.item_bind_list)

        return reply

    async def name_bind(self, data: str) -> str:
        self.client.load_checkpoint('after_translate')
        reply = await self._handle_chat(data)
        self.client.save_checkpoint('after_name_bind')
        return reply

    async def item_bind(self, data: str) -> str:
        self.client.load_checkpoint('after_translate')
        reply = await self._handle_chat(data)
        self.client.save_checkpoint('after_item_bind')
        return reply
