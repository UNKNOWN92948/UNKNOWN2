import sys
import asyncio

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import time
import random
import requests
import urllib.parse
import json
import os
import aiohttp
from colorama import init, Fore, Style
from collections import defaultdict
import re
from fake_useragent import UserAgent

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

def generate_user_agents(query_ids):
    ua = UserAgent()
    user_agents = {decode_query_id(query_id)[1]: ua.random for query_id in query_ids}
    with open('user_agents.json', 'w') as file:
        json.dump(user_agents, file)
    return user_agents

def load_user_agents(query_ids):
    if not os.path.exists('user_agents.json'):
        return generate_user_agents(query_ids)

    try:
        with open('user_agents.json', 'r') as file:
            user_agents = json.load(file)

        if not isinstance(user_agents, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in user_agents.items()):
            raise ValueError("Invalid format")

        return user_agents
    except (json.JSONDecodeError, ValueError):
        return generate_user_agents(query_ids)

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

def login(query_id, proxies=None, user_agent=None):
    url_login = "https://major.glados.app/api/auth/tg/"
    payload = {"init_data": query_id}
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": user_agent,
        "Referer": "https://major.glados.app/"
    }

    while True:
        try:
            response = requests.post(url_login, headers=headers, data=json.dumps(payload), proxies=proxies)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            log_retry(f"Login failed for query_id {query_id}: Network error - {str(e)}. Retrying...")
            time.sleep(5)

def get_access_token(data):
    return data.get('access_token')

def check_user_details(user_id, access_token, proxies=None):
    url_user_details = f"https://major.glados.app/api/users/{user_id}/"
    headers_user_details = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://major.glados.app/"
    }
    
    while True:
        try:
            response = requests.get(url_user_details, headers=headers_user_details, proxies=proxies)
            response.raise_for_status()
            
            data = response.json()
            rating = data.get("rating", "No rating found")
            return rating
        except requests.exceptions.RequestException as e:
            log_error(f"Network error occurred while fetching user details for user {user_id}: {str(e)}. Retrying...")
            time.sleep(5)

def perform_daily_spin(access_token, proxies=None, user_agent=None):
    url_spin = "https://major.glados.app/api/roulette/"
    headers_spin = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": user_agent,
        "Referer": "https://major.glados.app/"
    }

    while True:
        try:
            response = requests.post(url_spin, headers=headers_spin, proxies=proxies)
            if response.status_code == 400:
                log_message("Daily Spin Already Claimed [×]", Fore.RED)
                return response

            single_line_progress_bar(10, "Completing Spin...")

            if response.status_code == 201:
                log_message("Daily Spin Reward claimed successfully [✓]", Fore.GREEN)
            else:
                log_error(f"Failed to claim Daily Spin, status code: {response.status_code}")

            random_delay()
            return response
        except requests.exceptions.RequestException as e:
            log_error(f"Network error occurred while performing daily spin: {str(e)}. Retrying...")
            time.sleep(5)

def perform_daily(access_token, proxies=None, user_agent=None):
    url_daily = "https://major.glados.app/api/user-visits/visit/"
    headers_daily = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": user_agent,
        "Referer": "https://major.glados.app/"
    }
    
    while True:
        try:
            response = requests.post(url_daily, headers=headers_daily, proxies=proxies)
            return response
        except requests.exceptions.RequestException as e:
            log_error(f"Network error occurred while performing daily visit: {str(e)}. Retrying...")
            time.sleep(5)

async def coins(token: str, reward_coins: int, proxies=None, user_agent=None):
    url = 'https://major.bot/api/bonuses/coins/'
    data = json.dumps({'coins': reward_coins})
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": user_agent,
        "Content-Length": str(len(data)),
        "Origin": "https://major.bot"
    }
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            async with session.post(url=url, headers=headers, data=data, proxy=proxies.get('http') if proxies else None) as response:
                if response.status == 400:
                    log_message("Daily Hold Balance Already Claimed [×]", Fore.RED)
                elif response.status in [500, 520]:
                    log_message("Server Major Down", Fore.YELLOW)
                response.raise_for_status()
                coins = await response.json()
                if coins['success']:
                    log_message(f"Hold Bonus Claim: {reward_coins} [✓]", Fore.GREEN)
    except aiohttp.ClientResponseError:
        pass  # Suppress HTTP error messages for hold coins
    except (Exception, aiohttp.ContentTypeError) as e:
        log_message(f"An Unexpected Error Occurred While Playing Hold Coins: {str(e)}", Fore.RED)

