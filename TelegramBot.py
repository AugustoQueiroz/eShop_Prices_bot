from __future__ import annotations

import re
import json
import urllib
import requests

from eShop_Prices import eShop_Prices

class InteractionManager:
    def __init__(self, chat_id: int, bot: TelegramBot):
        self.chat_id = chat_id
        self.bot = bot

        self.eShop_scraper = eShop_Prices()

    def _build_prices_message(self, game_title: str, prices: [{str: str}]):
        message_body = f'<strong><u>Current prices around the world for <em>{game_title}</em>:</u></strong>'
        for price in prices:
            message_body += f'\n<strong>{price["country"]}:</strong>\t\t{price["price"]}'
        
        return message_body

    def handle_message(self, message):
        text = message['text']

        if re.match('/start', text):
            self.bot.send_message(
                self.chat_id,
                '''
                Hi there, you can use this bot to quickly and easily get some info about game pricing on the Nintendo eShops around the world\\.
                
                \nUse /prices followed by name of the game you want to search \\(ex\\.: `/prices The Legend of Zelda`\\) to get a list of the prices in each store\\.
                \nUse /currency followed by a currency code \\(ex\\.: `/currency BRL`\\) to get the prices converted to that currency on your next requests\\.
                '''
                )

        elif re.match('/search', text):
            m = re.search('(?<=/search ).*', text)
            if m is not None:
                self.bot.send_action(self.chat_id, action='typing')
                self.search(m.group(0))
            else:
                self.bot.send_message(self.chat_id, 'You must give a game name to search \\(ex\\.: `/search The Legend of Zelda`\\)')
        
        elif re.match('/prices', text):
            m = re.search('(?<=/prices ).*', text)
            if m is not None:
                self.bot.send_action(self.chat_id, action='typing')
                self.get_prices_from_query(m.group(0))
            else:
                self.bot.send_message(self.chat_id, 'You must give a game name to search \\(ex\\.: `/prices The Legend of Zelda`\\)')
        
        elif re.match('/currency', text):
            m = re.search('(?<=/currency ).*', text)
            if m is not None:
                self.eShop_scraper.currency = m.group(0)
                self.bot.send_message(self.chat_id, f'Currency set to {m.group(0)}')

    def handle_callback(self, callback):
        original_message = callback['message']
        data = callback['data']

        if re.search('/prices', data):
            chosen_option = int(re.search('(?<=/prices ).*', data).group(0))
            game_title = original_message['reply_markup']['inline_keyboard'][chosen_option][0]['text']
            search_results = self.eShop_scraper.search(game_title)
            game_title = list(search_results.keys())[0]
            prices = self.eShop_scraper.get_prices_from_url(search_results[game_title])

            self.bot.update_message(
                self.chat_id,
                original_message['message_id'],
                self._build_prices_message(game_title, prices),
                parse_mode='HTML'
            )

    def search(self, query: str):
        results = self.eShop_scraper.search(query)

        response_body = f'Search results for _{query}_:'
        for result in results:
            response_body += f'\n{result}'
        
        self.bot.send_message(self.chat_id, response_body)
    
    def get_prices_from_query(self, query: str):
        search_results = self.eShop_scraper.search(query)

        if len(search_results.keys()) == 0:
            self.bot.send_message(
                self.chat_id,
                f'No game matches the search query _{query}_\\.'
            )
        elif len(search_results.keys()) == 1:
            game_title = list(search_results.keys())[0]
            prices = self.eShop_scraper.get_prices_from_url(search_results[game_title])
            
            self.bot.send_message(
                self.chat_id,
                self._build_prices_message(game_title, prices),
                parse_mode='HTML'
            )
        elif len(search_results.keys()) > 1:
            inline_buttons = []
            for i, result in enumerate(search_results):
                inline_buttons.append([{
                    'text': result,
                    'callback_data': f'/prices {i}'
                }])

            reply_markup = {
                'inline_keyboard': inline_buttons
            }
            
            self.bot.send_message(
                self.chat_id,
                f'More than one game matches _{query}_, which of the following would you like the prices for?',
                reply_markup=urllib.parse.quote(json.dumps(reply_markup), safe='')
            )

