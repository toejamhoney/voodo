#!/usr/bin/python
#vim: set fileencoding=utf-8 :

# Note that ip addresses are strings, ports are ints
SETTINGS = {
    'AVD_DIR' : '/Users/honey/.android/avd',
    'VOODO_DIR' : '/Users/honey/Documents/honeyShared/voodo',
    'ISO_DIR' : '/Volumes/Macintosh_HD_3/voodo_iso',
    'LOG_DIR' : '/Volumes/Macintosh_HD_2/voodo_logs',
    'PIN_DIR' : 'c:\\pin-56759\\source\\tools\\ManualExamples\\obj-ia32',
    'PIN_TOOLS_DIR' : 'c:\\Documents and Settings\\source\\tools\\SimpleExamples\\obj-ia32',
    'PIN_BAT_DIR' : 'c:\\Documents and Settings\\',
    'MALWARE_DEST' : 'C:\\malware',
    'HOST_ADDR' : '10.3.3.1',
    'LAN_NETWORK': '10.0.0.',
    'LAN_GATEWAY': '10.0.0.1',
    'GATEWAY_NICS' : ['10.3.3.2', '10.0.0.1', '10.0.2.15'],
    'PROXY_PORT' : 4827,
    'VOODO_PORT' : 4828,
    'DEFAULT_VM' : 'test7a',
}

GUESTS = {
    # Gateways
    'cent64_a': { 'address' : '10.3.3.2', },
    'cent64_b': { 'address' : '10.3.3.3', },
    'cent64_c': { 'address' : '10.3.3.4', },
    'cent64_d': { 'address' : '10.3.3.5', },
    'cent64_e': { 'address' : '10.3.3.6', },
    # Honey(Clients/Pots/Net)
    'xp01': { 'address' : '10.3.3.101',
               #'gateway' : 'cent64_a'
             },
    'xp02': { 'address' : '10.3.3.102',
               #'gateway' : 'cent64_b'
             },
    'xp03': { 'address' : '10.3.3.103',
               #'gateway' : 'cent64_c'
             },
    'xp04': { 'address' : '10.0.0.104',
               'gateway' : 'cent64_d'
             },
    'xp05': { 'address' : '10.0.0.105',
               'gateway' : 'cent64_e'
             },
    'test7a': { 'address' : '10.0.0.199',
               'gateway' : 'cent64_a',
               'nics' : { '0': 'Local Area Connection', '1': 'Local Area Connection 2' },
               #'address' : '10.0.0.199',
               #'gateway' : 'cent64_a',
             },
    'test7b': { 'address' : '10.3.3.11',
               'nics' : { '0': 'Local Area Connection' },
               #'address' : '10.0.0.198',
               #'gateway' : 'cent64_b'
             },
    'winxp' : { 'address' : '10.3.3.12', },
    'win7_a' : { 'address' : '10.3.3.13', },
    'win7_b' : { 'address' : '10.3.3.14', },
    'win7_c' : { 'address' : '10.3.3.15', },
}

ANALYZER_CMDS = {
    # id : (before cmd, after cmd, cleanup)
    # None in a cmd will mean pass the begin(), or kill the PID on end()
    # before cmd = run before application, after cmd = run after
    # cleanup is any command that should be run post analysis like pulling
    # a log file
    'tcpdump': ('/usr/sbin/tcpdump -ennSvXXs 1514 -i eth1 -w $LOG_FILE',
                '$KILL',
                None),
     'logcat': ('$ADB logcat -c',
                '$ADB logcat -d -f /sdcard/logcat.txt ActivityManager:I *:S',
                '$ADB pull /sdcard/logcat.txt $LOG_FILE'),
}

HEADERS = {
    'DEFAULT_UA' : r'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',# SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729)',
    'USER_AGENTS' : [
                   'Mozilla/5.0 (Windows NT 5.1; rv:2.0) Gecko/20100101 Firefox/4.0',
                   'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Win64; x64; Trident/6.0)',
                   'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0; Xbox)',
                   'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)a',
                   'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; chromeframe/13.0.782.218; chromeframe; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648; .NET CLR 3.5.21022; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)',
                   'Mozilla/4.0 (compatible; MSIE 6.0; Windows 98; Rogers Hi-Speed Internet; (R1 1.3))a',
                   'Opera/9.80 (Android 2.3.5; Linux; Opera Mobi/ADR-1111101157; U; de) Presto/2.9.201 Version/11.50',
                   'Opera/9.80 (Windows Mobile; WCE; Opera Mobi/WMD-50433; U; en) Presto/2.4.13 Version/10.00',
                   'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.874.121 Safari/535.2',
                   'Mozilla/5.0 (Windows NT 6.0; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.186 Safari/535.1',
                   'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.75 Safari/537.1',
                   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/536.26.17 (KHTML, like Gecko) Version/6.0.2 Safari/536.26.17',
                   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2',
                   'Mozilla/5.0 (iPod; U; CPU iPhone OS 4_0 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7'
                   ],
    'ACCEPT-LANGUAGE' : 'en-US,en;q=0.5',
}

SEARCH_SETTINGS = {
    'GOOGLE_PREFIX' : r'http://www.google.com/search?q=',
    'GOOGLE_SUFFIX' : r'&site=webhp&source=hp&btnG=Search&hl=en&biw=&bih=&gbv=1',
     'BING_PREFIX' : r"http://www.bing.com/search?q=",
    'BING_SUFFIX_1' : r"&first=",
    'BING_SUFFIX_2' : r"&FORM=PERE",
     'GOOGLE_NEWS' : r'http://news.google.com/nwshp?hl=en&tab=nn',
    'GOOGLE_TRENDS' : r'http://www.google.com/trends/hottrends/atom/hourly',
    'AOL_HOT_TERMS' : r'http://search.aol.com/aol/trends',
}
