import os,json
from operator import itemgetter
from .table import pretty_print_table as table
from .colors import colors

def basic_stats(data):
    
    all_plugs = {}
    all_themes = {}
    count_domains = 0

    for domain in data:
        count_domains +=1
        for plug in domain['plugins']:
            if plug not in all_plugs:
                all_plugs[plug] = 1
            else:
                all_plugs[plug] += 1
        for theme in domain['themes']:
            if theme not in all_themes:
                all_themes[theme] = 1
            else:
                all_themes[theme] += 1

    plugs = []
    for plug in all_plugs:
        p = []
        p.append(plug)
        p.append(all_plugs[plug])
        p.append(round(all_plugs[plug]*100/count_domains,2))
        plugs.append(p)
    plugs = sorted(plugs, key=itemgetter(2), reverse=True)
    plugs.insert(0,["Plugin", "Total", "%", ])
    print(colors.fg.cyan, "Plugins stats for:", colors.reset, f"({count_domains} domains)")
    table(plugs)
    
    themes = []
    for theme in all_themes:
        t = []
        t.append(theme)
        t.append(all_themes[theme])
        t.append(round(all_themes[theme]*100/count_domains,2))
        themes.append(t)
    themes = sorted(themes, key=itemgetter(2), reverse=True)
    themes.insert(0,["Theme", "Total", "%", ])
    print(colors.fg.cyan, "Themes stats for:", colors.reset, f"({count_domains} domains)")
    table(themes)
