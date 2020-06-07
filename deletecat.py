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

reg = re.compile(r"(with no backlinks|.*-class|needing|cf. full|wikiproject)", flags=re.IGNORECASE)
skip = {Page(site, "Template:Possibly empty category"), Page(site, "Template:Monthly clean-up category"), Page(site, "Template:Category disambiguation"), Page(site, "Template:Db-c1"), Page(site, "Template:Cfd full"), Page(site, "Template:Category class")}
for page in emptycats:
	try:
		cat = pywikibot.page.Category(site, page)
		if cat.exists() and cat.isEmptyCategory():
			if (any(template in cat.itertemplates() for template in skip)) or (reg.search(page+cat.text) is not None):
				continue
			elif cat.isCategoryRedirect():
				backlinkcount = len(list(cat.backlinks(total=2)))
				if(backlinkcount == 0) or ((backlinkcount == 1) and (cat.toggleTalkPage().exists())):
					editsummary = "Marking category as empty."
					cat.text = cat.text+"\n[[Category:Empty categories with no backlinks]]"
			else:
				cat.text = "{{Db-c1|bot=QEDKbot}}\n"+cat.text
				editsummary = "Nominating category for deletion ([[WP:CSD#C1]])."
			cat.save(summary=editsummary+" Contact [[User talk:QEDK|operator]] if any bugs found.")
	except Exception as e:
		print(str(page), e)
	if((emptycats.index(page)+1) % 50 == 0):
		emergency()

if(statuspage.text == "on"):
	statuspage.text = "off"
	statuspage.save(summary="Disabling tagging till next run.")

print("Task is complete.")
exit(0)
