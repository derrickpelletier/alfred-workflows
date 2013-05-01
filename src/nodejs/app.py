import os, urllib, urllib2, re, hashlib, subprocess, datetime
try:
  import xml.etree.cElementTree as et
except ImportError:
  import xml.etree.ElementTree as et

import alfred
alfred.setDefaultEncodingUTF8()
from bs4 import BeautifulSoup

from pprint import pprint

__version__ = '1.0'
CACHE_EXPIRE = 60 * 30

class App(object):

  def run(self):

    arg1 = alfred.argv(1) # version or page
    arg2 = alfred.argv(2) # Would be the page if using a version
    arg3 = alfred.argv(3) # Could be a property or method only

    ver = None
    page = ''
    search = None

    # Parse args to figure out which page this is.
    if not arg1:
      return self.showDefaultList()

    arg1 = arg1.lower()
    if arg1.replace(".","").isdigit():
      ver = arg1
      if arg2 is not None:
        page = arg2.lower()
      if arg3 is not None:
        search = arg3.lower()
    else:
      page = arg1
      if arg2 is not None:
        search = arg2.lower()

    # Make the URL for the all page, whether it is version specific or not.
    url = 'http://nodejs.org/'
    if ver is not None:
      url = url + 'docs/' + 'v0.' + ver + '/'
    url = url + "api/" + page + ".html"

    # Begin feedback loop
    feedback = alfred.Feedback()

    if not search:
      feedback.addItem(title='Table of Contents', subtitle=page + ' toc', arg=url + 'html#toc')
    
    success, data = self.getTocOfPage(url)
    
    if not success:
      alfred.exitWithFeedback(title=data)

    for item in data:
      if not search or (search is not None and item['name'].lower().find(search) > -1 ):
        feedback.addItem(title=item['name'], subtitle=item['subtitle'], arg= url + item['link'])

    feedback.output()


  def reqUrl(self, url):
    res = alfred.request.get(url)
    return res.getContent() if res.isSuccess() else ''

  # Loads the page and parses the TOC
  def getTocOfPage(self, page, cached=True):
    data = alfred.cache.get(page)
    if cached and data:
      return True, data

    try:
      body = self.reqUrl(page)

      match = re.search(r'<div id="toc">(.*)<h2>Table of Contents</h2>(.*)<div id="apicontent">', body, flags=re.DOTALL)
      if not match:
          return False, 'parse page failed.'
      soup = BeautifulSoup(match.group(2))
    except Exception, e:
      return False, e.message

    data = []
    
    if not body:
      return alfred.exitWithFeedback(title='No results')


    for item in soup.ul.find_all('li'):

      try:
        obj = {}
        obj['name'] = item.select('a')[0].string.strip()
        obj['subtitle'] = item.select('a')[0].string.strip()
        obj['link'] = item.a['href'].strip()

      except Exception, e:
        continue

      data.append(obj)

    if cached and data:
      alfred.cache.set(page, data, CACHE_EXPIRE)
    return True, data

if __name__ == '__main__':
  App().run()
