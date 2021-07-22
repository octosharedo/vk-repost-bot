# Чистильщик. 
# 	Берет заготовленный на сегодня файл.
# 		В файле содержатся id репостов, id групп, в которые вступили из-за репоста.
# 	Выходит из групп, удаляет репосты.
# 	Функция track используется другими скриптами. 
# 		С помощью Track заготавливается файл удаления на будущее.

import vk_api, datetime, os, time, random
my_id = str(input()) #id страницы вк бота
white_list = [79525017, 97758272, 76256545, 77411518, 37268163] #список id групп белого списка

def captcha_handler(captcha):
	logging.error("Captcha!")
	key = input("Enter captcha code {0}: ".format(captcha.get_url())).strip()
	return captcha.try_again(key) # Пробуем снова отправить запрос с капчей

#инициализация
login = str(input())
password = str(input())
vk_session = vk_api.VkApi(login, password, captcha_handler=captcha_handler)
vk_session.auth()
vk = vk_session.get_api()

def track(date, post_id, links):
	'''записываем id поста-репоста, под ним - id групп, на которые подписались из-за этого поста'''
	with open('logs/'+str(date)+'-delete.txt','a') as track_file:
		track_file.write(str(post_id)+'\n')
		if links !=  None:
			for link in links:
				#если группа нам не знакома (не из белого списка), запишем, чтобы потом выйти
				#из групп, принадлежащих белому списку, не выходим
				if link not in white_list: track_file.write(str(link)+' ')
		track_file.write('\n')

def delete_post(post_id, links):
	'''удаляем репост, выходим из всех связанных с ним групп'''
	for link in links: vk.groups.leave(group_id = link)
	logging.info('left groups: '+ ' '.join(list(map(str,links))))
	try:
		vk.wall.delete(owner_id = my_id, post_id = post_id)
		logging.info('deleted post: '+str(post_id))
	except vk_api.VkApiError as msg:
		logging.error('error! failed deleting post: '+str(post_id)+': '+str(msg))

def scan_file(date):
	'''ходим по файлу (который создается с помощью track),
	собираем id репостов и id связанных с ними групп,
	удаляем репосты, выходим из групп'''
	try:
		with open('logs/'+str(date)+'-delete.txt') as track_file:
			while True:
				post_id = track_file.readline().strip()
				if post_id == '':
					break
				else:
					post_id = int(post_id)
				links = track_file.readline().strip().split()
				links = [int(i) for i in links]
				delete_post(post_id,links)
		os.remove('logs/'+str(date)+'-delete.txt')
		logging.info('File for '+str(date)+' deleted')
	except FileNotFoundError:
		logging.info('Nothing to do.')
		

if __name__ == "__main__":
	import logging
	print('Tracker')
	logging.basicConfig(filename='logs/'+str(datetime.date.today())+'-tracker.log', level=logging.INFO)
	scan_file(datetime.date.today())