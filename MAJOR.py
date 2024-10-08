import sys
import time
import random
import requests
import urllib.parse
import json
import os
import asyncio
import aiohttp
from colorama import init, Fore, Style
from collections import defaultdict
import re

# Initialize colorama
init(autoreset=True)

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def art():
    print(Fore.GREEN + Style.BRIGHT + r"""
  _                
 | | | |             | |               
 | |_| |  __ _   ___ | | __  ___  _ __ 
 |  _  | / _` | / __|| |/ / / _ \| '__|
 | | | || (_| || (__ |   < |  __/| |   
 \_| |_/ \__,_| \___||_|\_\ \___||_| 
    """ + Style.RESET_ALL)

    print(Fore.CYAN + "Major Script Edited by @Dhiraj_9619  DHEERAJ" + Style.RESET_ALL)
    print(Fore.MAGENTA + "==============================================" + Style.RESET_ALL)

def read_query_ids(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file]

def decode_query_id(query_id):
    params = urllib.parse.parse_qs(query_id)
    user_info_encoded = params.get('user', [''])[0]
    user_info_decoded = urllib.parse.unquote(user_info_encoded)
    user_info_json = json.loads(user_info_decoded)
    user_id = user_info_json.get('id')
    username = user_info_json.get('username')
    return user_id, username

def load_proxies():
    with open('proxy.txt', 'r') as proxy_file:
        return json.load(proxy_file)

def load_account_proxies():
    if os.path.exists('account_proxies.json'):
        with open('account_proxies.json', 'r') as file:
            return json.load(file)
    return {}

def save_account_proxies(account_proxies):
    with open('account_proxies.json', 'w') as file:
        json.dump(account_proxies, file)

def check_and_correct_user_agents_format():
    user_agents_file = 'user_agents.json'
    
    if not os.path.exists(user_agents_file):
        with open(user_agents_file, 'w') as file:
            json.dump([], file)
            log_message(f"Created {user_agents_file}. You can add your User-Agents manually.", Fore.YELLOW)
        return
    
    try:
        with open(user_agents_file, 'r') as file:
            user_agents = json.load(file)

        if not isinstance(user_agents, list) or any(not isinstance(agent, str) for agent in user_agents):
            log_message(f"Incorrect format in {user_agents_file}. Attempting to correct format...", Fore.RED)
            user_agents = [agent for agent in user_agents if isinstance(agent, str)]
            with open(user_agents_file, 'w') as file:
                json.dump(user_agents, file)
                log_message("Format corrected.", Fore.GREEN)
    
    except json.JSONDecodeError:
        log_message(f"Invalid JSON format in {user_agents_file}. Attempting to correct format...", Fore.RED)
        with open(user_agents_file, 'w') as file:
            json.dump([], file)
            log_message("Format corrected.", Fore.GREEN)

def load_user_agents():
    user_agents_file = 'user_agents.json'
    check_and_correct_user_agents_format()
    
    with open(user_agents_file, 'r') as file:
        user_agents = json.load(file)

    return user_agents

def select_random_proxy(proxies, proxy_usage):
    available_proxies = [proxy for proxy in proxies if proxy_usage[proxy['http']] < 4]
    if available_proxies:
        return random.choice(available_proxies)
    return None

def is_proxy_working(proxy):
    test_url = "http://example.com"
    try:
        response = requests.get(test_url, proxies={'http': proxy['http'], 'https': proxy['http']}, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def bind_working_proxy(proxies_list, account_proxies, query_id, proxy_usage):
    for proxy in proxies_list:
        if is_proxy_working(proxy) and proxy_usage[proxy['http']] < 4:
            account_proxies[query_id] = proxy
            proxy_usage[proxy['http']] += 1
            return proxy
    return None

def login(query_id, proxies=None, user_agent=None):
    url_login = "https://major.glados.app/api/auth/tg/"
    payload = {"init_data": query_id}
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": user_agent,
        "Referer": "https://major.glados.app/"
    }

    for attempt in range(5):  # Retry 5 times
        try:
            response = requests.post(url_login, headers=headers, data=json.dumps(payload), proxies=proxies)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ProxyError as e:
            log_retry(f"Login attempt {attempt + 1} failed for query_id {query_id}: Proxy error - {str(e)}")
            time.sleep(1)
        except requests.exceptions.RequestException as e:
            log_retry(f"Login attempt {attempt + 1} failed for query_id {query_id}: Request error - {str(e)}")
            time.sleep(1)

    return None

