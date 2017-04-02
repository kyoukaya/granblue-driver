import json
from os import makedirs, path
from random import randint, uniform
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException,
                                        TimeoutException,
                                        UnexpectedAlertPresentException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep, strftime, time
from code import interact

from pushbullet import InvalidKeyError, Pushbullet
from seleniumrequests import Chrome

CFG = json.load(open('config.json', 'r', encoding='utf-8'))
HOTKEYS = CFG['viramate_hotkeys']
USE_PB = CFG['use_pb']
PB_KEY = CFG['keys']['pushbullet']
LOG_FILE = '[{}] GBFDriver.log'.format(strftime('%m-%d %H%M'))


def log(message):
    """Prints to console and outputs to log file"""
    try:
        with open('.\\logs\\'+LOG_FILE, 'a', encoding='utf-8', newline='') as fout:
            message = '[{}] {}'.format(strftime('%a %H:%M:%S'), message)
            print(message)
            fout.write(message + '\n')
    except FileNotFoundError:
        makedirs('.\\logs')
        log('Created log folder')
        log(message)


def setup_driver_instance():
    profile = CFG['chrome_profiles'][2]
    chrome_binary = CFG['chrome_binary']
    webdriver_binary = CFG['webdriver_binary']

    print(f'''Config loaded...
PB: {PB_KEY}, USE_PB: {USE_PB}, HOTKEYS: {HOTKEYS}, PROFILE: {profile}
chrome_binary: {chrome_binary}, webdriver_binary: {webdriver_binary}
''')

    options = webdriver.ChromeOptions()
    profile = path.abspath(profile)
    log(f'Profile path: {profile}')
    options.add_argument('user-data-dir={}'.format(profile))
    options.binary_location = '.\\chrome-win32\\chrome.exe'
    gbf = Chrome(executable_path='.\\chromedriver.exe', chrome_options=options)
    return gbf


def alert_operator(message, pause=True):
    """Push alerts for CAPTCHAs, etc."""
    if USE_PB is True and message.__len__() > 0:
        try:
            pub = Pushbullet(PB_KEY)
            push = pub.push_note('GBFdriver', message)
            log(push)
        except InvalidKeyError:
            log('Invalid PB API key!')
    print(message)
    if pause:
        input('Press enter to continue')


def set_viewport_size(driver, width, height):
    window_size = driver.execute_script("""
        return [window.outerWidth - window.innerWidth + arguments[0],
          window.outerHeight - window.innerHeight + arguments[1]];
          """, width, height)
    driver.set_window_size(*window_size)


def random_click(ele, var_x, var_y):
    clicked = False
    while not clicked:
        actions = ActionChains(GBF)
        actions.move_to_element(ele).move_by_offset(var_x, var_y).click_and_hold().perform()
        sleep(uniform(0.05, 0.15))
        actions.release().perform()
        clicked = True


def js_click(ele, var_x, var_y):
    """In the off case we might not want to use the default way of clicking things"""
    ele_loc = ele.location
    ele_loc_x = ele_loc['x']+var_x
    ele_loc_y = ele_loc['y']+var_y
    script = 'document.elementFromPoint({},{}).click();'.format(ele_loc_x, ele_loc_y)
    GBF.execute_script(script)


def clicker(ele, delay=0.5, kind='random', variance=0.2):
    """Takes a CSS selector in the form of a CSS selector/xpath string or an element object
    and clicks on it."""
    if isinstance(ele, str) and ele_check(ele):
        log('Clicking on \'{}\'. Method: {}, variance: {}'.format(ele, kind, variance))
        if ele[0] == '/':
            ele = GBF.find_element_by_xpath(ele)
        else:
            ele = GBF.find_element_by_css_selector(ele)
    elif isinstance(ele, str):
        log('Element does not exist: {}'.format(ele))
        return
    if delay > 0:
        # Shouldn't really matter but it helps us to not spam clicks when stuck in loops
        delay = uniform(delay, 0.5 * delay)
        sleep(delay)
    try:
        # Variance routine
        size = {k: int(ele.size[k]*variance) for k in ele.size}
        var_x = randint(0 - size['width'], size['width'])
        var_y = randint(0 - size['height'], size['height'])
        if size['width'] < 3 or size['height'] < 3:
            log('WARNING: Low variance expected, button is too small\n' +
                f'{ele.size}, {var_x}, {var_y}')

        # Handle potential errors that arise from non-existent elements
        if kind == 'random':
            random_click(ele, var_x, var_y)
        elif kind == 'js':
            # Simulate a click in javascript
            js_click(ele, var_x, var_y)
        elif kind == 'fallback':
            # Can't introduce click variance with native methods
            ele.click()
        else:
            log('Invalid kind \'{}\' inputted!'.format(kind))
    except (StaleElementReferenceException, NoSuchElementException):
        log('Element does not exist')
        return False
    except UnexpectedAlertPresentException as exp:
        log('{}\nAlert detected, dismissing'.format(exp))
        GBF.switch_to.alert.accept()
        clicker(ele, delay, kind, variance)


