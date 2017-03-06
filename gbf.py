from datetime import date, datetime
from time import sleep
from random import randint, uniform
from selenium import webdriver
from selenium.common.exceptions import (TimeoutException,
                                        NoSuchElementException,
                                        StaleElementReferenceException,
                                        WebDriverException,
                                        UnexpectedAlertPresentException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pushbullet import InvalidKeyError, Pushbullet

LOG_FILE = "[%s] GBFDriver.log" % (date.today())
HOTKEYS = ["q", "w", "e", "r", "t", "y"]
USE_PB = False
API_KEY = {
    "PB": "",
}

PROFILE = ('C:/Users/kyoukaya/profile')
OPTIONS = webdriver.ChromeOptions()
OPTIONS.add_argument('user-data-dir=%s' % PROFILE)
GBF = webdriver.Chrome(chrome_options=OPTIONS)


def log(message):
    """Prints to console and outputs to log file"""
    with open(LOG_FILE, "a", encoding="utf-8", newline='') as fout:
        message = "[%s] %s" % (str(datetime.now())[0:-4], message)
        print(message)
        fout.write(message + "\n")


def alert_operator(message, pause=True):
    """Push alerts for CAPTCHAs, etc."""
    if USE_PB is True and message.__len__() > 0:
        try:
            pub = Pushbullet(API_KEY["PB"])
            push = pub.push_note("GBFdriver", message)
            log(push)
        except InvalidKeyError:
            log("Invalid PB API key!")
    print(message)
    if pause:
        input("Press enter to continue")


def set_viewport_size(driver, width, height):
    window_size = driver.execute_script("""
        return [window.outerWidth - window.innerWidth + arguments[0],
          window.outerHeight - window.innerHeight + arguments[1]];
          """, width, height)
    driver.set_window_size(*window_size)


def random_click(ele, var_x, var_y):
    clicked = False
    while not clicked:
        log("Element at: %d, %d" % (ele.location["x"], ele.location["y"]))
        log("Clicking %s with variance X: %d, Y: %d" % (ele, var_x, var_y))
        actions = ActionChains(GBF)
        actions.move_to_element(ele).move_by_offset(var_x, var_y).click_and_hold().perform()
        sleep(uniform(0.05, 0.15))
        actions.release().perform()
        clicked = True


def java_click(ele, var_x, var_y):
    """In the off case we might not want to use the default way of clicking things"""
    ele_loc = ele.location
    ele_loc_x = ele_loc["x"]
    ele_loc_y = ele_loc["y"]
    log("%d, %d" % (ele_loc_x, ele_loc_y))
    log("Clicking %s using javascript with variance X: %d, Y: %d" %
        (ele, var_x, var_y))
    script = "document.elementFromPoint(%s,%s).click();" % (
        ele_loc_x, ele_loc_y)
    GBF.execute_script(script)


def clicker(ele, delay=0.5, kind="random", variance=3):
    """Takes a CSS selector in the form of a CSS selector/xpath string or an element object
    and clicks on it.
    Additional arguments (delay, kind, variance)"""
    if isinstance(ele, str) and ele_check(ele):
        print(ele)
        if ele[0] == '/':
            log("Finding element by xpath")
            ele = GBF.find_element_by_xpath(ele)
        else:
            ele = GBF.find_element_by_css_selector(ele)
    elif isinstance(ele, str):
        log("Element does not exist: %s" % ele)
        return
    if delay > 0:
        delay = uniform(1.25 * delay, 0.75 * delay)
        log("Sleeping for %d seconds before clicking" % (delay))
        sleep(delay)
    var_x = randint(0 - variance, variance)
    var_y = randint(0 - variance, variance)
    try:
        # Handle potential errors that arise from non-existent elements
        if kind == "random":
            random_click(ele, var_x, var_y)
        elif kind == "java":
            java_click(ele, var_x, var_y)
        elif kind == "fallback":
            # Can't introduce click variance with native methods...
            ele.click()
        else:
            log("Invalid kind '%s' inputted!" % (kind))
    except (StaleElementReferenceException, NoSuchElementException):
        log("Element does not exist")
        return False
    except UnexpectedAlertPresentException as exp:
        log('%s\nAlert detected, dismissing' % exp)
        GBF.switch_to_alert().accept()
        clicker(ele, delay, kind, variance)


def ele_check(ele, wait=1):
    try:
        if ele[0] == '/':
            WebDriverWait(GBF, wait).until(
                EC.visibility_of_element_located((By.XPATH, ele))
            )
            return True
        else:
            WebDriverWait(GBF, wait).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ele))
            )
            return True
    except TimeoutException:
        return False
    except UnexpectedAlertPresentException as exp:
        log('%s\nAlert detected, dismissing' % exp)
        GBF.switch_to_alert().accept()
        return ele_check(ele)


