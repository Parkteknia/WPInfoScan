import os.path
import sys
import time
import argparse
import gettext, locale
import json
import requests
import re
from pathlib import Path
from lib.headers import header
from lib.colors import colors
from lib.stats import basic_stats as stats

currentDir = os.path.dirname(os.path.realpath(__file__)) + os.path.sep

clean_domains = []

locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')

langs = ["es_ES", "en_US"]

t = gettext.translation('wpis', 
                        'locale',
                        languages=langs,
                        fallback=True)
_ = t.gettext

def _doSimpleHTTPRequest(url):
    headers = header()
    try:
        response = requests.get(url, headers=headers)
        return response.text
    except requests.exceptions.RequestException as e:
        return False
    return True

def _readWebPage(url):
    headers=header()
    response = requests.get(url, headers=headers)
    time.sleep(1) 
    if response.status_code == 200:
        time.sleep(1)
        print("\t",colors.reset, _("Request parsed:"), colors.fg.orange, f'{url}', colors.reset)
        return response.text
    else:
        print("\t",colors.bg.red, _("Request error:"), colors.reset, colors.fg.orange, f'{url}', colors.reset, _("(status code:%s)") % response.status_code)
        return False

def _isValidFile(conf_file):
    if not os.path.exists(conf_file):
        print(colors.bg.red, _("The file %s does not exist!") % conf_file,colors.reset)
        return False
    else:
        return True  # return an open file handle

def _isValidDomainName(domain):
    
    regex = "^((?!-)[A-Za-z0-9-]" + "{1,63}(?<!-)\\.)" +"+[A-Za-z]{2,6}"
    p = re.compile(regex)
    
    if (domain == None):
        return False
    if(re.search(p, domain)):
        return True
    else:
        return False

def _isWPDomainName(page):
    t = re.compile(r"wp-content(?:\\\/|\/)\/?")
    wp = re.findall(t, page)
    if not wp:
        return False
    return True

def _isOnlineDomainName(url):
    return _doSimpleHTTPRequest(url)

def _isDomainName(domain):
    
    if not _isValidDomainName(domain):
        print(colors.bg.red, _("Domain name %s is invalid!") % domain, colors.reset)
        return False
        
    homepage = _isOnlineDomainName("https://" + domain + "/")
    
    if not homepage:
        print(colors.bg.red, _("It appears that domain name %s does not exist!") % domain, colors.reset)
        return False
        
    if not _isWPDomainName(homepage):
        print(colors.bg.red, _("Domain name %s does not contain a WP installation!") % domain, colors.reset)
        return False

    return True

def _loadConfig(cnf_file):
    print(colors.fg.cyan, _("Loading..."), colors.reset)
    data = json.load(open(cnf_file, 'r'))
    if data:
        print(colors.fg.cyan, _("Loaded config:"), colors.reset, f"{cnf_file}")
        return data
    return False

def _validateDataConfig(data, cnf_errors):
    
    print(colors.fg.cyan, _("Validating config data..."), colors.reset)
    
    validated_errors = True
    domains = []
    
    for host in data['hosts']:
        
        host['errors'] = []
        
        if not _isValidDomainName(host['domain']):
            host['errors'].append(_("invalid"))
            validated_errors = False   
        
        if not _isOnlineDomainName("https://" + host['domain'] + "/"):
            host['errors'].append(_("offline"))
            validated_errors = False 
            
        domains.append(host)
        
    return {"valid": validated_errors, "domains": domains}

def _prepareURLs(client):
    client_urls = []
    for url in client['url_names']:
        if url != "/":
            url_path = "https://" + client['domain'] + "/"+url+"/"
        else:
            url_path = "https://" + client['domain'] + "/"
        client_urls.append(url_path)
    return client_urls

def _getClientObj(domain, urls):
    client = {}
    client['domain'] = domain
    client['url_names'] = ["/"] + urls
    client['urls'] = _prepareURLs(client)
    return client

def _extractWPData(client):
    all_plugins = []
    all_themes = []
    for url in client['urls']:
        web_data = _readWebPage(url)
        if web_data:
            p = re.compile(r"wp-content(?:\\\/|\/)plugins(?:\\\/|\/)([a-zA-Z0-9_-]+)\/?")
            plugins = re.findall(p, web_data)
            if plugins:
                for plugin in plugins:
                    if plugin not in all_plugins:
                        all_plugins.append(plugin)
            t = re.compile(r"wp-content(?:\\\/|\/)themes(?:\\\/|\/)([a-zA-Z0-9_-]+)\/?")
            themes = re.findall(t, web_data)
            if themes:
                for theme in themes:
                    if theme not in all_themes:
                        all_themes.append(theme)
    client['plugins'] = all_plugins
    client['themes']  = all_themes
    return client

def _saveJSON(data):
    with open('data.json', 'w') as f:
        json.dump(data, f)

def _readJSON(data_file):
    f = open(data_file)
    data = json.load(f)
    return data

def scan(client):
    print(colors.reset, "------------------------------------------", colors.reset)
    print(colors.fg.cyan, _("Analyzing domain:"), colors.reset, f"{client['domain']}")
    client = _extractWPData(client)
    if client['plugins']:
        print(colors.fg.cyan, "Plugins ("+str(len(client['plugins'])) + "):", colors.reset)
        for plugin in client['plugins']:
            print(f"\t- {plugin}")
    else:
        print(colors.bg.red, _("This Wordpress installation appears to contain no plugins"), colors.reset)
    if client['themes']:
        print(colors.fg.cyan, "Theme:", colors.reset)
        for theme in client['themes']:
            print(f"\t- {theme}")
    else:
        print(colors.bg.red, _("This Wordpress installation appears to contain no themes"), colors.reset)