def send_keys_to_element(ele, keys):
    if isinstance(ele, str) and ele_check(ele):
        if ele[0] == '/':
            ele = GBF.find_element_by_xpath(ele)
        else:
            ele = GBF.find_element_by_css_selector(ele)
    elif isinstance(ele, str):
        log('Element does not exist: {}'.format(ele))
        return
    ele.send_keys(keys)


def ele_check(ele, wait=1):
    try:
        if ele[0] == '/':
            WebDriverWait(GBF, wait, poll_frequency=0.10).until(
                EC.visibility_of_element_located((By.XPATH, ele))
            )
            return True
        else:
            WebDriverWait(GBF, wait, poll_frequency=0.10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ele))
            )
            return True
    except TimeoutException:
        return False
    except UnexpectedAlertPresentException as exp:
        log('{}\nAlert detected, dismissing'.format(exp))
        GBF.switch_to_alert().accept()
        return ele_check(ele)


def wait_until_css(css, maxwait=5):
    log('Waiting for {} for {} seconds'.format(css, maxwait))
    waiting = True
    start = time()
    while waiting:
        if ele_check(css):
            return True
        else:
            if (time() - start) > maxwait:
                log('Timed out')
                return False


def load_page(url, wait_for='', ignore_url=False):
    GBF.get(url)
    sleep(0.3)  # Not entirely sure how we should detect redirects...
    if GBF.current_url != url and not ignore_url:
        message = 'Unexpected URL: {}'.format(GBF.current_url)
        alert_operator(message)
        log(message)
    if wait_for != '':
        wait_until_css(wait_for, maxwait=2)


def skill_check():
    """Returns a list of lists with skill availability booleans"""
    available = []
    cards = GBF.find_elements_by_css_selector('.quick-panel.prt-ability-list')
    for counter in range(0, len(cards)):
        char_avail = []
        char = cards[counter].find_elements_by_css_selector('.lis-ability')
        for charcount in range(0, len(char)):
            if char[charcount].get_attribute('class') == \
                    'lis-ability btn-ability-available quick-button':
                char_avail.append(True)
            else:
                char_avail.append(False)
        available.append(char_avail)
    return available


def do_skill(character, skill, target=-1):
    # Viramate dependency
    available = skill_check()
    if not available[character][skill]:
        log('Character {}\'s skill {} is unavailable.'.format(character, skill))
    log('Using character {}\'s skill {}. Target {}'.format
        (character, skill, target))
    actions = ActionChains(GBF)
    actions.send_keys(format(character + 1, str())).perform()
    sleep(0.2)
    actions.send_keys(HOTKEYS[skill]).perform()
    sleep(0.2)
    if target > -1:
        actions.send_keys(HOTKEYS[target]).perform()
        sleep(0.2)


def summon_check():
    """Returns list of available summons"""
    if not ele_check('.quick-summon'):
        log('Couldn\'t find summons')
        return
    cards = GBF.find_elements_by_css_selector('.quick-summon')
    available = []
    for counter in range(0, 6):
        if cards[counter].get_attribute('class') == 'quick-summon available':
            available.append(counter)
        else:
            continue
    log('Available summons: {}'.format(str(available)))
    return available


def do_summon(num):
    """We should probably use a click instead since that's way faster"""
    if num not in summon_check():
        log('Summon {} unavailable!'.format(num))
        return
    log('Using summon number {}'.format(num))
    actions = ActionChains(GBF)
    actions.send_keys(5).perform()  # Viramate dependency
    sleep(0.5)
    actions.send_keys(HOTKEYS[num]).perform()
    sleep(0.5)
    actions.send_keys(Keys.SPACE).perform()


def ougi_check():
    if ele_check('.btn-lock.lock0'):
        return True
    elif ele_check('.btn-lock.lock1'):
        return False


def set_ougi(ougi):
    # Viramate dependency
    while ougi != ougi_check():
        actions = ActionChains(GBF)
        actions.send_keys('c').perform()
        sleep(0.2)


