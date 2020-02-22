import time 
import eventlet 
import requests 
import logging 
import telebot
import json
import os
from time import sleep

with open ('config.json') as config:
	data = json.load(config)
	URL_VK = data['URL_VK']
	BOT_TOKEN = data['BOT_TOKEN']
	CHANNEL_NAME = data['CHANNEL_NAME']

# URL_VK = os.environ['URL_VK']
# BOT_TOKEN = os.environ['BOT_TOKEN']
# CHANNEL_NAME = os.environ['CHANNEL_NAME']

bot = telebot.TeleBot(BOT_TOKEN)
SINGLE_RUN = False
PERIOD_CHECK_TIME = 240 # 4 min

def get_data():
	timeout = eventlet.Timeout(10)
	try:
		feed = requests.get(URL_VK)
		return feed.json()
	except eventlet.timeout.Timeout:
		logging.warning('Got Timeout while retrieving VK JSON data. Cancelling...')
		return None
	finally:
		timeout.cancel()

def send_new_posts(items):
	for item in items:
		if int(time.time()) - item['date'] > PERIOD_CHECK_TIME: 
			break
		if 'attachments' in item:
			if 'photo' in item['attachments'][0]:
				img_sizes = item['attachments'][0]['photo']['sizes']
				img_url = next(x for x in img_sizes if x['type'] == 'x')['url']
				bot.send_photo(CHANNEL_NAME, img_url)			
		if 'text' in item:
			text = item['text']
			bot.send_message(CHANNEL_NAME, text, disable_web_page_preview=True)		
		time.sleep(1)
	return

def check_new_posts_vk():
	logging.info('[VK] Started scanning for new posts')
	try:
		feed = get_data()
		if feed is not None:
			entries = feed['response']
			if entries['items'] != []:					
				if 'is_pinned' in entries['items'][0]:
					wall_posts = entries['items'][1:]
				else:
					wall_posts = entries['items']
				send_new_posts(wall_posts)
				new_last_id = wall_posts[0]['id']		
				logging.info('New last_id (VK) is {!s}'.format(new_last_id))
	except Exception as ex:
		logging.error('Exception of type {!s} in check_new_post():{!s}').format(type(ex).__name__,str(ex))
		pass
	logging.info('[VK] Finished scanning')
	return

if __name__ == '__main__':
	logging.getLogger('requests').setLevel(logging.CRITICAL)
	logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s', level=logging.INFO, filename='bot_log.log', datefmt='%d.%m.%Y %H:%M:%S')
	if not SINGLE_RUN:
		while True:
			check_new_posts_vk()
			logging.info('[App] Script went to sleep.')
			time.sleep(PERIOD_CHECK_TIME)
	else:
		check_new_posts_vk()
	logging.info('[App] Script exited. \n')