async def daily_hold(token: str, proxies=None, user_agent=None):
    reward_coins = 915  # Fixed coin amount
    single_line_progress_bar(60, "Completing Hold...")  # Progress bar before the actual claim
    await coins(token=token, reward_coins=reward_coins, proxies=proxies, user_agent=user_agent)

async def daily_swipe(access_token, proxies=None, user_agent=None):
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

    while True:
        try:
            response = requests.post(url_swipe, data=json.dumps(payload), headers=headers_swipe, proxies=proxies)
            if response.status_code == 400:
                log_message("Daily Swipe Balance Already Claimed [×]", Fore.RED)
                return response
            
            single_line_progress_bar(60, "Completing Swipe...")  # Progress bar before the actual claim

            if response.status_code == 201:
                single_line_progress_bar(2, Fore.GREEN + "Swipe Bonus claimed successfully [✓]" + Style.RESET_ALL)

            random_delay()
            return response
        except requests.exceptions.RequestException as e:
            log_error(f"Network error occurred while performing daily swipe: {str(e)}. Retrying...")
            time.sleep(5)

def task_answer():
    url = 'https://raw.githubusercontent.com/UNKNOWN92948/UNKNOWN2/refs/heads/main/task_answers.json'
    while True:
        try:
            response = requests.get(url)
            response.raise_for_status()
            response_answer = response.json()
            return response_answer['youtube']
        except requests.exceptions.RequestException as e:
            log_error(f"Network error occurred while loading task answers: {str(e)}. Retrying...")
            time.sleep(5)

async def fetch_tasks(token, is_daily, proxies=None, user_agent=None):
    url = f'https://major.bot/api/tasks/?is_daily={is_daily}'
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": user_agent,
    }
    while True:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                async with session.get(url=url, headers=headers, proxy=proxies.get('http') if proxies else None) as response:
                    if response.status in [500, 520]:
                        log_error("[ Server Major Down ]")
                        return None
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientResponseError as e:
            log_error(f"[ HTTP Error Occurred While Fetching Tasks: {str(e.message)} ]. Retrying...")
            await asyncio.sleep(5)
        except (Exception, aiohttp.ContentTypeError) as e:
            log_error(f"[ An Unexpected Error Occurred While Fetching Tasks: {str(e)} ]. Retrying...")
            await asyncio.sleep(5)

async def complete_task(token, task_id, task_title, task_award, proxies=None, user_agent=None):
    url = 'https://major.bot/api/tasks/'
    answers = task_answer()
    data = json.dumps({'task_id': task_id, 'payload': {'code': answers.get(task_title)}})
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": user_agent,
    }
    while True:
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
                    return
        except aiohttp.ClientResponseError as e:
            log_error(f"[ An HTTP Error Occurred While Completing Tasks: {str(e.message)} ]. Retrying...")
            await asyncio.sleep(5)
        except (Exception, aiohttp.ContentTypeError) as e:
            log_error(f"[ An Unexpected Error Occurred While Completing Tasks: {str(e)} ]. Retrying...")
            await asyncio.sleep(5)

def do_task(token, task_id, task_name, proxies=None, user_agent=None):
    url = "https://major.bot/api/tasks/"
    payload = {'task_id': task_id}
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": user_agent,
    }
    
    while True:
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
            log_error(f"Network error occurred while completing task '{task_name}': {str(e)}. Retrying...")
            time.sleep(5)

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
    while True:
        try:
            response = requests.post(url_durov, data=json.dumps(payload), headers=headers_durov, proxies=proxies)
            if response.status_code == 201:
                log_message("Durov Task Completed Successfully [✓]", Fore.GREEN)
            else:
                log_message("Durov Task already completed! [×]", Fore.RED)
            return response
        except requests.exceptions.RequestException as e:
            log_error(f"Network error occurred while completing Durov task: {str(e)}. Retrying...")
            time.sleep(5)

