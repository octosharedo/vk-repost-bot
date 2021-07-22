# coding=UTF-8
import vk_api, time, random, logging
import datetime
from tracker import track

#1 января, 00:00 текущего года
current_year = datetime.datetime.combine(datetime.date(datetime.date.today().year,1,1),datetime.time(0,0))
#дата через 5 дней от сейчас
track_date = (datetime.datetime.combine(datetime.date.today(),datetime.time(0,0)) + datetime.timedelta(5)).date()
logging.basicConfig(filename='logs/'+str(datetime.date.today())+'-white.log', level=logging.INFO)
	
def captcha_handler(captcha):
	logging.error("Captcha!")
	key = input("Enter captcha code {0}: ".format(captcha.get_url())).strip()
	return captcha.try_again(key) # Пробуем снова отправить запрос с капчей
	
vk_session = vk_api.VkApi('+375257134905', 'gfhfljrc62', captcha_handler=captcha_handler)
vk_session.auth()
vk = vk_session.get_api()

def links_search(text):
	links = []
	
	#search for [club*
	idx = text.find('[club') #get idx of 1st mentioned group (if any); else = -1
	while idx != -1:
		idx_end = text.find('|',idx+5) #that would be the end of group id
		group_id = text[idx+5:idx_end]
		if group_id.isdigit() and int(group_id) not in links:
			links.append(int(group_id))
		idx = text.find('[club', idx+5)

	#search for vk.com/*
	idx = text.find('vk.com/') #get name of 1st mentioned group (if any); else = -1
	while idx != -1:
		#после ссылки на группу будет либо пробел, либо новая строка. ищем индекс конца ссылки.
		idx_end_1 = text.find(' ',idx+7)
		idx_end_2 = text.find('\n',idx+7)
		idx_end = idx_end_1 if idx_end_1 < idx_end_2 else idx_end_2
		
		group_name = text[idx+7:idx_end]
		try:
			group_id = vk.groups.getById(group_id = group_name)[0]['id']
			if group_id not in links:
				links.append(group_id)
		except vk_api.exceptions.ApiError as msg:
			logging.error("exception! " + str(msg))
		finally:
			idx = text.find('vk.com/', idx+7)

	return links #айдишники всех упомянутых в посте групп

def repost(response, club_id):
	k = 0
	for item in response:
		k +=1
		logging.info(k)
		logging.info("looking into: " + 'wall-'+str(club_id)+'_'+str(item['id']))
		
		links = links_search(item['text'])

		if club_id==37268163 and 'старт' in item['text'].lower():
			text=''
			vk.wall.createComment(owner_id = -club_id, post_id = item['id'], message = 'Старт')
			comments = vk.wall.getComments(owner_id = -club_id, post_id = item['id'], count = 5, extended = 1, thread_items_count = 1)['items']
			for i in range(5): #searching for instructions
				for j in range (comments[i]['thread']['count']):
					if comments[i]['thread']['items'][j]['from_id'] == -club_id:
						text = comments[i]['thread']['items'][j]['text']
						break
				if text != '':
					break					
			if text == '': #if smth went wrong and instructions couldn't be found
				logging.error('Something went wrong during comment extraction. Aborting process.')
				continue
			links = links.append(links_search(text)) #adding links

		#repost
		try:
			repostInfo = vk.wall.repost(object='wall-'+str(club_id)+'_'+str(item['id']))
			logging.info("made repost: " + str(repostInfo['post_id']))
			track(track_date, repostInfo['post_id'], links)
		except vk_api.exceptions.ApiError as msg:
			logging.error("exception! " + str(msg))
			continue
				
		#join groups
		if links != None:
			for j in links:
				try:
					vk.groups.join(group_id = int(j))
					logging.info("joined: " + str(j))
				except vk_api.exceptions.ApiError as msg:
					logging.error("exception! " + str(msg))
					continue
		#wait
		logging.info("\n")
		time.sleep(120.0+random.random()*120.0)                   

