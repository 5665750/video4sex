#-*- coding=utf-8 -*-
import sys
sys.path.append("..")
import requests
import re
from threading import Thread
import Queue
import urllib2
from app import db
from app.models import Post, onlineTag
import sys
import argparse
import datetime
from hashlib import md5
import logging
import time


logger = logging.getLogger("ttc")
logger.setLevel(logging.DEBUG)
ch = logging.FileHandler("/root/video4sex/logs/ttc.log")
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

try:
    ttc = Post.query.filter_by(flag='ttc').first().zhan
except:
    ttc = 'http://www.tongtongcao.com'

ttc_url = ttc
flag = 'ttc'
proxies = {}


def get_cate():
    cont = requests.get(ttc).content
    cates = re.findall(
        '<a href="/\?m=vod-type-id-(\d+?)\.html">(.*?)</a>', cont)
    categorys = {}
    re_cate = {}
    for cate in cates:
        categorys[cate[1]] = cate[0]
        re_cate[cate[0]] = cate[1]
    return categorys, re_cate


def get_maxpage(cate_id):
    try:
        url = ttc + '/?m=vod-type-id-{cate_id}.html'.format(cate_id=cate_id)
        cont = requests.get(url).content
        max_page = int(re.findall(
            '<a target="_self" href="/\?m=vod-type-id-{cate_id}-pg-(\d+?)\.html" class="pagelink_a">'.format(cate_id=cate_id), cont)[-1])
    except:
        logger.info('{} get max page fail!'.format(cate_id))
        max_page = 1
    return max_page


def timenow():
    return datetime.datetime.now().strftime('%Y%m%d %H:%M:%S')


headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
           'Upgrade-Insecure-Requests': '1'}
parser = argparse.ArgumentParser()
parser.add_argument('-t', default='new')
parser.add_argument('-m1', default=1, type=int)
parser.add_argument('-m2', default=1, type=int)
args = parser.parse_args()

urls = {ttc_url: [args.m1, args.m2]}
info_reg = re.compile(
    '''<a class="link-hover" href="/\?m=vod-detail-id-(\d+?)\.html" title="(.*?)"><img class="lazy" data-original="(.*?)"''')
mp4_reg = re.compile('''unescape\('.*?(http.*?)'\)''')


cates, re_cate = get_cate()


class Get(Thread):
    def __init__(self, queue):
        super(Get, self).__init__()
        self.queue = queue

    def run(self):
        while 1:
            cateid, url = self.queue.get()
            logger.info('start parse ' + url)
            try:
                resp = requests.get(url, headers=headers, proxies=proxies)
                cont = resp.content
                urls = info_reg.findall(cont)
                logger.info('{} get {} videos'.format(url, len(urls)))
                for id, title, picture in urls:
                    url = ttc_url + \
                        '/?m=vod-play-id-{id}-src-1-num-1.html'.format(id=id)
                    picture = ttc_url + picture
                    if Post.query.filter_by(flag='ttc', id=id).count() == 0:
                        url2_queue.put((id, url, title, picture, cateid))
            except Exception, e:
                logger.info(e)
            time.sleep(1)
            if self.queue.empty():
                break


class Get2(Thread):
    def __init__(self, queue):
        super(Get2, self).__init__()
        self.queue = queue

    def run(self):
        while 1:
            id, url, title, picture, cateid = self.queue.get()
            logger.info('start parse ' + url)
            if Post.query.filter_by(flag='ttc', id=id).count() == 0:
                try:
                    resp = requests.get(url, headers=headers, proxies=proxies)
                    cont = resp.content
                    tag = re_cate[cateid]
                    mp4 = mp4_reg.findall(cont)[0]
                    mp4 = mp4.replace('%3A', ":")
                    mp4 = mp4.replace('%2F', "/")
                    mp44 = mp4
                    en = flag + '#' + id
                    m1 = md5(en)
                    encode = m1.hexdigest()
                    f = flag
                    logger.info(id + ' ' + title + ' ' + tag + ' ' + encode)
                except Exception, e:
                    logger.info(e)
                try:
                    data = Post(zhan=ttc_url, flag=f, id=id, title=title, picture=picture,
                                video=mp44, raw_video=mp4, encode=encode, createtime=timenow())
                    db.session.add(data)
                    db.session.commit()
                    logger.info(id + ' insert successfully')
                except Exception, e:
                    logger.info(str(id) + ' : insert fail')
                try:
                    logger.info(tag)
                    tagdata = onlineTag(
                        tag=tag, url=tag, encode_id=encode)
                    db.session.add(tagdata)
                    db.session.commit()
                except:
                    logger.info(str(id) + ' : insert tag fail')
                time.sleep(1)
                if self.queue.empty():
                    time.sleep(5)


url_queue = Queue.Queue()
url2_queue = Queue.Queue()

if args.t == 'reload':
    for tag, id in cates.items():
        max_page = get_maxpage(id)
        logger.info('{} max page : {}'.format(tag, max_page))
        for page in range(1, max_page + 1):
            url = ttc_url + \
                '/?m=vod-type-id-{id}-pg-{page}.html'.format(id=id, page=page)
            url_queue.put((id, url))
else:
    for tag, id in cates.items():
        url = ttc_url + '/?m=vod-type-id-{id}-pg-1.html'.format(id=id)
        url_queue.put((id, url))
for i in range(2):
    t = Get(url_queue)
    t.start()
for i in range(5):
    t1 = Get2(url2_queue)
    t1.start()