def single_line_progress_bar(duration, message):
    bar_length = 30
    for percent in range(101):
        filled_length = int(bar_length * percent // 100)
        bar = '█' * filled_length + '▒' * (bar_length - filled_length)
        print(f"\r{Fore.GREEN}[{bar}] {percent}%", end="")
        time.sleep(duration / 100)
    print(f"\r{message}" + " " * (bar_length + 10), end='\r')

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

def get_ending_account_number(start_number, total_accounts):
    while True:
        try:
            end_number = int(input(f"Enter the ending account number ({start_number + 1} to {total_accounts}): ").strip())
            if start_number < end_number <= total_accounts:
                return end_number
            else:
                print(f"Please enter a number between {start_number + 1} and {total_accounts}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            graceful_exit()

def extract_browser_info(user_agent):
    match = re.search(r'(Chrome/\d+\.\d+\.\d+|Firefox/\d+\.\d+|Safari/\d+\.\d+)', user_agent)
    return match.group(0) if match else "Unknown Browser"

def process_account(query_id, proxies_list, auto_task, auto_play_game, durov_enabled, durov_choices, account_proxies, total_balance, user_agents, account_index, proxy_usage, other_tasks_enabled, completed_tasks):
    user_id, username = decode_query_id(query_id)
    log_message(f"-------- Account no {account_index + 1} ---------", Fore.LIGHTBLUE_EX)
    log_message(f"Username: {username}", Fore.WHITE)
    
    user_agent = user_agents.get(username, "Mozilla/5.0")
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
        if response_daily and response_daily.status_code == 200:
            daily_data = response_daily.json()
            if daily_data.get('is_increased'):
                log_message("Daily Bonus Claimed Successfully [✓]", Fore.GREEN)
            else:
                log_message("Daily Bonus Already Claimed [×]", Fore.RED)
            
            time.sleep(random.randint(2, 3))

        if durov_enabled:
            durov(access_token, *durov_choices, proxies=proxy, user_agent=user_agent)

        if auto_play_game:
            # Execute daily_hold and wait for it to finish
            asyncio.run(daily_hold(token=access_token, proxies=proxy, user_agent=user_agent))
            # Execute daily_swipe and check if it's already claimed
            swipe_response = asyncio.run(daily_swipe(access_token, proxies=proxy, user_agent=user_agent))
            if swipe_response.status_code != 400:
                single_line_progress_bar(60, "Completing Swipe...")  # Only show if not already claimed
            # Finally, perform the daily spin
            perform_daily_spin(access_token, proxies=proxy, user_agent=user_agent)

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
                                if retries == 3:
                                    log_error(f"Failed to complete '{task_name}' after 3 attempts.")

        if other_tasks_enabled:
            excluded_tasks = {
                "Extra Stars Purchase",
                "Stars Purchase",
                "Promote TON blockchain",
                "Boost Major channel",
                "Boost Roxman channel",
                "Follow CATS Channel",
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
                        task_title = task['title'].rstrip('#')
                        if task_title in excluded_tasks:
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

    # Add a random wait time of 3-5 seconds after processing each account with countdown
    delay = random.randint(3, 5)
    countdown_timer(delay)

def main():
    try:
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

        query_ids = read_query_ids('data.txt')
        
        clear_terminal()
        art()

        auto_task = get_yes_no_input("Enable auto daily task? (y/n): ")
        auto_play_game = get_yes_no_input("Enable auto game play? (y/n): ")
        fast_game = False

        play_durov = get_yes_no_input("Do you play Durov? (y/n): ")

        other_tasks_enabled = get_yes_no_input("Enable other tasks? (y/n): ")

        starting_account = get_starting_account_number(len(query_ids))
        
        ending_account = len(query_ids)
        if not fast_game:
            ending_account = get_ending_account_number(starting_account, len(query_ids))

        user_agents = load_user_agents(query_ids)

        durov_choices = []
        if play_durov:
            while True:
                try:
                    durov_input = input("Input Durov choices (e.g: 4,6,9,10): ").strip()
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

        for index, query_id in enumerate(query_ids[starting_account:ending_account], start=starting_account):
            process_account(query_id, proxies_list, auto_task, auto_play_game, play_durov, durov_choices, account_proxies, total_balance, user_agents, index, proxy_usage, other_tasks_enabled, completed_tasks)

        if use_proxy:
            save_account_proxies(account_proxies)

        log_message(f"Total Balance of all accounts: {sum(total_balance)}", Fore.YELLOW)
        log_message("All accounts processed. Starting random timer for the next cycle.", Fore.CYAN)

        clear_error_log()
        clear_retry_log()

        random_timer = random.randint(8 * 60 * 60, 9 * 60 * 60)
        countdown_timer(random_timer)
        clear_terminal()
        art()

    except KeyboardInterrupt:
        graceful_exit()

if __name__ == "__main__":
    main()