def do_attack(auto=False, ougi=False):
    if not ele_check('.btn-attack-start.display-on'):
        log('Unable to attack!')
        return False
    if ougi != ougi_check():
        set_ougi(ougi)
    log('Attacking. Auto={}, Ougi={}'.format(auto, ougi))
    clicker('.btn-attack-start.display-on', variance=.25)
    if auto:
        if wait_until_css('.btn-auto'):
            clicker('.btn-auto')
    return True


def wait_until_url(url):
    start = time()
    while (time() - start) < 40:
        if url in GBF.current_url:
            return
    log('Somehow we\'re at {}'.format(GBF.current_url))


def popup_check():
    """Detects and deals with popups"""
    try:
        ele = GBF.find_element_by_css_selector('.prt-popup-header')
        if not ele.is_displayed():
            return
    except Exception:
        return
    text = ele.text
    if text == 'Not enough AP':
        log('Not enough AP, using 1/2 pot')
        clicker('.btn-use-full.index-1')
        if wait_until_css('.btn-usual-ok'):
            clicker('.btn-usual-ok')
            return
    elif text == 'Access Verification':
        # We can push the captcha image to the operator and wait for a response through PB, just an
        # idea
        alert_operator('CAPTCHA detected! Help!')
        return
    else:
        # if ele_check('.btn-usual-cancel'):
        log('"{}" popup detected and dismissed.'.format(text))
        actions = ActionChains(GBF)
        actions.send_keys('`').send_keys(Keys.SPACE).perform()  # Viramate dependency


def check_bp():
    wait_until_css('prt-user-bp-value')
    bp = GBF.find_elements_by_class_name('prt-user-bp-value')[0]
    num = bp.get_attribute('title')
    return int(num)


def check_health():
    log('Checking health')
    characters = GBF.find_elements_by_class_name('prt-gauge-hp-inner')
    thp = []
    for i in range(4):
        percent = characters[i].get_attribute('style').split()[1]
        thp.append(int(percent[0:-2]))
    return thp


def wait_for_skill_queue():
    log('Waiting for skills to finish casting')
    while not ele_check('.prt-ability-rail-overlayer.hide'):
        if GBF.current_url not in 'http://game.granbluefantasy.jp/#raid_multi/':
            log('We seem to have exited the raid page while waiting for skills')
            return False
    return True


def wait_for_ready():
    waiting = True
    start = time()
    while waiting:
        if wait_until_css('.btn-attack-start.display-on'):
            log('Ready!')
            return True
        else:
            if (time() - start) > 10:
                return False
            if 'http://game.granbluefantasy.jp/#raid_multi/' not in GBF.current_url:
                log('We seem to have exited the raid page while waiting for ready')
                return False
            continue


def results_page(homepage, target, rounds):
    # Need to figure out if a hell is triggered
    # Character EMP id cjs-lp-rankup
    log('In results page')
    wait_until_css('.btn-usual-ok', maxwait=1)
    load_page(homepage, target, ignore_url=True)
    rounds += 1
    return rounds


def raid_battle():
    """Handles what we do in a fight"""
    if not wait_for_ready():
        return
    log('In battle page')
    do_summon(5)
    if not wait_for_skill_queue():
        return
    if not do_attack():
        return
    sleep(1)
    GBF.refresh()


def create_coop_lobby():
    target = '.btn-create-room.location-href'
    target2 = '.btn-entry-room'
    if wait_until_css(target, maxwait=2):
        clicker(target)
    if wait_until_css(target2, maxwait=2):
        clicker(target2)


def coop_lobby():
    log('In coop lobby page')
    target = '.btn-repeat-last'
    target2 = '.btn-quest-start.multi.se-quest-start'
    start = time()
    while True:
        popup_check()
        c_url = GBF.current_url
        if c_url == 'http://game.granbluefantasy.jp/#coopraid' or \
           c_url == 'http://game.granbluefantasy.jp/#coopraid/room/entry':
            create_coop_lobby()
        elif 'http://game.granbluefantasy.jp/#coopraid/room/' not in c_url:
            return
        if ele_check('.btn-make-ready-large.not-ready', wait=0):
            # We'll try to handle party and summon selection someday
            alert_operator('Please choose a summon')
        if ele_check(target, wait=0):
            clicker(target)
        if ele_check(target2, wait=0):
            clicker(target2)
            sleep(0.5)
            popup_check()
            sleep(0.5)
            return
        if (time() - start) > 10:
            # Refresh the room after awhile because it likes to get stuck
            GBF.refresh()
            return


def top_page():
    clicker('.btn-login.switch-position')