def get_access_token(data):
    return data.get('access_token')

def check_user_details(user_id, access_token, proxies=None):
    url_user_details = f"https://major.glados.app/api/users/{user_id}/"
    headers_user_details = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://major.glados.app/"
    }
    
    try:
        response = requests.get(url_user_details, headers=headers_user_details, proxies=proxies)
        response.raise_for_status()
        
        data = response.json()
        rating = data.get("rating", "No rating found")
        return rating
    
    except requests.exceptions.HTTPError as http_err:
        log_error(f"HTTP error occurred: {http_err} for user {user_id}")
    except Exception as err:
        log_error(f"Other error occurred: {err} for user {user_id}")

    return None

def perform_daily_spin(access_token, proxies=None, user_agent=None, fast_game=False):
    url_spin = "https://major.glados.app/api/roulette/"
    headers_spin = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": user_agent,
        "Referer": "https://major.glados.app/"
    }
    response = requests.post(url_spin, headers=headers_spin, proxies=proxies)

    if response.status_code == 201:
        spin_data = response.json()
        rating_award = spin_data.get("rating_award")
        duration = 2 if fast_game else 10
        single_line_progress_bar(duration, Fore.GREEN + f"Daily Spin Reward: {rating_award} [✓]" + Style.RESET_ALL)  # Adjusted duration and message
    elif response.status_code == 400:
        log_message("Daily Spin Already Claimed [×]", Fore.RED)
    else:
        log_error(f"Failed to claim Daily Spin, status code: {response.status_code}")

    random_delay()
    return response

def perform_daily(access_token, proxies=None, user_agent=None):
    url_daily = "https://major.glados.app/api/user-visits/visit/"
    headers_daily = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": user_agent,
        "Referer": "https://major.glados.app/"
    }
    response = requests.post(url_daily, headers=headers_daily, proxies=proxies)
    return response

def daily_hold(access_token, proxies=None, user_agent=None, fast_game=False):
    coins = random.randint(900, 950)
    payload = {"coins": coins} 
    url_hold = "https://major.glados.app/api/bonuses/coins/"
    headers_hold = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": user_agent,
        "Referer": "https://major.glados.app/"
    }
    response = requests.post(url_hold, data=json.dumps(payload), headers=headers_hold, proxies=proxies)
    duration = 2 if fast_game else 60
    if response.status_code == 201:
        single_line_progress_bar(duration, Fore.GREEN + "Hold Bonus Claim successfully [✓]" + Style.RESET_ALL)
    elif response.status_code == 400:
        log_message("Daily Hold Balance Already Claimed [×]", Fore.RED)

    random_delay()
    return response

def daily_swipe(access_token, proxies=None, user_agent=None, fast_game=False):
    coins = random.randint(1000, 1300)
    payload = {"coins": coins} 
    url_swipe = "https://major.glados.app/api/swipe_coin/"
    headers_swipe = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": user_agent,
        "Referer": "https://major.glados.app/"
    }
    response = requests.post(url_swipe, data=json.dumps(payload), headers=headers_swipe, proxies=proxies)
    duration = 2 if fast_game else 60
    if response.status_code == 201:
        single_line_progress_bar(duration, Fore.GREEN + "Swipe Bonus Claim successfully [✓]" + Style.RESET_ALL)
    elif response.status_code == 400:
        log_message("Daily Swipe Balance Already Claimed [×]", Fore.RED)

    random_delay()
    return response

def task_answer():
    url = 'https://raw.githubusercontent.com/Dhiraj9619/UNKNOWN2/refs/heads/main/task_answers.json'
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for HTTP errors
        response_answer = response.json()
        return response_answer['youtube']
    except requests.exceptions.HTTPError as http_err:
        log_error(f"[ HTTP Error Occurred While Loading Task Answer: {str(http_err)} ]")
    except Exception as e:
        log_error(f"[ An Error Occurred While Loading Task Answer: {str(e)} ]")
    return None

async def fetch_tasks(token, is_daily, proxies=None, user_agent=None):
    url = f'https://major.bot/api/tasks/?is_daily={is_daily}'
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": user_agent,
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.get(url=url, headers=headers, proxy=proxies.get('http') if proxies else None) as response:
                if response.status in [500, 520]:
                    log_error("[ Server Major Down ]")
                    return None
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientResponseError as e:
        log_error(f"[ An HTTP Error Occurred While Fetching Tasks: {str(e.message)} ]")
        return None
    except (Exception, aiohttp.ContentTypeError) as e:
        log_error(f"[ An Unexpected Error Occurred While Fetching Tasks: {str(e)} ]")

