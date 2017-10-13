# TODO
## General
* **Code's in a mess, clean it up!!**
* Fix popup_check()
* Check if already casting a summon before attempting to summon 
* Don't search for OK in the results page because we might have dismissed it

### Coop routine
* If someone else hosts just ready
* Leech script

### Replace selenium-requests
Why not just use jQuery to send GET and POST requests instead of selenium-requests?
``` GBF.execute_script("return $.ajax({url:'http://game.granbluefantasy.jp/user/status',async:false});")
  ```

def speedtest():
  start = time()
  GBF.execute_script("return $.ajax({url:arguments[0],async:false});", url)
  print(time()-start)

### Programmable Battle Logic

### Snipe raids
* Listen for raid codes on twitter
* Check raid codes
  * `POST http://game.granbluefantasy.jp/quest/battle_key_check`
  * Form data `{"special_token":null,"battle_key":"BB54C3FC"}`
  * Response `{"redirect":"#quest\/supporter_raid\/2427308300\/300401\/1\/2"}`


### Blast slimes

### Play the casino

### Extract useful information
* List supplies

  * Pots and berries
    * `GET http://game.granbluefantasy.jp/item/normal_item_list/1`

  * Player status (AP, AP regen, BP, BP regen)
    * `GET http://game.granbluefantasy.jp/user/status`

  * Weapon EXP Consumables, Limit break bars (Red, Steel, Gold, Damascus bars), Powerups (Celestial Ciphers)  
    * `GET http://game.granbluefantasy.jp/item/evolution_items/0/1`

  * Summon EXP Consumables, Limit break stones (Bright, Moonlight, Sunlight stone)
    * `GET http://game.granbluefantasy.jp/item/evolution_items/0/2`

  * Character EXP Consumables, Limit break items
    * `GET http://game.granbluefantasy.jp/item/evolution_items/0/3`

  * Treasure
    * `GET http://game.granbluefantasy.jp/item/article_list/1`

  * Gacha Tickets
    * `GET http://game.granbluefantasy.jp/item/gacha_ticket_list/1`

  * Other items (It's blank for me?)
    * `GET http://game.granbluefantasy.jp/item/others_items/1`

  * Character List
    * `POST http://game.granbluefantasy.jp/npc/list/1/0`
    * With payload `{"special_token":null,"is_new":true,"sort":{"1":[7,3]},"filter":{"5":"0000","6":"000000","7":"00000","13":"000000"}}`

  * Weapon List
    * `POST http://game.granbluefantasy.jp/weapon/list/1/0`
    * With payload `{"special_token":null,"is_new":true,"sort":{"1":[10,3]},"filter":{"5":"0000","6":"000000","8":"0000000000","9":0,"10":0,"11":0,"12":0}}`

  * Summon List
    * `POST http://game.granbluefantasy.jp/summon/list/1/0`
    * With payload `{"special_token":null,"is_new":true,"sort":{"1":[7,3]},"filter":{"5":"0000","6":"000000","9":0,"12":0}}`

  * Outfit List
    * `GET http://game.granbluefantasy.jp/skin/list/1/-1` 
    

### Not get ourselves banned again! _Should be solved!_
- [x] Introduce random delay in clicking
- [x] Check if click variance is *really* working
- [ ] Don't use accounts you don't want to get banned with this script /w\

### Battle
* Parse all the data in a raid page with a single function!
  * Enemies/Allies bar stats
  * Ougi (already implemented)
  * Type of raid
  * Raid Time and humans in raid
  * Game speed
  * Name of party characters
* Choose different parties based on what raid we're going in
* Load different stratergies based on what raid we're in

### Features
* Load settings from a config file. JSON? Better than having to hardcode everything.
* Side script to create and play alts?
* Use tweepy to open up a stream to listen for targeted raids
* Reduce dependence on viramate for battles
  * Summon selection
  * Handle popups (We can handle *enough* stuff now)
  * Handle summons