class TelegramBot:
    def __init__(self, token: str):
        self.base_url = f'https://api.telegram.org/bot{token}'

        self.ongoing_interactions = {}
        try:
            with open('ongoing_interactions') as oi_file:
                for chat_id in oi_file:
                    self.ongoing_interactions[int(chat_id)] = InteractionManager(int(chat_id), self)
        except FileNotFoundError:
            pass

        try:
            with open('last_processed_update_id') as lpui_file:
                self.last_processed_update_id = int(lpui_file.read())
        except FileNotFoundError:
            self.last_processed_update_id = None

    def __get_updates(self, timeout:int=100, last_processed_update_id:int=None):
        request_url = f'{self.base_url}/getUpdates?timeout={timeout}'
        if last_processed_update_id is not None:
            request_url += f'&offset={last_processed_update_id + 1}'

        response = requests.get(request_url)
        
        if response.status_code == 200:
            response = json.loads(response.text)
            return response['result']
        else:
            print("Error")

    def send_message(self, chat_id: int, message_body: str, parse_mode: str='MarkdownV2', reply_markup=None):
        escaped_message_body = urllib.parse.quote(message_body)
        request_url = f'{self.base_url}/sendMessage?chat_id={chat_id}&text={escaped_message_body}&parse_mode={parse_mode}'
        if reply_markup is not None:
            request_url += f'&reply_markup={reply_markup}'
        print(request_url)
        response = requests.get(request_url)

        if response.status_code != 200:
            print('Error sending message')

    def update_message(self, chat_id: int, message_id: int, message_body: str, parse_mode: str='MarkdownV2', reply_markup=None):
        escaped_message_body = urllib.parse.quote(message_body)
        request_url = f'{self.base_url}/editMessageText?chat_id={chat_id}&message_id={message_id}&text={escaped_message_body}&parse_mode={parse_mode}'
        if reply_markup is not None:
            request_url += f'&reply_markup={reply_markup}'
        print(request_url)
        response = requests.get(request_url)

        if response.status_code != 200:
            print('Error updating message')

    def send_action(self, chat_id: int, action: str):
        request_url = f'{self.base_url}/sendChatAction?chat_id={chat_id}&action={action}'
        response = requests.get(request_url)

        if response.status_code != 200:
            print('Error sending chat action')

    def run(self):
        try:
            while True:
                for update in self.__get_updates(timeout=100, last_processed_update_id=self.last_processed_update_id):
                    if 'message' in update.keys():
                        message = update['message']

                        chat_id = message['chat']['id']

                        if chat_id not in self.ongoing_interactions:
                            self.ongoing_interactions[chat_id] = InteractionManager(chat_id, self)
                        
                        self.ongoing_interactions[chat_id].handle_message(message)

                    elif 'callback_query' in update.keys():
                        chat_id = update['callback_query']['message']['chat']['id']

                        if chat_id not in self.ongoing_interactions:
                            self.ongoing_interactions[chat_id] = InteractionManager(chat_id, self)
                        
                        self.ongoing_interactions[chat_id].handle_callback(update['callback_query'])

                    else:
                        print('Skipping non user non new message')
                        continue

                    self.last_processed_update_id = update['update_id']
        except KeyboardInterrupt:
            self.exit_gracefully()
    
    def exit_gracefully(self):
        with open('last_processed_update_id', 'w') as lpui_file:
            lpui_file.write(f'{self.last_processed_update_id}')
        
        with open('ongoing_interactions', 'w') as oi_file:
            for chat_id in self.ongoing_interactions:
                oi_file.write(f'{chat_id}')

if __name__ == '__main__':
    with open('token') as token_file:
        token = token_file.read()

    print(token)
    
    TelegramBot(token).run()