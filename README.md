# granblue-driver
Things are very messy, rewriting things on the side.

Window size setting must be set to __**small**__ in game settings. Needs viramate for hotkeys and hosting last hosted coop quest because I'm lazy.


# Installation
* Install [Python 3.6](https://www.python.org/downloads/) or higher. If you're installing python for the first time, tick the option to write the python directory into your system's PATH to save yourself the trouble.
* Download and unzip this repo.
* In cmd navigate to the folder you unzipped.
* Enter `pip install -r requirements.txt`
* Place [chrome webdriver](https://sites.google.com/a/chromium.org/chromedriver/downloads) binary in the folder.
* Install chrome/chromium (or whatever works for you).

# Flags
Temp
* --hostslime, --leechslime, --debug (start script in interactive mode)

# Usage
* python gbf.py [profile_name] [options]
* The script will pause upon starting up. Hit enter to unpause when the coop room is all set up and summons are picked.
