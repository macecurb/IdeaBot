from bs4 import BeautifulSoup
import dataloader, time, logging
import sys
sys.path.append('./libs/scraperlibs')
import pageRet

config = dataloader.datafile('./data/reddit.config')
config.content = config.content["DEFAULT"]
print(config.content["datafilepath"])
data = dataloader.datafile(config.content["datafilepath"])
data.content = [x.strip("\n") for x in data.content]
urllist = dataloader.datafile(config.content["urlfilepath"])
urllist.content = [x.strip("\n") for x in urllist.content]

def redditLogging():
    '''() -> Logger class
    set ups main log so that it outputs to ./scraperr.log and then returns the log'''
    logger = logging.getLogger('reddit')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(filename='scraperr.log', encoding='utf-8', mode='w')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s: %(message)s'))
    logger.addHandler(handler)
    return logger

redditLog = redditLogging()

def is_new_comment(url):
    '''(str) -> bool
    checks reddit.txt for whether the url is new or not'''
    #is_new = True
    return url.strip("\n") not in data.content
    '''
    if len(data.content) > 0:
        for i in range(len(data.content)):
            if data.content[i][:len("Most Recent Thread:")].lower() == "most recent thread:" : # if it's the file line about most recent thread
                if url == data.content[i][len("Most Recent Thread:"):len("Most Recent Thread:")+len(url)]:
                    is_new = False
                else:
                    break
    return is_new '''

def delete_entry(string):
    '''(str [, bool])->bool
    delete the first entry in data.content that contains string, if it exists'''
    for i in range(len(data.content)):
        if string.lower() in data.content[i].lower():
            del(data.content[i])
            return True
    return False

def continuousScrape(q, stop, newThread):
    '''(Queue object, Queue object, Queue object) -> None
    checks continuously for changes in the freeforums. A [url (str), affected users(str)] object is reported through q when anything changes
    This should be run in a different thread since it is blocking (it's a fucking while loop ffs)
    stop.put(anything) will stop the loop'''
    redditLog.info("Thread started")
    mostrecentrunstart = -100000
    time.sleep(10)
    while stop.empty(): # run continuously unless there's something in stop
        if time.time() - mostrecentrunstart >= int(config.content["period"]):
            while not newThread.empty():
                item = newThread.get()
                if item["url"][-len(".rss?sort=new"):] != ".rss?sort=new":
                    item["url"] = item["url"]+".rss?sort=new"
                if item["action"] == "remove" or item["action"] == "delete":
                    try:
                        del(urllist.content[urllist.content.index(item["url"])])
                        redditLog.info(item["url"]+" successfully removed")
                    except:
                        redditLog.info(item["url"]+" wasn't found nor removed")
                elif item["action"]=="add":
                    if item["url"] not in urllist.content:
                        urllist.content.append(item["url"])
                        redditLog.info(item["url"]+" successfully added")
                    else:
                        redditLog.info(item["url"]+" already existed so was not added")
            urllist.save()

            redditLog.info("Starting scraping run")
            mostrecentrunstart = time.time()
            for url in urllist.content:
                redditLog.info("Now scraping " + url)
                try:
                    rss = BeautifulSoup(pageRet.pageRet(url).decode(), "html.parser") # rss page
                    items = rss.find_all("entry")[1:]
                    comments = [[x.find("link").get("href"), x.find("title").get_text()] for x in items] # list of [url, thread title]

                    if is_new_comment(comments[0][0]):
                        redditLog.info("New response found: " + comments[0][0])
                        data.content.append(comments[0][0])
                        q.put([url[:-len(".rss?sort=new")], "https://reddit.com"+comments[0][0]])
                        data.save()
                    redditLog.info("Finished scraping run in "+ str(time.time() - mostrecentrunstart))
                except:
                    redditLog.warning("Scraping " + url + " failed. Either the page has changed or the page is unavailable...")
    redditLog.info("Stopped")


# debug pls comment out everything under here if it isn't already
#continuousScrape(None,None)

#data.save()
