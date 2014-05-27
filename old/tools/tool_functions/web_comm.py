import HTMLParser
from random import randrange
import re
import time
import urllib
import urllib2

import config


#################################################################################
#### Global var
default_ua = config.HEADERS['DEFAULT_UA']
user_agents = config.HEADERS['USER_AGENTS']
accept_language = config.HEADERS['ACCEPT-LANGUAGE']
google_prefix = config.SEARCH_SETTINGS['GOOGLE_PREFIX']
google_suffix = config.SEARCH_SETTINGS['GOOGLE_SUFFIX']
bing_prefix = config.SEARCH_SETTINGS['BING_PREFIX']
bing_suffix_1 = config.SEARCH_SETTINGS['BING_SUFFIX_1']
bing_suffix_2 = config.SEARCH_SETTINGS['BING_SUFFIX_2']
aol_trends_page = config.SEARCH_SETTINGS['AOL_HOT_TERMS']
result_links = []
result_terms = []


#################################################################################
#### Redirect Handler

class RedirectHandler(urllib2.HTTPRedirectHandler):
      
      def http_error_302(self, req, fp, code, msg, headers):
          infoURL = urllib.addinfourl(fp, headers, req.get_full_url())
          infoURL.status = code
          infoURL.code = code
          return infoURL

      http_error_300 = http_error_302
      http_error_301 = http_error_302
      http_error_303 = http_error_302
      http_error_307 = http_error_302

#opener = urllib2.build_opener(urllib2.HTTPHandler(debuglevel=1))
opener = urllib2.build_opener(RedirectHandler)
urllib2.install_opener(opener)


#################################################################################
#### HTML Parsers

# Recompile the HTMLParser attributes to be a little more relaxed about non standard characters
#   Added (White space separated list of characters/sequences): { }
HTMLParser.attrfind = re.compile(
    r'\s*([a-zA-Z_][-.:a-zA-Z_0-9]*)(\s*=\s*'
    r'(\'[^\']*\'|"[^"]*"|[-a-zA-Z0-9./,:;+*%?!&$\(\)_#=~@{}]*))?')

link_blacklist = [
  'http://g.msn.com',
  'microsoft.com',
  'r.msn.com',
  'webcache.googleusercontent.com',
  'feedback.discoverbing.com',
  ]

# This html parser overrides the handler for starting element tags. We only care about links right now.
#   Filter on <a> tags with 'href' attributes
class google_search_parser(HTMLParser.HTMLParser):
      
      def handle_starttag(self, tag, att):
          global result_links
          # If its a link
          if tag == 'a' and att[0][0] == 'href':
            # If it is a search result
            if att[0][1].startswith(r'/url?q='):
              # If it is not google cache content
              if att[0][1].find(r'webcache.googleusercontent') == -1:
                # Filter out the url from googles added 'stuff'
                linkPartitions = att[0][1].partition(r'http://')
                link = linkPartitions[1] + linkPartitions[2]
                # Filter out the google tracking stuff at the end of the url
                link = link.partition(r'&sa')[0]
                if link:
                  result_links.append(link)
                  result_links[-1] = urllib.unquote(result_links[-1])
                print result_links[-1]

class link_parser(HTMLParser.HTMLParser):

      def handle_starttag(self, tag, att):
          global result_links
          bad_link = False
          # If its a link
          if tag == 'a' and att[0][0] == 'href':
            if att[0][1].startswith('http'):
              for element in link_blacklist:
                if att[0][1].find(element) != -1:
                  bad_link = True
              if not bad_link:
                result_links.append(att[0][1])
                result_links[-1] = urllib.unquote(result_links[-1])
                print result_links[-1]

class google_news_parser(HTMLParser.HTMLParser):

      def handle_starttag(self, tag, att):
          # If its a link
          if tag == 'a':
            for name, value in att:
              if name == 'href':
                print value
                print self.get_starttag_text()

      def handle_decl(self, data):
          pass

      def unknown_decl(self, data):
          for line in data.split("\n"):
            if line.startswith("  <li"):
              line = line.split(">")
              line = line[3].rstrip(r"</a")
              search_terms.append(line)

class aol_trends_parser(HTMLParser.HTMLParser):
      
      def __init__(self):
          HTMLParser.HTMLParser.__init__(self)
          self.recording = False

      def unknown_decl(self, data):
          lines = data.lstrip('CDATA[\n\n').strip(' \n\r')
          if lines.startswith('<ol'):
            parser = aol_trends_parser()
            parser.feed(lines)

      def handle_decl(self, data):
          pass

      def handle_starttag(self, tag, att):
          if tag == 'ol':
            self.recording = True

      def handle_endtag(self, tag):
          if tag == 'ol':
            self.recording = False

      def handle_data(self, data):
          global result_terms
          if self.recording and data != '\n':
            if data not in result_terms:
              data = data.strip(' \n\r')
              if data:
                result_terms.append(data)


#################################################################################
#### HTTP Functions - open/request/download code

def open_URL(URL, guest=False, refer=False):
    URL = fix_URL(URL)
    random_int = randrange( len(user_agents) )
    try:
      request = urllib2.Request(URL)
      if not guest:
        request.add_header('User-Agent', user_agents[random_int])
      else:
        request.add_header('User-Agent', default_ua) 
      request.add_header('Accept-Language', accept_language)
      request.add_header('Accept-Encoding', 'identity')
      request.add_header('Host', URL.lstrip('http://').partition('/')[0])
      if refer:
        request.add_header('Referer', 'http://www.google.com')
    except Exception as error:
      print "ERROR open_URL request:",error
      print "    ",URL
      return
    try:
      opened_URL = urllib2.urlopen(request)
    except Exception as error:
      print "ERROR open_URL urlopen:",error
      print "    ",URL
      return
    return opened_URL