def wait_until_css(css, maxwait=5):
    log("Waiting for %s for %d seconds" % (css, maxwait))
    waiting = True
    tries = 0
    while waiting:
        if ele_check(css):
            return True
        else:
            if maxwait > 0:
                tries += 1
            if tries > maxwait:
                log("Maximum tries reached")
                return False


def load_page(url, wait_for="", ignore_url=False):
    GBF.get(url)
    sleep(0.1)
    if GBF.current_url != url and not ignore_url:
        message = "Unexpected URL: %s" % (GBF.current_url)
        log(message)
        alert_operator(message)
        load_page(url, wait_for)
    if wait_for != "":
        wait_until_css(wait_for)


def skill_check():
    """Returns a list of lists with skill availability booleans"""
    available = []
    cards = GBF.find_elements_by_css_selector(".quick-panel.prt-ability-list")
    for counter in range(0, len(cards)):
        char_avail = []
        char = cards[counter].find_elements_by_css_selector(".lis-ability")
        for charcount in range(0, len(char)):
            if char[charcount].get_attribute("class") == \
                    "lis-ability btn-ability-available quick-button":
                char_avail.append(True)
            else:
                char_avail.append(False)
        available.append(char_avail)
    return available


def do_skill(character, skill, target=-1):
    available = skill_check()
    if not available[character][skill]:
        log("Character %s's skill %s is unavailable." % (character, skill))
    log("Using character %s's skill %s. Target %s" %
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
    if not ele_check(".quick-summon"):
        log("Couldn't find summons")
        return
    cards = GBF.find_elements_by_css_selector(".quick-summon")
    available = []
    for counter in range(0, 6):
        if cards[counter].get_attribute("class") == "quick-summon available":
            available.append(counter)
        else:
            continue
    log("Available summons: %s" % str(available))
    return available


def do_summon(num):
    """We should probably use a click instead since that's way faster"""
    if num not in summon_check():
        log("Summon %s unavailable!" % num)
        return
    log("Using summon number %s" % num)
    actions = ActionChains(GBF)
    actions.send_keys(5).perform()
    sleep(0.5)
    actions.send_keys(HOTKEYS[num]).perform()
    sleep(0.5)
    actions.send_keys(Keys.SPACE).perform()


def ougi_check():
    if ele_check(".btn-lock.lock0"):
        return True
    elif ele_check(".btn-lock.lock1"):
        return False


def set_ougi(ougi):
    while ougi != ougi_check():
        actions = ActionChains(GBF)
        actions.send_keys("c").perform()
        sleep(0.2)


def do_attack(auto=False, ougi=False):
    if not ele_check(".btn-attack-start.display-on"):
        log("Unable to attack!")
        return False
    if ougi != ougi_check():
        set_ougi(ougi)
    log("Attacking. Auto=%s, Ougi=%s" % (auto, ougi))
    clicker(".btn-attack-start.display-on", variance=6)
    if auto:
        if wait_until_css(".btn-auto"):
            clicker(".btn-auto")
    return True


def wait_until_url(url):
    counter = 0
    while counter < 40:
        if url in GBF.current_url:
            return
        sleep(0.25)
    log("Somehow we're at %s" % GBF.current_url)

"""def claim_rewards():
    if ele_check(".btn-usual-ok"):
        cancel_ok = GBF.find_elements_by_class_name("btn-usual-ok")[0]
        clicker(cancel_ok)
    sleep(2)
    wait_until_css("lis-raid")
    r_list = GBF.find_elements_by_class_name("lis-raid")
    for r in r_list:
        log('claiming reward - did not join raid')
        r.click()
    if ele_check(".btn-usual-ok"):
        cancel_ok = GBF.find_elements_by_class_name("btn-usual-ok")[0]
        clicker(cancel_ok)"""


def popup_check():
    # CAPTCHA identifier <div> class="prt-popup-header">Access Verification</div>
    waiting = True
    try:
        ele = GBF.find_element_by_css_selector(".prt-popup-header")
        if not ele.is_displayed():
            return
    except:
        return
    text = ele.text
    log("%s popup detected" % text)
    if text == "Not enough AP":
        log("Not enough AP, using 1/2 pot")
        clicker(".btn-use-full.index-1")
        if wait_until_css(".btn-usual-ok"):
            clicker(".btn-usual-ok")
            return
    if text == "Access Verification":
        alert_operator("CAPTCHA detected! Help!")
        return
    else:
        # if ele_check(".btn-usual-cancel"):
        actions = ActionChains(GBF)
        actions.send_keys("`").send_keys(Keys.SPACE).perform()
        log("Popup dismissed")

"""def check_bp():
    wait_until_css("prt-user-bp-value")
    bp = GBF.find_elements_by_class_name("prt-user-bp-value")[0]
    num = bp.get_attribute("title")
    return (int)(num)"""


def check_health():
    log('Checking health')
    characters = GBF.find_elements_by_class_name('prt-gauge-hp-inner')
    thp = []
    for i in range(4):
        percent = characters[i].get_attribute('style').split()[1]
        thp.append(int(percent[0:-2]))
    return thp


def wait_for_skill_queue():
    log("Waiting for skills to finish casting")
    while not ele_check(".prt-ability-rail-overlayer.hide"):
        if GBF.current_url not in "http://game.granbluefantasy.jp/#raid_multi/":
            log("We seem to have exited the raid page while waiting for skills")
            return False
    return True


def wait_for_ready():
    waiting = True
    log("Waiting for ready...")
    while waiting:
        if wait_until_css(".btn-attack-start.display-on"):
            log("Ready!")
            return True
        else:
            if "http://game.granbluefantasy.jp/#raid_multi/" not in GBF.current_url:
                log("We seem to have exited the raid page while waiting for ready")
                return False
            continue


def results_page(homepage, target, rounds):
    log("In results page")
    wait_until_css(".btn-usual-ok", maxwait=1)
    load_page(homepage, target, ignore_url=True)
    rounds += 1
    return rounds


def raid_battle():
    if not wait_for_ready():
        return
    log("In battle page")
    do_summon(5)
    if not wait_for_skill_queue():
        return
    if not do_attack():
        return
    sleep(1)
    GBF.refresh()


def create_coop_lobby():
    target = ".btn-create-room.location-href"
    target2 = ".btn-entry-room"
    if wait_until_css(target, maxwait=2):
        clicker(target)
    if wait_until_css(target2, maxwait=2):
        clicker(target2)


def coop_lobby():
    log("In coop lobby page")
    target = ".btn-repeat-last"
    target2 = ".btn-quest-start.multi.se-quest-start"
    counter = 0
    while True:
        popup_check()
        c_url = GBF.current_url
        if c_url == "http://game.granbluefantasy.jp/#coopraid" or \
           c_url == "http://game.granbluefantasy.jp/#coopraid/room/entry":
            create_coop_lobby()
        elif "http://game.granbluefantasy.jp/#coopraid/room/" not in c_url:
            return
        if ele_check(".btn-make-ready-large.not-ready", wait=0.1):
            # We'll try to handle party and summon selection someday
            alert_operator("Please choose a summon")
        if ele_check(target, wait=0.1):
            ele = GBF.find_element(By.CSS_SELECTOR, target)
            clicker(ele)
        if ele_check(target2, wait=0.1):
            ele = GBF.find_element(By.CSS_SELECTOR, target2)
            clicker(ele)
            sleep(0.5)
            popup_check()
            sleep(0.5)
            return
        if counter < 8:
            # Counter to refresh the room after awhile since it likes to stop
            # updating for no reason
            counter += 1
            log("Counter: %d" % counter)
        else:
            actions = ActionChains(GBF)
            actions.send_keys(Keys.F5).perform()
            sleep(.5)
            return


def top_page():
    clicker(".btn-login.switch-position")


def authentication_page():
    clicker('//*[@id="gree-login"]')


def main_loop():
    homepage = "http://game.granbluefantasy.jp/#coopraid"
    target = ".prt-head-current"
    rounds = 0
    while True:
        sleep(2)
        cur_url = GBF.current_url
        if "http://game.granbluefantasy.jp/#coopraid" in cur_url:
            coop_lobby()
            popup_check()  # Checks for CAPTCHAs and weird stuff after we hit the start button
        elif "http://game.granbluefantasy.jp/#raid_multi/" in cur_url:
            raid_battle()
        elif "http://game.granbluefantasy.jp/#result_multi/" in cur_url:
            rounds = results_page(homepage, target, rounds)
        elif "http://game.granbluefantasy.jp/#top" in cur_url:
            top_page()
        elif "http://game.granbluefantasy.jp/#authentication" in cur_url:
            authentication_page()
        else:
            load_page(homepage, target, ignore_url=True)
            sleep(.5)


def main():
    log("Profile path: %s" % PROFILE)
    set_viewport_size(GBF, 400, 600)
    main_loop()

if __name__ == "__main__":
    try:
        main()
    except WebDriverException:
        log("Chrome exited")
        quit()
    except Exception as exp:
        alert_operator("Fatal exception has occured, bot terminating\n%s" % exp)
