# coding=UTF-8
import vk_api, time, random, logging
import datetime
from tracker import track
#1 января, 00:00 текущего года
current_year = datetime.datetime.combine(datetime.date(datetime.date.today().year,1,1),datetime.time(0,0))
#дата через 5 дней от сейчас
track_date = (datetime.datetime.combine(datetime.date.today(),datetime.time(0,0)) + datetime.timedelta(5)).date()

#инициализация
def captcha_handler(captcha):
	logging.error("Captcha!")
	key = input('Attention!\n Captcha required: {0} :'.format(captcha.get_url())).strip().strip('\n')
	return captcha.try_again(key) # Пробуем снова отправить запрос с капчей
login_number = str(input())
password = str(input())
vk_session = vk_api.VkApi(login_number, password, captcha_handler=captcha_handler)
vk_session.auth()
vk = vk_session.get_api()
logging.basicConfig(filename='logs/'+str(datetime.date.today())+'.log', level=logging.INFO)

def linksSearch(text):
	links = []
	
	#search for [club*
	idx = text.find('[club') #get idx of 1st mentioned group (if any); else = -1
	while idx != -1:
		idx_end = text.find('|',idx+5) #that would be the end of group id
		groupId = text[idx+5:idx_end]
		if groupId.isdigit() and int(groupId) not in links:
			links.append(int(groupId))
		idx = text.find('[club', idx+5)

	#search for vk.com/*
	idx = text.find('vk.com/') #get name of 1st mentioned group (if any); else = -1
	while idx != -1:
		#после ссылки на группу могут быть ' ', '\n', ',', '.', ';'. ищем индекс конца ссылки.
		idx_end = [text.find(' ',idx+7),text.find('\n',idx+7),text.find(',',idx+7),text.find('.',idx+7),text.find(';',idx+7)]
		idx_end = [i for i in idx_end if i>0]
		if idx_end!=[]:
			idx_end = min(idx_end)
		else:
			logging.info('Could not find the end of groupname')
			idx = text.find('vk.com/', idx+7)
			continue
		
		groupName = text[idx+7:idx_end]
		try:
			groupId = vk.groups.getById(group_id = groupName)[0]['id']
			if groupId not in links:
				links.append(groupId)
		except vk_api.exceptions.ApiError as msg:
			logging.error("exception! during searching vk.com/: " + str(msg)+ ". Groupname was "+groupName)
		finally:
			idx = text.find('vk.com/', idx+7)

	return links #айдишники всех упомянутых в посте групп

def filter(response,date):
	black_list = ['клан', 'трейд','warface','youtube', 'rp','сервер','cs:go','аватария','ролевая','фотограф', 'fortnite','coin','role play','gta','cs go', 'csgo', 'аккаунт', 'page player', 'brawl stars', 'warface', 'roleplay', 'оформление', 'server', 'minecraft', 'майнкрафт', 'тумботино','детские', 'swell4ik']
	
	logging.info('found '+str(len(response['items'])))
	#filter little groups pt.1
	littles_ids = [item['id'] for item in response['groups'] if item['members_count']<500]
	#filter blacklisters pt.1
	black_ids = [item['id'] for item in response['groups'] if [i for i in black_list if i in item['name'].lower()]]
	#filter this year
	response = [item for item in response['items'] if datetime.datetime.fromtimestamp(item['date']) > current_year]
	logging.info('filter this year. left: '+str(len(response)))
	#filter users
	response = [item for item in response if item['owner_id']<0]
	logging.info('filter users. left '+str(len(response)))
	#filter already reposted
	response = [item for item in response if item['reposts']['user_reposted']==0]
	logging.info('filter already reposted. left '+str(len(response)))
	#filter needed date
	response = [item for item in response if date in item['text'] and (('1'+date) not in item['text']) and (('2'+date) not in item['text'])]
	logging.info('filter needed date. left: '+str(len(response)))
	#filter little groups pt.2
	response = [item for item in response if (-item['owner_id']) not in littles_ids]
	logging.info('filter little groups. left '+str(len(response)))
	#filter blacklisters pt.2
	response = [item for item in response if (-item['owner_id']) not in black_ids]
	logging.info('filter blacklisters. left '+str(len(response)))
	del littles_ids, black_ids, black_list
	return response

