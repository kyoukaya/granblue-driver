# TODO
## General
* **Code's in a mess, clean it up!!**
* Fix popup_check()
* Check if already casting a summon before attempting to summon 
* Don't search for OK in the results page because we might have dismissed it

### Coop routine
* If someone else hosts just ready
* Leech script

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