async def complete_task(token, task_id, task_title, task_award, proxies=None, user_agent=None):
    url = 'https://major.bot/api/tasks/'
    answers = task_answer()  # Fetch answers from the remote URL
    data = json.dumps({'task_id': task_id, 'payload': {'code': answers.get(task_title)}})
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": user_agent,
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.post(url=url, headers=headers, data=data, proxy=proxies.get('http') if proxies else None) as response:
                if response.status == 400:
                    return
                elif response.status in [500, 520]:
                    log_error("[ Server Major Down ]")
                response.raise_for_status()
                complete_task = await response.json()
                if complete_task['is_completed']:
                    log_message(f"[ {task_title}: Got {task_award} [✓] ]", Fore.GREEN)
    except aiohttp.ClientResponseError as e:
        log_error(f"[ An HTTP Error Occurred While Completing Tasks: {str(e.message)} ]")
    except (Exception, aiohttp.ContentTypeError) as e:
        log_error(f"[ An Unexpected Error Occurred While Completing Tasks: {str(e)} ]")

def do_task(token, task_id, task_name, proxies=None, user_agent=None):
    url = "https://major.bot/api/tasks/"
    payload = {'task_id': task_id}
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": user_agent,
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, proxies=proxies)
        random_delay()
        if response.status_code == 200:
            result = response.json()
            if result.get('is_completed', False):
                log_message(f"{task_name} already Claimed [×]", Fore.YELLOW)
                return True
            else:
                log_message(f"{task_name} Claimed [✓]", Fore.GREEN)
                return True
        elif response.status_code == 201:
            if task_name == "Follow Major in Telegram":
                log_message("Task Major Tg Follow Claim Success [✓]", Fore.GREEN)
            else: 
                log_message(f"{task_name} claimed Success [✓]", Fore.GREEN)
            return True
        elif response.status_code == 400 and 'detail' in response.json() and response.json()['detail'] == "Task is already completed":
            log_message(f"{task_name} already claimed [×]", Fore.RED)
            return True
        else:
            log_error(f"Failed to complete task '{task_name}', status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        log_error(f"Error occurred while completing task '{task_name}': {e}")
        return False

def durov(access_token, c_1=None, c_2=None, c_3=None, c_4=None, proxies=None, user_agent=None):
    url_durov = "https://major.bot/api/durov/"
    headers_durov = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": user_agent,
        "Referer": "https://major.glados.app/"
    }
    
    payload = {"choice_1": c_1, "choice_2": c_2, "choice_3": c_3, "choice_4": c_4}
    response = requests.post(url_durov, data=json.dumps(payload), headers=headers_durov, proxies=proxies)
    if response.status_code == 201:
        log_message("Durov Task Completed Successfully [✓]", Fore.GREEN)
    else:
        log_message("Durov Task already completed! [×]", Fore.RED)
    return response