def repost(response):
	k = 0
	for item in response:
		logging.info(k) #it's K-th post now
		k += 1
		logging.info("looking into: " + 'wall'+str(item['owner_id'])+'_'+str(item['id']))
		
		links = linksSearch(item['text'])
		if -item['owner_id'] not in links:
			links.append(-item['owner_id'])

		#repost
		try:
			repost_info = vk.wall.repost(object='wall'+str(item['owner_id'])+'_'+str(item['id']))
			logging.info("made repost: " + str(repost_info['post_id']))
			track(track_date, repost_info['post_id'], links)
		except vk_api.exceptions.ApiError as msg:
			logging.error("error! failed reposting: " + str(msg))
			continue
				
		#join groups
		for j in links:
			try:
				vk.groups.join(group_id = int(j))
				logging.info("joined: " + str(j))
			except vk_api.exceptions.ApiError as msg:
				logging.error("error! failed joining: " + str(msg))
				continue
		#wait
		logging.info("\n")
		time.sleep(120.0+random.random()*120.0)

def generalSearch():
	months = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноябра','декабря']
	todayDate = datetime.date.today()
	tomorrowDate = (datetime.datetime.combine(todayDate,datetime.time(0,0)) + datetime.timedelta(1)).date()
	today = str(todayDate.day) + ' ' + months[todayDate.month -1]
	tomorrow = str(tomorrowDate.day) + ' ' + months[tomorrowDate.month -1]
	
	logging.info('searching for today')
	response = vk.newsfeed.search(extended = 1, fields = 'members_count', q = today + u' конкурс репост лайк -уведомления -голосуем -напоминаем -концу -youtube -завершился -закончился -ниже -проголосовать -свадьба -курганский -голосование -поздравляем -фотограф -нарисовать -скоро -csgo -ванны -ванн -колокольчик -админка -скриншот -cs -ксго -клан -пиар -админ -bitcoin -аватарка -установи -закреп -coin -майнить -VkPoint -VKC -altcoin -аккаунт -последний -последние -валюта -коин -загрузить -коммент -активным -аватария -выложить -отписаться -друзя -напишите -поселок -участвую -вирт -администратор -бан -оставить -скоро -уведомлять -закрепить -активность -рассылка -комм -комент -сервер -койн -пригласить -закреплена -коментарий -комментарий -зарегистрироваться', count = 200)
	response = filter(response,today)
	repost(response)
	logging.info('search for today is finished!')

	logging.info('searching for tomorrow')
	response = vk.newsfeed.search(extended = 1, fields = 'members_count', q = tomorrow + u' конкурс репост лайк -уведомления -голосуем -напоминаем -концу -youtube -завершился -закончился -ниже -проголосовать -свадьба -курганский -голосование -поздравляем -фотограф -нарисовать -скоро -csgo -ванны -ванн -колокольчик -админка -скриншот -cs -ксго -клан -пиар -админ -bitcoin -аватарка -установи -закреп -coin -майнить -VkPoint -VKC -altcoin -аккаунт -последний -последние -валюта -коин -загрузить -коммент -активным -аватария -выложить -отписаться -друзя -напишите -участвую -вирт -администратор -бан -оставить -скоро -уведомлять -закрепить -активность -рассылка -комм -комент -сервер -койн -пригласить -закреплена -коментарий -комментарий -зарегистрироваться', count = 200)
	response = filter(response,tomorrow)
	repost(response)
	logging.info('search for tomorrow is finished!')

	logging.info("General Search is finished.")

if __name__ == "__main__":
	print('General Search')
	generalSearch()