def authentication_page():
    clicker('//*[@id="gree-login"]/img')
    # clicker('//*[@id="mobage-login"]/img')
    # clicker('//*[@id="dmm-login"]/img')


def wait_for_page_load():
    start_time = time()
    while True:
        if GBF.execute_script('return document.readyState;') == 'complete':
            return
        elif (time() - start_time) > 5:
            log('Timed out while waiting for page to load...')
            return


def play_poker():
    """Poker routine adapted from https://github.com/shengdi/granblue-selenium
    Only works on the small setting of the game as the clicks to hold cards is hardcoded"""
    # Only get the page if we're not on the page...
    if GBF.current_url != 'http://game.granbluefantasy.jp/#casino/game/poker/200040':
        GBF.get("http://game.granbluefantasy.jp/#casino/game/poker/200040")
    wait_until_css(".prt-start")
    # Deal
    clicker(".prt-start")
    wait_until_css('.prt-ok')

    cards = []
    suits = []
    clicks = []
    counts = {'0': 0, '1': 0, '2': 0, '3': 0, '4': 0, '5': 0}
    for card in GBF.execute_script('return cards_1_Array'):
        suit = int(card[:2].strip('_'))
        rank = int(card[-2:].strip('_'))
        cards.append((suit, rank))
    for i in range(1, 6):
        """
        Suites: Spade = 1, Hearts = 2, Diamonds = 3, Club = 4, Joker = 99
        Ranks: A = 1, 2 = 2, ..., 10 = 10, J = 11, Q = 12, K = 13, Joker = 99
        """
        num = GBF.execute_script("return exportRoot.cards_%d[1]" % i)
        if num in cards:
            print('cards: ')
            print(cards)
            print('num')
            print(num)
            # Click this..
            clicks.append(i)  # Click card number i
            # Find the duplicate and append to clicks
            clicks.append(cards.index(num) + 1)
        if num == '99':
            clicks.append(i)  # Click card number i

        # Count suits..
        suit = GBF.execute_script("return exportRoot.cards_%d[0]" % i)
        if suit == '99':
            # bah just ignore..since joker has been selected it won try all
            # suits..
            suit = '0'
        counts[suit] += 1
        suits.append(suit)
        cards.append(num)

    # If no duplicates found just click all of the same suite..
    if len(clicks) == 0:
        for i in counts:
            if counts[i] == 4:
                # Hold all of this suite..
                for j, k in enumerate(suits):
                    del k
                    if suits == i:
                        clicks.append(j + 1)

    hold = set(clicks)
    print(hold)

    # try x 10 y 400
    # try x 100 y 224

    # actions = ActionChains(GBF)
    # actions.send_keys(Keys.END).perform()
    # actions.move_to_element(GBF.find_elements_by_id("cav")[0]).perform()

    # 0,0 is card 3
    # alright we just loop and print ba
    # for x in range(0,320,10):
    #  for y in range(0,400,10):
    #    actions = ActionsChains(client.GBF)

    canv = GBF.find_element_by_id("canv")
    for i in hold:
        if i == 1:
            print('holding card 1')
            actions = ActionChains(GBF)
            actions.move_to_element_with_offset(
                canv, 20, 210).click().perform()
        if i == 2:
            print('holding card 2')
            actions = ActionChains(GBF)
            actions.move_to_element_with_offset(
                canv, 80, 210).click().perform()
        if i == 3:
            print('holding card 3')
            actions = ActionChains(GBF)
            actions.move_to_element_with_offset(
                canv, 140, 210).click().perform()
        if i == 4:
            print('holding card 4')
            actions = ActionChains(GBF)
            actions.move_to_element_with_offset(
                canv, 200, 210).click().perform()
        if i == 5:
            print('holding card 5')
            actions = ActionChains(GBF)
            actions.move_to_element_with_offset(
                canv, 260, 210).click().perform()

    # Keep
    sleep(1)
    clicker(".prt-ok")

    # Check if we get to doubleup...
    # Check if prt-yes-shine and prt-no-shine is visiable...
    doubleup = False
    print('waiting for doubleup')
    wait_until_css(".prt-yes", maxwait=5)
    # check prt-yes, if it has display: none that means we have no doubleup
    # or check if it has display: block
    yes = GBF.find_elements_by_class_name("prt-yes")[0]
    if yes.value_of_css_property('display') == 'block':
        clicker('.prt-yes')
        doubleup = True
        print('doubleup !')
    else:
        print('no doubleup')
        return

    if doubleup:
        count_doubleup = 0
        while count_doubleup < 11:
            sleep(2)
            doubleup_card_1 = GBF.execute_script(
                "return exportRoot.doubleup_card_1[1]")
            high = GBF.find_elements_by_class_name("prt-high-shine")[0]
            low = GBF.find_elements_by_class_name("prt-low-shine")[0]
            high_array = ['2', '3', '4', '5', '6', '7']
            low_array = ['8', '9', '10', '11', '12', '13', '1']

            if doubleup_card_1 in high_array:
                print('card is %s, choosing high !' % doubleup_card_1)
                clicker('//*[@id="wrapper"]/div[3]/div[2]/div[8]/div[6]')
            elif doubleup_card_1 in low_array:
                print('card is %s, choosing low !' % doubleup_card_1)
                clicker('//*[@id="wrapper"]/div[3]/div[2]/div[8]/div[5]')

            doubleup_card_2 = GBF.execute_script(
                "return exportRoot.doubleup_card_1[1]")
            # check if fail...
            sleep(3)
            # check prt-yes, if it has display: none that means we have no
            # doubleup
            check_fail = GBF.find_elements_by_class_name("prt-yes")[0]
            if check_fail.value_of_css_property('display') == 'block':
                print('doubleup succeed !')
            else:
                print('doubleup failed..')
                return

            # if doubleup_card_2 == u'8':
            #  click_displayed("prt-no-shine")
            #  print 'met 8..not double upping..'
            #  return
            # else:
            clicker(".prt-yes")
            print('doubleup again !')
            count_doubleup += 1
    else:
        print('returning')
        return