def single_line_progress_bar(duration, message):
    bar_length = 30
    for percent in range(101):
        filled_length = int(bar_length * percent // 100)
        bar = '█' * filled_length + '▒' * (bar_length - filled_length)
        print(f"\r{Fore.GREEN}[{bar}] {percent}%", end="")
        time.sleep(duration / 100)
    print(f"\r{message}" + " " * (bar_length + 10), end='\r')  # Clear line with message

def countdown_timer(seconds):
    while seconds > 0:
        mins, secs = divmod(seconds, 60)
        hours, mins = divmod(mins, 60)
        try:
            print(f"{Fore.CYAN + Style.BRIGHT}Wait {hours:02}:{mins:02}:{secs:02} ⏳", end='\r')
            time.sleep(1)
            seconds -= 1
        except KeyboardInterrupt:
            graceful_exit()
    print(" " * 50, end='\r')

def random_delay():
    delay = random.randint(1, 2)
    countdown_timer(delay)

def graceful_exit():
    print("\n" + Fore.YELLOW + "Exiting gracefully... Please wait.")
    time.sleep(2)
    print("Goodbye!" + Style.RESET_ALL)
    sys.exit()

def log_message(message, color=Fore.WHITE):
    print(f"{color + Style.BRIGHT}{message}{Style.RESET_ALL}")

def log_error(error_message):
    with open('.error_log.txt', 'a') as file:
        file.write(error_message + '\n')

def log_retry(retry_message):
    with open('.retry_log.txt', 'a') as file:
        file.write(retry_message + '\n')

def clear_error_log():
    open('.error_log.txt', 'w').close()

def clear_retry_log():
    open('.retry_log.txt', 'w').close()

def get_yes_no_input(prompt):
    while True:
        try:
            choice = input(prompt).strip().lower()
            if choice in ['y', 'n']:
                return choice == 'y'
            else:
                print("Please enter 'y' or 'n'.")
        except KeyboardInterrupt:
            graceful_exit()

def get_starting_account_number(total_accounts):
    while True:
        try:
            start_number = int(input(f"Enter the starting account number (1 to {total_accounts}): ").strip())
            if 1 <= start_number <= total_accounts:
                return start_number - 1
            else:
                print(f"Please enter a number between 1 and {total_accounts}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            graceful_exit()

def extract_browser_info(user_agent):
    match = re.search(r'(Chrome/\d+\.\d+\.\d+|Firefox/\d+\.\d+|Safari/\d+\.\d+)', user_agent)
    return match.group(0) if match else "Unknown Browser"

def process_account(query_id, proxies_list, auto_task, auto_play_game, durov_enabled, durov_choices, account_proxies, total_balance, user_agents, account_index, proxy_usage, fast_game, other_tasks_enabled, completed_tasks):
    user_id, username = decode_query_id(query_id)
    log_message(f"-------- Account no {account_index + 1} ---------", Fore.LIGHTBLUE_EX)
    log_message(f"Username: {username}", Fore.WHITE)
    
    user_agent = user_agents[-1] if user_agents else "Mozilla/5.0"
    browser_info = extract_browser_info(user_agent)
    log_message(f"Browser: {browser_info}", Fore.MAGENTA)

    if user_id is None:
        log_error(f"Failed to decode user ID for account {username}. Skipping...")
        return

    proxy = account_proxies.get(query_id)
    if proxies_list:
        if not proxy or proxy_usage[proxy['http']] >= 4:
            proxy = select_random_proxy(proxies_list, proxy_usage)
            if proxy:
                account_proxies[query_id] = proxy
                proxy_usage[proxy['http']] += 1

        proxy = {
            'http': proxy['http'],
            'https': proxy['http']
        }
    else:
        proxy = None

    login_data = login(query_id, proxies=proxy, user_agent=user_agent)

    if not login_data:
        log_error(f"Login failed after retries for {username}.")
        return

    if proxy:
        account_proxies[query_id] = proxy

    access_token = get_access_token(login_data)
    initial_balance = check_user_details(user_id, access_token, proxies=proxy)

    if initial_balance is not None:
        log_message(f"Balance: {initial_balance}", Fore.GREEN)
        total_balance.append(initial_balance)

    if access_token:
        response_daily = perform_daily(access_token, proxies=proxy, user_agent=user_agent)
        if response_daily.status_code == 200:
            daily_data = response_daily.json()
            if daily_data.get('is_increased'):
                log_message("Daily Bonus Claimed Successfully [✓]", Fore.GREEN)
            else:
                log_message("Daily Bonus Already Claimed [×]", Fore.RED)
            
            time.sleep(random.randint(2, 3))

        if durov_enabled:
            durov(access_token, *durov_choices, proxies=proxy, user_agent=user_agent)

        if auto_play_game:
            response_hold = daily_hold(access_token, proxies=proxy, user_agent=user_agent, fast_game=fast_game)
            response_swipe = daily_swipe(access_token, proxies=proxy, user_agent=user_agent, fast_game=fast_game)
            response_spin = perform_daily_spin(access_token, proxies=proxy, user_agent=user_agent, fast_game=fast_game)

        if auto_task:
            tasks = asyncio.run(fetch_tasks(access_token, is_daily=True, proxies=proxy, user_agent=user_agent))
            specific_tasks = {
                29: "Follow Major in Telegram",
                16: "Share in Telegram Stories",
                5: "TON Channels"
            }
            if tasks:
                for task in tasks:
                    task_id = task.get('id')
                    task_name = specific_tasks.get(task_id, f'Task {task_id}')
                    if task_id in specific_tasks:
                        retries = 0
                        while retries < 3:
                            task_completed = do_task(access_token, task_id, task_name, proxies=proxy, user_agent=user_agent)
                            if task_completed:
                                break
                            if task_name == "Follow Major in Telegram":
                                log_message("Please join Major TG first", Fore.RED)
                                time.sleep(1)
                                retries += 1
                                log_error(f"Retrying... ({retries}/3) for '{task_name}'")
                                time.sleep(0.5)
                                clear_terminal()
                                if retries == 3:
                                    log_error(f"Failed to complete '{task_name}' after 3 attempts.")

        if other_tasks_enabled:
            excluded_tasks = {
                "Extra Stars Purchase",
                "Stars Purchase",
                "Promote TON blockchain",
                "Boost Major channel",
                "Boost Roxman channel",
                "Follow CATS Channel'",
                "Follow Roxman in Telegram",
                "Binance x TON",
                "One-time Stars Purchase",
                "Connect TON wallet",
                "Play W-Coin",
                "Duck Master",
                "Status Purchase",
                "X Empire",
                "Follow Fintopio in Telegram",
                "Get Fintopio Today",
                "Coub.com",
                "Invite more Friends"
            }

            for type in ['true', 'false']:
                tasks = asyncio.run(fetch_tasks(access_token, is_daily=type, proxies=proxy, user_agent=user_agent))
                if tasks is not None:
                    for task in tasks:
                        if task['title'] in excluded_tasks:
                            log_message(f"Skipping task '{task['title']}'", Fore.YELLOW)
                            continue

                        if not task['is_completed'] and task['id'] not in completed_tasks:
                            retries = 0
                            while retries < 3:
                                task_result = asyncio.run(complete_task(access_token, task_id=task['id'], task_title=task['title'], task_award=task['award'], proxies=proxy, user_agent=user_agent))
                                if task_result:
                                    completed_tasks.add(task['id'])
                                    break
                                retries += 1
                                log_error(f"Retrying... ({retries}/3) for '{task['title']}'")
                                time.sleep(1)

    final_balance = check_user_details(user_id, access_token, proxies=proxy)
    log_message(f"Final balance: {final_balance}", Fore.GREEN)
    if final_balance is not None:
        total_balance.append(final_balance)
    log_message("")

def main():
    try:
        check_and_correct_user_agents_format()

        use_proxy = get_yes_no_input("Do you want to use a proxy? (y/n): ")

        if use_proxy:
            proxies_list = load_proxies()
            account_proxies = load_account_proxies()
            proxy_usage = defaultdict(int)
            for proxy in account_proxies.values():
                proxy_usage[proxy['http']] += 1
        else:
            proxies_list = None
            account_proxies = {}
            proxy_usage = defaultdict(int)

        user_agents = load_user_agents()

        query_ids = read_query_ids('data.txt')
        
        clear_terminal()
        art()

        auto_task = get_yes_no_input("Enable auto daily task? (y/n): ")
        auto_play_game = get_yes_no_input("Enable auto game play? (y/n): ")
        fast_game = False

        if auto_play_game:
            fast_game = get_yes_no_input("Enable Fast game play? (y/n): ")

        play_durov = get_yes_no_input("Do you play Durov? (y/n): ")

        other_tasks_enabled = get_yes_no_input("Enable other tasks? (y/n): ")

        starting_account = get_starting_account_number(len(query_ids))

        durov_choices = []
        if play_durov:
            while True:
                try:
                    durov_input = input("Input Durov choices (e.g: 4, 6, 9, 10): ").strip()
                    choices = durov_input.split(',')
                    if len(choices) == 4:
                        durov_choices = [choice.strip() for choice in choices]
                        break
                    else:
                        log_message("Invalid input. Please provide exactly 4 comma-separated choices.", Fore.RED)
                except KeyboardInterrupt:
                    graceful_exit()

        total_balance = []
        completed_tasks = set()

        for index, query_id in enumerate(query_ids[starting_account:], start=starting_account):
            process_account(query_id, proxies_list, auto_task, auto_play_game, play_durov, durov_choices, account_proxies, total_balance, user_agents, index, proxy_usage, fast_game, other_tasks_enabled, completed_tasks)

        if use_proxy:
            save_account_proxies(account_proxies)

        log_message(f"Total Balance of all accounts: {sum(total_balance)}", Fore.YELLOW)
        log_message("All accounts processed. Starting random timer for the next cycle.", Fore.CYAN)

        clear_error_log()  # Clear the error log at the end
        clear_retry_log()  # Clear the retry log at the end

        random_timer = random.randint(8 * 60 * 60, 9 * 60 * 60)
        countdown_timer(random_timer)
        clear_terminal()
        art()

    except KeyboardInterrupt:
        graceful_exit()

if __name__ == "__main__":
    main()
