# eShop_Prices_Bot

A Telegram interface for [eshop-prices.com](eshop-prices.com)

## Commands

- [x] `/prices + <game_name>` : Return the price list for the asked game.
    - [x] `/prices` gives the list of favorites to pick from.
- [x] `/topdiscounts` : Return the list of games with the highest discount currently.
- [x] `/currency` : Change the currency the prices should be displayed in.
- [x] `/addfavorite` : Add a game to your favorites list and get a notification when it is on sale somewhere.
    - [x] `/removefavorite`
    - [x] `/myfavorites`
    - [ ] Get notified when favorites are on sale
- [ ] `/forgetme` : Command to delete all stored information about a user (currency and favorites)
- [ ] `/mydata` : Send the user all their stored information (currency and favorite games)