import time 
import eventlet 
import requests 
import logging 
import telebot
import json
from time import sleep

with open ('config.json') as config:
	data = json.load(config)
	URL_VK = data['URL_VK']
	FILENAME_VK = data['FILENAME_VK']
	BASE_POST_URL = data['BASE_POST_URL']	
	BOT_TOKEN = data['BOT_TOKEN']
	CHANNEL_NAME = data['CHANNEL_NAME']

bot = telebot.TeleBot(BOT_TOKEN)
SINGLE_RUN = False

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

def send_new_posts(items, last_id):
	for item in items:
		if item['id'] <= last_id:
			break
		text = item['text']
		img_sizes = item['attachments'][0]['photo']['sizes']
		img_url = next(x for x in img_sizes if x['type'] == 'x')['url']
		bot.send_photo(CHANNEL_NAME, img_url)
		bot.send_message(CHANNEL_NAME, text, disable_web_page_preview=True)
		time.sleep(1)
	return

def check_new_posts_vk():
	logging.info('[VK] Started scanning for new posts')
	with open(FILENAME_VK, 'rt') as file:
		last_id = int(file.read())
		if last_id is None:
			logging.error('Could not read from storage. Skipped iteration.')
			return
		logging.info('Last ID (VK) = {!s}'.format(last_id))
	try:
		feed = get_data()
		if feed is not None:
			entries = feed['response']
			if 'is_pinned' in entries['items'][0]:
				wall_posts = entries['items'][1:]
			else:
				wall_posts = entries['items']
			send_new_posts(wall_posts, last_id)
			new_last_id = wall_posts[0]['id']		
			with open(FILENAME_VK, 'wt') as file:
				file.write(str(new_last_id))
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
			time.sleep(60 * 4)
	else:
		check_new_posts_vk()
	logging.info('[App] Script exited. \n')