def filter(response, date):
	logging.info('found '+str(len(response)))
	response = [item for item in response if datetime.datetime.fromtimestamp(item['date']) > current_year]
	logging.info('filter this year. left: '+str(len(response)))
	response = [item for item in response if item['reposts']['user_reposted']==0]
	logging.info('filter already reposted. left: '+str(len(response)))
	response = [item for item in response if date in item['text'] and (('1'+date) not in item['text']) and (('2'+date) not in item['text'])]
	logging.info('filter needed date. left: '+str(len(response)))
	return response

def whiteList():
	yesterday = datetime.datetime.combine(datetime.date.today(),datetime.time(0,0)) - datetime.timedelta(1)
	months = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноябра','декабря']
	todayDate = datetime.date.today()
	tomorrowDate = (datetime.datetime.combine(todayDate,datetime.time(0,0)) + datetime.timedelta(1)).date()
	today = str(todayDate.day) + ' ' + months[todayDate.month -1]
	tomorrow = str(tomorrowDate.day) + ' ' + months[tomorrowDate.month -1]

	clubId = 79525017 #search 'подписчик'
	logging.info('club79525017 searching "подписчик '+today+'"')
	response = vk.wall.search(owner_id = -clubId, query = 'подписчик '+today, count = 20)['items']
	repost(filter(response,today),clubId)
	logging.info('club79525017 searching "подписчик '+tomorrow+'"')
	response = vk.wall.search(owner_id = -clubId, query = 'подписчик '+tomorrow, count = 20)['items']
	repost(filter(response,tomorrow),clubId)

	clubId = 97758272 #search 'подписчик'
	logging.info('club97758272 searching "подписчик '+today+'"')
	response = vk.wall.search(owner_id = -clubId, query = 'подписчик '+today, count = 20)['items']
	repost(filter(response,today),clubId)
	logging.info('club97758272 searching "подписчик '+tomorrow+'"')
	response = vk.wall.search(owner_id = -clubId, query = 'подписчик '+tomorrow, count = 20)['items']
	repost(filter(response,tomorrow),clubId)

	clubId = 76256545 #search 'подписчик'
	logging.info('club76256545 searching "подписчик '+today+'"')
	response = vk.wall.search(owner_id = -clubId, query = 'подписчик '+today, count = 20)['items']
	repost(filter(response,today),clubId)
	logging.info('club76256545 searching "подписчик '+tomorrow+'"')
	response = vk.wall.search(owner_id = -clubId, query = 'подписчик '+tomorrow, count = 20)['items']
	repost(filter(response,tomorrow),clubId)

	clubId = 77411518 #однодневные конкурсы с "УЖЕ (после)ЗАВТРА"
	logging.info('club77411518 searching "послезавтра"')
	response = vk.wall.search(owner_id = -clubId, query = 'послезавтра', count = 20)['items']
	logging.info('found: '+str(len(response)))
	response = [item for item in response if datetime.datetime.fromtimestamp(item['date']) > yesterday]
	logging.info('filter since yesterday. left: '+str(len(response)))
	response = [item for item in response if item['reposts']['user_reposted']==0]
	logging.info('filter already reposted. left: '+str(len(response)))
	repost(response,clubId)
	logging.info('club77411518 searching "завтра"')
	response = vk.wall.search(owner_id = -clubId, query = 'завтра', count = 20)['items']
	logging.info('found: '+str(len(response)))
	response = [item for item in response if datetime.datetime.fromtimestamp(item['date']) > yesterday]
	logging.info('filter since yesterday. left: '+str(len(response)))
	response = [item for item in response if item['reposts']['user_reposted']==0]
	logging.info('filter already reposted. left: '+str(len(response)))
	repost(response,clubId)

	clubId = 37268163 #искать дату и комментить "старт"
	logging.info('club37268163 searching "'+today+'"')
	response = vk.wall.search(owner_id = -clubId, query = today, count = 20, owners_only = 1)['items']
	repost(filter(response,today),clubId)
	logging.info('club37268163 searching "'+tomorrow+'"')
	response = vk.wall.search(owner_id = -clubId, query = tomorrow, count = 20, owners_only = 1)['items']
	repost(filter(response,tomorrow),clubId)
	
if __name__ == "__main__":
	print('White List')
	whiteList()