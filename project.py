import pygame
import json
from __main__ import *
import engine

data_dir = 'Data/'

print('Compiling databases...')

me_list = []
#me_list.append(pygame.mixer.Sound(me_dir + '0.wav'))
#me_list.append(pygame.mixer.Sound(me_dir + '1.wav'))

se_list = []


with open(data_dir + 'items.json') as json_data:
    items = json.load(json_data)
item_list = {}
for item in items['items']:
    new_item = engine.Item(item['name'],item['desc'],item['type'],item['price'],item['can_use'],item['effect'])
    item_list[new_item.name] = new_item
    print('New item, "' + new_item.name + '," with a type of ' + new_item.type + '.')

with open(data_dir + 'species.json') as json_data:
    mon_list = json.load(json_data)
x = 0
species_list = []
for mon in mon_list['species']:
    new_mon = engine.MonSpecies(mon['name'],mon['stats'],mon['learnset'],mon['evolution'],mon['gender_ratio'],int(mon['catch_rate']))
    print('New mon, "' + new_mon.name + '," with an id of ' + str(x))
    species_list.append(new_mon)
    x += 1
del x
del mon_list

str_list = []
try:
    with open(data_dir + 'text.json') as json_data:
        raw_text_list = json.load(json_data)
    str_list = raw_text_list['texts']
    del raw_text_list
    print(str_list['success'])
except:
    print('Something went wrong while compiling text...')

print('Databases loaded...')