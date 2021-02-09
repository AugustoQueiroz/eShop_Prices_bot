import bs4
import urllib
import requests

class eShop_Prices:
    def __init__(self, currency=''):
        self.base_url = 'https://eshop-prices.com/'

        self.currency = currency

    def __parse_games_list_item(self, games_list_item: bs4.element.Tag) -> (str, str):
        return (games_list_item.find_all('h5')[0].string, games_list_item['href'])

    def __parse_country_column(self, country_column: bs4.element.Tag) -> str:
        try:
            return list(country_column.strings)[3].strip()
        except IndexError:
            return list(country_column.strings)[0].strip()

    def get_prices_from_url(self, game_url: str) -> [{str: str}]:
        request_url = self.base_url + game_url + f'?currency={self.currency}'
        print('Making request to ' + request_url)

        response = requests.get(
            request_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0'
            }
        )

        if response.status_code == 200:
            soup = bs4.BeautifulSoup(response.text, 'html.parser')

            prices_table = soup.find_all('table', {'class': 'prices-table'})[0]

            prices = []
            for row in prices_table.tbody.find_all('tr'):
                columns = row.find_all('td')
                try:
                    prices.append(
                        {
                            'country': self.__parse_country_column(columns[1]),
                            'price': columns[3].string.strip()
                        }
                    )
                except IndexError:
                    print(row)

            return prices
        else:
            return f'Error getting prices from game_url! (Status = {response.status_code})'

    def search(self, query: str) -> {str: str}:
        encoded_query = urllib.parse.quote(query, safe='')

        request_url = self.base_url + f'games?q={encoded_query}'

        response = requests.get(
            request_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0'
            }
            )

        if response.status_code == 200:
            soup = bs4.BeautifulSoup(response.text, 'html.parser')

            games_list = soup.find_all('a', {'class': 'games-list-item'})

            results = {}

            for games_list_item in games_list:
                game_name, game_url = self.__parse_games_list_item(games_list_item)
                results[game_name] = game_url

            return results
        else:
            return f'Error performing search! (Status = {response.status_code})'
        pass

    def get_prices(self, game: str) -> [{str: str}]:
        search_results = self.search(game)

        if len(search_results) == 0:
            pass
        elif len(search_results) == 1:
            return self.get_prices_from_url(list(search_results.values())[0])
        else:
            print('More than one game found from that query:')
            for i, game_title in enumerate(search_results.keys()):
                print(f'{i} - {game_title}')
            
            game_to_get = input('What game do you want the prices for (use the number) ? ')

            return self.get_prices_from_url(list(search_results.values())[int(game_to_get)])

if __name__ == '__main__':
    game_query = input('Game to Query ? ')

    print(eShop_Prices().get_prices(game_query))