def get_HTML(URL, headers=False, guest=False):
    print 'GET HTML'
    opened_URL = open_URL(URL, guest, headers)
    if opened_URL:
      return opened_URL.read()


#################################################################################
#### Query Functions

def get_aol_terms(URL = aol_trends_page):
    global result_terms
    result_terms = []
    opened_HTML = get_HTML(URL, True)
    parser = aol_trends_parser()
    parser.feed(opened_HTML)
    return result_terms


#################################################################################
#### Search Engine Functions

# Return the links for n pages of a google search for a query
def google_search(queries, pages):
    print "GOOGLE SEARCH BEGIN"
    results = []
    for query in queries:
      start_at_result = 0
      for page in range(pages):
        print query,': pg',page
        time.sleep(30+randrange(30))
        URL = google_prefix + query.replace(' ','+') + google_suffix + '&start=' + str(start_at_result)
        print URL
        opened_HTML = get_HTML(URL)
        parser = google_search_parser()
        parser.feed(opened_HTML)
        #links = get_google_links(URL)
        #if links:
          #results += links
        start_at_result += 10
    #return results
    return result_links

def bing_search(queries, pages):
    print "BING SEARCH BEGIN"
    start_at_result = 0
    results = []
    for query in queries:
      for page in range(pages):
        print query,': pg',page
        time.sleep(30+randrange(30))
        URL = bing_prefix + query.replace(' ','+') + bing_suffix_1 + str(start_at_result) + bing_suffix_2
        #links = get_bing_links(URL)
        #if links:
          #results += links
        parser = link_parser()
        opened_HTML = get_HTML(URL)
        parser.feed(opened_HTML)
        start_at_result += 10
    #return results
    return result_links

def get_google_links(URL):
    results = []
    try:
      doc = get_HTML(URL)
      #doc = lxml.html.parse(URL).getroot()
    except Exception as error:
      print 'get_links parse error',error
      print '    ',URL
    else:
      for link in lxml.html.iterlinks(doc):
        if link [1] == 'href' and 'url?q=' in link[2]:
          if 'googleusercontent' not in link[2]:
            url = link[2].split('url?q=')[1].split('&')[0]
            url = urllib.unquote(url)
            if url not in results:
                results.append(url)
                print "    "+url
      return results

def get_bing_links(URL):
    results = []
    try:
      doc = get_HTML(URL)
    except Exception as error:
      print 'get_links parse error',error
      print '    ',URL
    else:
      for link in lxml.html.iterlinks(doc):
        if link [1] == 'href' and link[2].startswith('http://'):
            url = link[2]
            url = urllib.unquote(url)
            if url not in results:
                if not url.startswith('http://g.msn.com'):
                  if '.microsoft.com' not in url and '.r.msn' not in url:
                    results.append(url)
                    print "    "+url
      return results

#################################################################################
#### Page Scraper Functions

# Given one URL, this function will follow the redirects to the end of the 30* chain
def check_redirects(URL, guest=False):
    print 'CHECK REDIR.'
    ret_val = [ URL, ]
    print URL
    opened_URL = open_URL(URL, guest)
    if opened_URL:
      for header in opened_URL.info().headers:
        if header.startswith('Location'):
          redirected_URL = header[9:].strip(' \n\r')
          print redirected_URL
          ret_val.extend(check_redirects(redirected_URL, guest))
          break
    return ret_val

def get_iframes_links(URL):
    results = []
    try:
      html = get_HTML(URL)
      if html:
        tree = lxml.html.document_fromstring(html)
      else:
        return
    except Exception as error:
      print 'parse error',error
      print '    ',URL
    else:
      for element in tree.iter():
        if element.tag == 'iframe':
          attribs = dict(element.items())
          if 'style' in attribs:
            if 'visibility:hidden' in attribs['style']:
              if attribs['src'] and attribs['src'] != '#':
                if attribs['src'] not in results:
                  results.append(attribs['src'])
          if 'src' in attribs:
            if 'width' in attribs:
              if attribs['width'] < 10 or attribs['width'] == '':
                if attribs['src'] not in results:
                  results.append(attribs['src'])
            if 'height' in attribs:
              if attribs['height'] < 10 or attribs['height'] == '':
                if attribs['src'] not in results:
                  results.append(attribs['src'])
          if 'onload' in attribs:
            onload = attribs['onload']
            try:
              onload.split(';')
            except Exception as error:
              print 'onload parse error',error
            else:
              for line in onload:
                if 'src=' in line:
                  url = line.split('=')[1]
                  url.strip("'")
                  url.strip('"')
                  if url not in results:
                    results.append(url)
        if results:
          print "IFRAME Found\n    "
          results[-1] = urllib.unquote(results[-1])
          if not results[-1].startswith('http'):
            if 'www' in results[-1]:
              results[-1] = results[-1].partition('www')
              results[-1] = 'http://' + results[-1][1] + results[-1][2]
            else:
              results[-1] = URL + results[-1]
          print results[-1]
      return results


#################################################################################
#### Support Functions

def server_status(args=None):
    return True

# Adds the http:// prefix if necessary
def fix_URL(URL):
    if not URL.startswith(r'http'):
      URL = r'http://'+URL
    return URL
