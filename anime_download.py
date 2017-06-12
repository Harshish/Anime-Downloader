import mechanize
import sys,os,re,requests
from bs4 import BeautifulSoup
from mechanize._opener import urlopen
from tqdm import tqdm
from termcolor import colored, cprint

def fetchData(br,url):
	try:
		response = br.open(url)
	except mechanize.HTTPError as e:
		cprint("TIME OUT TRYING AGAIN", 'yellow', attrs=['bold'])
		return None
	return BeautifulSoup(response.read(),'html.parser')

def getDownloadURL(res):
	matchObj = re.match(r'(.*)player\.load\(\{(.*)file: "(.*)",(.*)\}\)\;',res,re.MULTILINE | re.DOTALL  )
	if matchObj:
	   dwnldURL = matchObj.group(3)
	else:
	   cprint("URL NOT FOUND TRYING MIRROR", 'yellow', attrs=['bold'])
	   return None

	matchObj = re.match(r'(.*)/(.*)\?(.*)',dwnldURL,re.DOTALL)
	if matchObj:
		fname = matchObj.group(2)
		cprint("FOUND: %s\n" % fname, 'green', attrs=['bold'])
	else:
		cprint("NO FILENAME FOUND USING DEFAULT", 'magenta', attrs=['bold'])
		fname = "video.flv"

	return (dwnldURL,fname)

def downloadFile(dwnldURL,fname):
	r = requests.get(dwnldURL, stream=True)
	total_size = int(r.headers.get('content-length', 0)); 

	with open(fname, 'wb') as f:
	    for data in tqdm(r.iter_content(chunk_size=1), total=total_size, unit='B', unit_scale=True):
	        f.write(data)
	        
try:	
	anime = raw_input(colored("ANIME NAME (AS ON animeplus.tv): ", 'magenta', attrs=['bold']))
	anime = anime.replace(' ','-')
	anime = anime.lower()
	fpath = ''
	flag = True
	while flag:
		ans = raw_input(colored("USE DEFAULT FILEPATH Y/N?: ", 'magenta'))
		if ans=="n" or ans =="N" or ans=="no" or ans=="NO":
			fpath = raw_input(colored("ENTER FILE PATH: ", 'blue'))
			flag = False
		elif ans=="y" or ans =="Y" or ans=="yes" or ans=="YES":
			flag = False
		else:
			cprint("INVALID CHOICE TRY AGAIN OR PRESS N TO EXIT", 'yellow', attrs=['bold'])


	br = mechanize.Browser()
	br.set_handle_equiv(True)
	br.set_handle_redirect(True)
	br.set_handle_referer(True)
	br.set_handle_robots(False)
	br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
	headers = [('User-agent', 
				'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
	br.addheaders = headers

	link = 'http://www.animeplus.tv/{}-online'.format(anime)
	soup = fetchData(br,link)
	while soup==None:
		soup = fetchData(br,link)
	videosDiv = soup.find_all(id='videos')
	for v in videosDiv:
		anchors = v.find_all('a')
	try:
		testurl =  anchors[0]['href']
	except:
		sys.exit(colored("\nLINK PARSING NOT FEASIBLE", 'red', attrs=['bold']))

	matchObj = re.match(r'http://www.animeplus.tv/(.*)-(.*)-online',testurl,re.MULTILINE | re.DOTALL  )
	if matchObj:
		total_episodes = int(matchObj.group(2))
	   	url = []
		for i in xrange(1,total_episodes + 1):
			url.append("http://www.animeplus.tv/{}-episode-{}-online".format(anime,i))
	else:
		total_episodes = -1

	if(total_episodes > 0):
		cprint("TOTAL EPISODES: %d" % len(url), 'cyan', attrs=['bold'])
	cprint("DOWNLOAD OPTIONS:\n-> ALL\n-> RANGE x-y (x,y = [1..n])\n-> EPISODE x (x = [1..n])\n", 'blue', attrs=['bold'])

	flag = True
	st = 0
	end = 0
	while(flag):
		ep = raw_input('OPT: ')
		if ep=="all" or ep=="ALL":
			st = 1
			end = len(url) + 1
			flag = False
		elif '-' in ep:
			s = ep.split('-')
			st = int(s[0])
			end = int(s[1])
			flag = False
			if end > len(url):
				cprint("EPISODES OUT OF RANGE TRY AGAIN PRESS Q TO EXIT", 'yellow', attrs=['bold'])
				flag = True
			end += 1
		elif ep.isdigit():
			st = int(ep)
			end = st + 1
			flag = False
		elif ep=="q" or ep=="Q":
			sys.exit(colored("EXITING IN PEACE", 'red', attrs=['bold']))
		else:
			cprint("INVALID CHOICE TRY AGAIN OR PRESS Q TO EXIT", 'yellow', attrs=['bold'])

	for i in xrange(st,end):
		cprint("FETHING CONTENT VIA: %s\n" % url[i-1], 'green', attrs=['bold'])
		soup = fetchData(br,url[i-1])
		while soup==None:
			soup = fetchData(br,link)
		streamsDiv = soup.find_all(id='streams')
		
		for elem in streamsDiv:
			frm = elem.findAll('iframe')
		mirrors = []
		for a in frm:
			mirrors.insert(0,str(a['src']))
		mcount = 0
		flag = True
		while flag:
			soup = fetchData(br,mirrors[mcount])
			res = str(soup)
			retinfo = getDownloadURL(res)
			if retinfo!=None:
				flag = False
			else:
				mcount += 1
				if mcount > len(mirrors):
					sys.exit(colored("CANNOT FIND MEDIA FOR %s" % anime, 'red', attrs=['bold']))

		fname = os.path.join(fpath, retinfo[1])
		if os.path.exists(fname):
			cprint("%s ALREADY EXISTS REWRITE Y/N?" % fname, 'yellow', attrs=['bold'])

			flag = True
			while flag:
				ans = raw_input()
				if ans=="n" or ans =="N" or ans=="no" or ans=="NO":
					sys.exit(colored("EXITING IN PEACE", 'red', attrs=['bold']))
				elif ans=="y" or ans =="Y" or ans=="yes" or ans=="YES":
					flag = False
				else:
					cprint("INVALID CHOICE TRY AGAIN OR PRESS N TO EXIT", 'yellow', attrs=['bold'])

		downloadFile(retinfo[0],fname)
except (KeyboardInterrupt, SystemExit):
	sys.exit(colored("\nFORCED EXIT", 'red', attrs=['bold']))