def loop_poker():
    lost = 0
    time_start = time()
    while (time() - time_start) < (60 * 60 * 3):
        popup_check()  # Should be able to detect captchas
        play_poker()
        lost += 1
        print('Lost me %d gold' % (lost * 1000))
    alert_operator('Bot done')


def main_loop():
    # We should go to http://game.granbluefantasy.jp/#top first and check if we need to log in
    homepage = 'http://game.granbluefantasy.jp/#coopraid'
    target = '.prt-head-current'
    rounds = 0
    while True:
        wait_for_page_load()
        cur_url = GBF.current_url
        if 'http://game.granbluefantasy.jp/#coopraid' in cur_url:
            coop_lobby()
            popup_check()  # Checks for CAPTCHAs and weird stuff after we hit the start button
        elif 'http://game.granbluefantasy.jp/#raid_multi' in cur_url:
            raid_battle()
        elif 'http://game.granbluefantasy.jp/#result_multi' in cur_url:
            rounds = results_page(homepage, target, rounds)
        elif 'http://game.granbluefantasy.jp/#top' in cur_url:
            top_page()
        elif 'http://game.granbluefantasy.jp/#authentication' in cur_url:
            authentication_page()
        elif 'loginbonus' in cur_url:
            clicker('.cjs-login')
        else:
            load_page(homepage, target, ignore_url=True)


def dispatcher(tasklist):
    """Takes a list/tuple of tasks and runs through them with suitable fallback responses"""

    tasklist = CFG['tasklist']
    dispatch_functions = {
        "main_loop": main_loop,
        "do_attack": do_attack
    }
    wait_for_page_load()

    for task in tasklist:
        args = list()
        kwargs = dict()

        if isinstance(task, (list, tuple)):
            # Check through the list/tuple of args for any kwargs, then separate them
            args = list(task[1:])
            task = task[0]
            counter = 0

            for arg in args:
                if isinstance(arg, dict):
                    # Unpack dicts and remove them from args
                    for item in arg:
                        kwargs[item] = arg[item]
                    del args[counter]
                else:
                    # Pass if not a dict
                    counter += 1

        response = dispatch_functions[task](*args, **kwargs)
        if response == 1001:
            log('{} has completed successfully'.format(task.__name__))
        elif response:
            log('{} has failed'.format(task.__name__))
            if args is not None:
                dispatcher((task, args))


if __name__ == '__main__':
    GBF = setup_driver_instance()
    load_page('http://game.granbluefantasy.jp/#authentication', ignore_url=True)
    set_viewport_size(GBF, 400, 600)
    sleep(1)
    # Need to make a function to automatically log in... Load #mypage > click top > check url >
    # log in | continue on with the script
    if GBF.current_url == 'http://game.granbluefantasy.jp/#authentication':
        authentication_page()
    try:
        input()
        loop_poker()
    except Exception as exp:
        alert_operator('Fatal exception has occured, bot terminating.\n{}'.format(exp))
        raise
