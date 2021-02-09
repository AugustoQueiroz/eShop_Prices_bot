import re
import json
import urllib
import requests

from eShop_Prices import eShop_Prices

eShop = eShop_Prices()

class InteractionManager:
    def __init__(self, chat_id, bot):
        self.chat_id = chat_id
        self.bot = bot

    def is_finished(self):
        return True

    def handle_message(self, message):
        text = message['text']

        if re.match('/search', text):
            m = re.search('(?<=/search ).*', text)
            if m is not None:
                self.bot.send_action(self.chat_id, action='typing')
                self.search(m.group(0))
            else:
                self.bot.send_message(self.chat_id, 'You must give a game name to search \\(ex\\.: `/search The Legend of Zelda`\\)')
        
        if re.match('/prices', text):
            m = re.search('(?<=/prices ).*', text)
            if m is not None:
                self.bot.send_action(self.chat_id, action='typing')
                self.get_prices_from_query(m.group(0))
            else:
                self.bot.send_message(self.chat_id, 'You must give a game name to search \\(ex\\.: `/prices The Legend of Zelda`\\)')

    def handle_callback(self, callback):
        pass
    
    def search(self, query):
        results = eShop.search(query)

        response_body = f'Search results for _{query}_:'
        for result in results:
            response_body += f'\n{result}'
        
        self.bot.send_message(self.chat_id, response_body)
    
    def get_prices_from_query(self, query):
        search_results = eShop.search(query)

        if len(search_results.keys()) == 0:
            self.bot.send_message(
                self.chat_id,
                f'No game matches the search query _{query}_\\.'
            )
        elif len(search_results.keys()) == 1:
            game_title = list(search_results.keys())[0]
            prices = eShop.get_prices_from_url(search_results[game_title])

            message_body = f'<strong><u>Current prices around the world for <em>{game_title}</em>:</u></strong>'
            for price in prices:
                message_body += f'\n<strong>{price["country"]}:</strong>\t\t{price["price"]}'
            
            self.bot.send_message(
                self.chat_id,
                message_body,
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
    def __init__(self, token):
        self.base_url = f'https://api.telegram.org/bot{token}'

        self.ongoing_interactions = {}

        try:
            with open('last_processed_update_id') as lpui_file:
                self.last_processed_update_id = int(lpui_file.read())
        except FileNotFoundError:
            self.last_processed_update_id = None

    def __get_updates(self, timeout=100, last_processed_update_id=None):
        request_url = f'{self.base_url}/getUpdates?timeout={timeout}'
        if last_processed_update_id is not None:
            request_url += f'&offset={last_processed_update_id + 1}'

        response = requests.get(request_url)
        
        if response.status_code == 200:
            response = json.loads(response.text)
            return response['result']
        else:
            print("Error")

    def send_message(self, chat_id, message_body, parse_mode='MarkdownV2', reply_markup=None):
        escaped_message_body = urllib.parse.quote(message_body)
        request_url = f'{self.base_url}/sendMessage?chat_id={chat_id}&text={escaped_message_body}&parse_mode={parse_mode}'
        if reply_markup is not None:
            request_url += f'&reply_markup={reply_markup}'
        print(request_url)
        response = requests.get(request_url)

        if response.status_code != 200:
            print('Error sending message')

    def send_action(self, chat_id, action):
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

                        if chat_id not in self.ongoing_interactions or self.ongoing_interactions[chat_id].is_finished():
                            self.ongoing_interactions[chat_id] = InteractionManager(chat_id, self)
                        
                        self.ongoing_interactions[chat_id].handle_message(message)

                    elif 'callback_query' in update.keys():
                        print(update)

                    else:
                        print('Skipping non user non new message')
                        continue

                    self.last_processed_update_id = update['update_id']
        except KeyboardInterrupt:
            self.exit_gracefully()
    
    def exit_gracefully(self):
        with open('last_processed_update_id', 'w') as lpui_file:
            lpui_file.write(f'{self.last_processed_update_id}')

if __name__ == '__main__':
    with open('token') as token_file:
        token = token_file.read()

    print(token)
    
    TelegramBot(token).run()