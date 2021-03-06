from bs4 import BeautifulSoup
import dataloader, time, logging
import sys
sys.path.append('./libs/scraperlibs')
import pageRet

config = dataloader.datafile('./data/freeforums.config')
config.content = config.content["DEFAULT"]
print(config.content["datafilepath"])
data = dataloader.datafile(config.content["datafilepath"])

def forumLogging():
    '''() -> Logger class
    set ups main log so that it outputs to ./scraperf.log and then returns the log'''
    logger = logging.getLogger('forum')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename='scraperf.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s: %(message)s'))
    logger.addHandler(handler)
    return logger

forumLog = forumLogging()

def is_new_thread(url):
    '''(str) -> bool
    checks freeforums.txt for whether the url is new or not'''
    is_new = True
    if len(data.content) > 0:
        for i in range(len(data.content)):
            if data.content[i][:len("Most Recent Thread:")].lower() == "most recent thread:" : # if it's the file line about most recent thread
                if url[:-3] == data.content[i][len("Most Recent Thread:"):len("Most Recent Thread:")+len(url)][:-3]:
                    is_new = False
                else:
                    break
    return is_new

def has_new_stuff(url):
    if len(data.content) > 0:
        for i in range(len(data.content)):
            if data.content[i][:len("Most Recent Thread:")].lower() == "most recent thread:" : # if it's the file line about most recent thread
                if url == data.content[i][len("Most Recent Thread:"):len("Most Recent Thread:")+len(url)]:
                    is_new = False
                else:
                    break
    return is_new

def get_most_recent():
    '''(None) -> str
    returns the url of the most recent thread in data.content'''
    for i in range(len(data.content)):
        if data.content[i][:len("Most Recent Thread:")].lower() == "most recent thread:" : # if it's the file line about most recent thread
            return data.content[i][len("Most Recent Thread:")+1:]

def get_trailing_int(url):
    '''(str) -> int
    finds the integer at the end of RSS Proboard URLs
    ie http://ideahavers.freeforums.net/thread/42/answer-life-universe-everything-666 returns 666'''
    return int(url.split("-")[-1])


def delete_entry(string):
    '''(str [, bool])->bool
    delete the first entry in data.content that contains string, if it exists'''
    for i in range(len(data.content)):
        if string.lower() in data.content[i].lower():
            del(data.content[i])
            return True
    return False

def continuousScrape(q, stop):
    '''(Queue object, Queue object) -> None
    checks continuously for changes in the freeforums. A [url (str), affected users(str)] object is reported through q when anything changes
    This should be run in a different thread since it is blocking (it's a fucking while loop ffs)
    stop.put(anything) will stop the loop'''
    forumLog.info("Thread started")
    mostrecentrunstart = -100000
    while stop.empty(): # run continuously unless there's something in stop
        if time.time() - mostrecentrunstart >= int(config.content["period"]):
            forumLog.info("Starting scraping run")
            mostrecentrunstart = time.time()
            try:
                rss = BeautifulSoup(pageRet.pageRet(config.content["url"]).decode(), "html.parser") # landing page
                items = rss.find_all("item")
                threads = [[x.find("guid").get_text(), x.find("title").get_text()] for x in items] # list of [url, thread title]

                if is_new_thread(threads[0][0]):
                    newestint = get_trailing_int(get_most_recent())
                    for i in threads:
                        if get_trailing_int(i[0]) > newestint:
                            forumLog.info("New thread found: " + i[0])
                            #scrape stuff
                            recentThread = BeautifulSoup(pageRet.pageRet(i[0]).decode(),"html.parser")
                            authors = []
                            for x in recentThread.find_all("div", class_="mini-profile"):
                                try:
                                    authors.append({"name" : x.find("a").get_text(),"url" : x.find("a").get("href"), "img" : x.find("div", class_="avatar").find("img").get("src")})
                                except AttributeError: # if author is a guest, x.find("a") will return a NoneType, and None.get("href") will raise an AttributeError
                                    pass
                            #authors = [x.find("a").get("href") for x in recentThread.find_all("div", class_="mini-profile")]
                            q.put([i[0], authors])
                        else:
                            break
                    delete_entry("most recent thread:")
                    data.content.append("most recent thread:" + threads[0][0])
                    data.save()
                    forumLog.info("Most recent thread is now: " + threads[0][0])
                forumLog.info("Finished scraping run in "+ str(time.time() - mostrecentrunstart))
            except:
                forumLog.warning("Scraping run failed. Either the page has changed or the page is unavailable...")
    forumLog.info("Stopped")


# debug pls comment out everything under here if it isn't already
#continuousScrape(None,None)

#data.save()
