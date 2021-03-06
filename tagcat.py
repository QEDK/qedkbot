#!/usr/bin/env python3
# GNU AFFERO GENERAL PUBLIC LICENSE Version 3, 19 November 2007 
# Copyright (c) 2020 QEDK
# A copy of the license is available at https://raw.githubusercontent.com/QEDK/qedkbot/master/LICENSE
import pywikibot
from pywikibot import Page
import toolforge
import requests
import re

toolforge.set_user_agent('qedkbot')
site = pywikibot.Site()
site.login()

checkpage = Page(site, "User:QEDKbot/Task 1 disable")
statuspage = Page(site, "User:QEDKbot/Task 1 status")


def emergency():
    if(checkpage.text != "true"):
        statuspage.text = "off"
        statuspage.save(summary="Task 1: tagging disabled.")
        print("Shutoff")
        exit(0)
    else:
        statuspage.text = "on"
        statuspage.save(summary="Task 1: tagging enabled.")


emergency()

S = requests.Session()
URL = "https://en.wikipedia.org/w/api.php"
emptycats = []
emptycatcomplete = 0
catcontinue = ""

while emptycatcomplete == 0:
    PARAMS = {
        "action": "query",
        "format": "json",
        "list": "allcategories",
        "aclimit": "max",
        "acmax": "0",
        "accontinue": catcontinue
    }
    R = S.get(url=URL, params=PARAMS)
    DATA = R.json()
    for catname in DATA['query']['allcategories']:
        emptycats.append("Category:"+catname['*'])
    if (DATA['batchcomplete'] != "''") and (len(DATA) == 4):
        catcontinue = DATA['continue']['accontinue']
    else:
        emptycatcomplete = 1
catcontinue = ""

reg = re.compile(r"(with\s+no\s+backlinks|-class|importance|needing|cf.*full|wikiproject|quality|unassessed|featured\s+topic)", flags=re.IGNORECASE)
rebot = re.compile(r"(\bbot|bot\b)", flags=re.IGNORECASE)
skip = {Page(site, "Template:Possibly empty category"), Page(site, "Template:Monthly clean-up category"), Page(site, "Template:Category disambiguation"), Page(site, "Template:Db-c1"), Page(site, "Template:Cfd full"), Page(site, "Template:Category class"), Page(site, "Template:Maintenance category autotag")}
log = Page(site, "User:QEDKbot/Catlog")
log.text = ""
for page in emptycats:
    try:
        cat = pywikibot.page.Category(site, page)
        if cat.exists() and cat.isEmptyCategory():
            if (any(template in cat.itertemplates() for template in skip)) or (reg.search(page+cat.text) is not None):
                continue
            elif cat.isCategoryRedirect():
                backlinkcount = len(list(cat.backlinks(total=2)))
                if(backlinkcount == 0) or ((backlinkcount == 1) and (cat.toggleTalkPage().exists())):
                    cat.text = cat.text + "\n[[Category:Empty categories with no backlinks]]"
                    cat.save(summary="Marking category as empty. Contact [[User talk:QEDK|operator]] if any bugs found.")
            else:
                cat.text = "{{Db-c1|bot=QEDKbot}}\n" + cat.text
                cat.save(summary="Nominating category for deletion ([[WP:CSD#C1]]). Contact [[User talk:QEDK|operator]] if any bugs found.")
                username = cat.oldest_revision.user
                if rebot.search(username) is None:
                    usertalk = Page(site, "User talk:" + username)
                    usertalk.text = usertalk.text + "\n{{subst:Db-catempty-notice|"+ page + "}}{{center|{{small|''This message was automatically delivered by [[User:QEDKbot|QEDKbot]]. ~~~~~''}}}}"
                    usertalk.save(summary="Notification for CSD-nominated category.")
                log.text += "* Nominating " + cat.title + " for deletion.\n"
                log.save(summary="Logging in userspace")
    except Exception as e:
        print(str(page), e)
    if((emptycats.index(page)+1) % 50 == 0):
        emergency()

if(statuspage.text == "on"):
    statuspage.text = "off"
    statuspage.save(summary="Disabling tagging till next run.")
    
print("Task is complete.")
exit(0)