def _main():
    config_choices = ['default', 'custom', 'stats']
    config_errors  = ['stop', 'force']
    config_outputs = ['json']
    argParser = argparse.ArgumentParser(description=_("Scan any Wordpress powered website and try to identify plugins and themes installed"),formatter_class=argparse.RawTextHelpFormatter)
    argParser.add_argument('-c', '--config',
                           choices = config_choices,
                           dest='cnf',
                           default = config_choices[0],
                           help=_("Choose <default> config (to pass a domain and urls),\n"
                               "<custom> (to load your own conf.json file) or\n"
                               "<stats> (to see last data.json scan stats).\n"
                               "<default, custom or stats>"),
                           required=True)
    argParser.add_argument('-e', '--errors',
                           choices = config_errors,
                           dest='cnfe',
                           default = config_errors[0],
                           help=_("Select what to do if there is an error during the scan <stop or force>"),
                           required=False)
    argParser.add_argument('-o', '--output',
                           choices = config_outputs,
                           dest='cnfo',
                           default = None,
                           help=_("Save scan results to a <json> file"),
                           required=False)
    argParser.add_argument('-s', '--scan',
                           metavar='<website url>',
                           dest='url',
                           help=_('Scan website at <website url>'))

    if True in list(map(lambda x: config_choices[0] in x, sys.argv)):
        argParser.add_argument('-d', "--domain",
                            metavar='<domain name>',
                            dest='domain',
                            help=_('Enter a domain name <domain.name>'),
                            required = True)
        argParser.add_argument('-u', '--urls',
                            metavar='<list urls>',
                            dest='urls',
                            help=_('Comma separated list of urls'),
                            type=lambda t: [s.strip() for s in t.split(',')],
                            required=True)

    if True in list(map(lambda x: config_choices[1] in x or config_choices[2] in x, sys.argv)):
        argParser.add_argument('-f', "--file",
                            metavar='<config file>',
                            dest='cnf_file',
                            help=_('Enter a configuration file.json <config file>'),
                            required = True)

    args = argParser.parse_args()
    
    print("\n", colors.bg.green, colors.fg.black, "WP-INFO-SCAN ", colors.reset)  
    
    try:
        if args.cnf == None:
            argParser.print_help()
        elif args.cnf == "default":
            print(colors.fg.cyan, _("Starting a 'default' WP-INFO-SCAN "), colors.reset)
            if _isDomainName(args.domain):
                scan(_getClientObj(args.domain, args.urls))
        elif args.cnf == "custom":
            print(colors.fg.cyan, _("Starting a 'custom' WP-INFO-SCAN "), colors.reset)
            if _isValidFile(args.cnf_file):
                config_data = _loadConfig(args.cnf_file)
                if config_data:
                    config_result = _validateDataConfig(config_data, args.cnfe)
                    if not config_result['valid']:
                        print(colors.bg.red, _("Config Error: Invalid or inaccessible domain names!"), colors.reset)
                        print(colors.fg.red, "------------------------------------------", colors.reset)
                        
                        for domain in config_result['domains']:
                            if domain['errors']:
                                print(colors.reset, colors.fg.orange, _("%s") % domain['domain'], colors.reset, _("contains errors:"), colors.reset, domain['errors'], colors.reset)
                                print(colors.fg.red, "------------------------------------------", colors.reset)
                        
                        if args.cnfe == "stop":
                            
                            print(colors.bg.red, _("Scanning stopped due to errors. Use the [-e force] option to bypass errors or fix your configuration file."), colors.reset)
                            
                        elif args.cnfe == "force":
                            print(colors.fg.cyan, _("Scanning: (%d domains)") % len(config_result['domains']), colors.reset)
                            for domain in config_result['domains']:
                                if not domain['errors']:
                                    print(colors.fg.cyan, _("Starting scan at:"), colors.reset, domain['domain'])
                                    client = _getClientObj(domain['domain'], domain['paths'])
                                    homepage = _isOnlineDomainName(client['urls'][0])
                                    if homepage:
                                        if not _isWPDomainName(homepage):
                                            print(colors.bg.red, _("Invalid Wordpress installation"), colors.reset)
                                            print(colors.fg.red, "------------------------------------------")
                                            print (colors.reset, _("The domain name:"), colors.fg.orange, f'{domain["host"]}', colors.reset, _("does not appear to contain a Wordpress installation."))
                                            print(colors.fg.red, "------------------------------------------", colors.reset)
                                        else:
                                            clean_domains.append(client)
                                            scan(client)
                            stats(clean_domains)
                        else:
                            print(colors.bg.red, _("The '-e argument' option is not correct"), colors.reset)
                        if args.cnfo:
                            if args.cnfo == "json":
                                _saveJSON(clean_domains)
                    else:
                        print(colors.fg.cyan, _("Scanning: (%d domains)") % len(config_result['domains']), colors.reset)
                        for domain in config_result['domains']:
                            client = _getClientObj(domain['domain'], domain['paths'])
                            clean_domains.append(client)
                            scan(client)
                        stats(clean_domains)
                        if args.cnfo:
                            if args.cnfo == "json":
                                _saveJSON(clean_domains)
        elif args.cnf == "stats":
            print(colors.fg.cyan, _("Showing stats from last WP-INFO-SCAN "), colors.reset)
            if _isValidFile(args.cnf_file):
                domains = _readJSON(args.cnf_file)
                stats(domains)
        else:
            update(args.pageN)
    except IOError as e:
        print(e)

if __name__ == "__main__": _main()
