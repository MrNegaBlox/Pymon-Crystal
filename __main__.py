music_dir = 'Music/'
me_dir = 'ME/'
sound_dir = 'Sounds/'
map_dir = 'Maps/'
spr_dir = 'Sprites/'
ui_dir = 'UI/'
script_dir = 'EventScripts/'

import random
import pickle
import io
import gc
gc.get_stats()
import pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=4, buffer=40960)
music = pygame.mixer.music
pygame.font.init()
Time = pygame.time
clock = pygame.time.Clock()

import pygame.midi
pygame.midi.init()

import math
import time
from time import time
import engine
import project
from pytmx.util_pygame import load_pygame
import datetime
import os

import types
import asyncio
from import_file import import_file

game_title = ''
# game_icon = pygame.image.load('icon.png')

red = (255, 0, 0)
blue = (0, 0, 255)
green = (0, 255, 0)
yellow = (255, 255, 0)
white = (255, 255, 255)
black = (0, 0, 0)

display_width = 320
display_height = 288

resolution_factor = 2

block_size = 32

fps = 30

KEY_A = False
KEY_A_DOWN = False
KEY_B = False
KEY_START = False
KEY_UP = False
KEY_DOWN = False
KEY_LEFT = False
KEY_RIGHT = False
KEY_CODE = False

DIR_LEFT = 0
DIR_RIGHT = 1
DIR_UP = 2
DIR_DOWN = 3

map = None

song = None

print('Setting up...')


class SystemTime:
    def get_hour(self) -> int:
        return datetime.datetime.now().hour

    def get_minute(self) -> int:
        return datetime.datetime.now().minute

    def get_weekday(self) -> str:
        daynum = datetime.datetime.now().weekday()
        if daynum == 6:
            return "SUNDAY"
        if daynum == 0:
            return "MONDAY"
        if daynum == 1:
            return "TUESDAY"
        if daynum == 2:
            return "WEDNESDAY"
        if daynum == 3:
            return "THURSDAY"
        if daynum == 4:
            return "FRIDAY"
        if daynum == 5:
            return "SATURDAY"

    def get_time_of_day(self) -> str:
        if self.get_hour() >= 6 and self.get_hour() < 10:
            return "Morning"
        elif self.get_hour() >= 10 and self.get_hour() < 18:
            return "Day"
        else:
            return "Night"

systime = SystemTime()


class Map:
    def __init__(self, map_):
        self.map = map_
        if 'name' in map_.properties:
            self.name = map_.properties['name']
        else:
            self.name = ""
        self.width = map_.width
        self.height = map_.height
        self.properties = map_.properties
        if self.name not in gameData.map_flags:
            gameData.map_flags[self.name] = []
            map_flag_amount = 16
            if "map_flag_amount" in map_.properties:
                map_flag_amount = int(map_.properties['map_flag_amount'])
            if map_flag_amount > 0:
                for x in range(map_flag_amount):
                    gameData.map_flags[self.name].append(False)
        if self.name not in gameData.map_vars:
            gameData.map_vars[self.name] = []
            map_var_amount = 0
            if "map_var_amount" in map_.properties:
                map_var_amount = int(map_.properties['map_var_amount'])
            if map_var_amount > 0:
                for x in range(map_var_amount):
                    gameData.map_vars[self.name].append(0.0)
        if 'region_number' in map_.properties:
            self.region = int(map_.properties['region_number'])
        else:
            self.region = 0
        if 'region_x' in map_.properties:
            self.region_x = int(map_.properties['region_x'])
        else:
            self.region_x = 0
        if 'region_y' in map_.properties:
            self.region_y = int(map_.properties['region_y'])
        else:
            self.region_y = 0
        self.connections = {}
        self.obj_list = []
        self.animated_tiles = []
        self.tileimages = []
        self.surface = None
        self.load_tile_data()
        self.events = self.map.get_layer_by_name("Events")
        self.load_obj_data()
        self.load_map_connections()
        self.load_map_border()
        global song
#        if 'music' in map_.properties:
#            if song is None:
#                music.load(music_dir + map_.properties['music'])
#                music.play(-1,0)
#                song = map_.properties['music']
#            if map_.properties['music'] != song:
#                music.fadeout(1)
#                music.load(music_dir + map_.properties['music'])
#                music.play(-1,0)
#                song = map_.properties['music']

    def load_tile_data(self):
        for y in range(self.map.height):
            for x in range(self.map.width):
                image_list = []
                props = self.map.get_tile_properties(x,y,0)
                if props is not None:
                    if 'frames' in props:
                        if len(props['frames']) > 1:
                            for animation_frame in props['frames']:
                                d = animation_frame.duration
                                i = animation_frame.gid
                                image_list.append(i)
                            animtile = AnimatedTile((x*block_size,y*block_size), image_list)
                            self.animated_tiles.append(animtile)
        for y in range(self.map.height):
            for x in range(self.map.width):
                image = self.map.get_tile_image(x, y, 0)
                self.tileimages.append((x, y, image))
        self.surface = pygame.Surface((self.width * block_size,self.height * block_size))
        for x,y,image in self.tileimages:
            self.surface.blit(image, (x * block_size, y * block_size))

    def load_obj_data(self):
        for obj in self.events:
            if obj.type == "NPC":
                if 'char_image' in obj.properties:
                    mv_pat = engine.mv_pattern_stationary
                    if 'move_type' in obj.properties:
                        if obj.properties['move_type'] == 'stationary':
                            mv_pat = engine.mv_pattern_stationary
                        elif obj.properties['move_type'] == 'walk':
                            mv_pat = engine.mv_pattern_walk
                        elif obj.properties['move_type'] == 'look':
                            mv_pat = engine.mv_pattern_look
                    npc = NPC(obj.x, obj.y, obj.properties, obj.properties['char_image'], mv_pat)
                else:
                    npc = NPC(obj.x, obj.y, obj.properties)
                self.obj_list.append(npc)
            elif obj.type == "signpost":
                sign = Signpost(obj.x, obj.y, obj.properties['text'])
                self.obj_list.append(sign)
            elif obj.type == "door":
                door = Door(obj.x, obj.y, obj.properties['dest_map'], float(obj.properties['dest_x']), float(obj.properties['dest_y']), obj.properties['warp_type'])
                self.obj_list.append(door)
            elif obj.type == "trigger_step":
                if 'behavior' in obj.properties:
                    trigger = StepTrigger(obj.x, obj.y,obj.width,obj.height,obj.properties['behavior'])
                else:
                    trigger = None
                self.obj_list.append(trigger)

    def load_map_border(self):
        self.tile_border_img = pygame.Surface((64,64))
        images = []
        for y in range(2):
            for x in range(2):
                image = self.map.get_tile_image(x, y, 1)
                images.append((x, y, image))
        for x,y,image in images:
            self.tile_border_img.blit(image,(x * block_size, y * block_size))
        self.map_base = pygame.Surface((64 * (self.map.width + 2),64 * (self.map.height + 2)))
        x = -64 * 2
        while x < 64 * (self.map.width + 2):
            y = -64 * 2
            while y < 64 * (self.map.height + 2):
                self.map_base.blit(self.tile_border_img, (x, y))
                y += 64
            x += 64

    def load_map_connections(self):
        c_left_offset = 0
        c_right_offset = 0
        c_up_offset = 0
        c_down_offset = 0
        if 'connection_left' in self.map.properties:
            c_left_map = load_pygame(map_dir + self.map.properties['connection_left'] + ".tmx")
            if 'outside' in c_left_map.properties:
                if c_left_map.properties['outside'] == "true":
                    if systime.get_time_of_day() == "Night":
                        print("It's night.")
                        c_left_map.tilesets[0].source = "../Tilesets/GSC overworld johto nite.png"
                        c_left_map.reload_images()
            if 'c_left_offset' in self.map.properties:
                c_left_offset = int(self.map.properties['c_left_offset'])
            connection_left = MapConnection(c_left_map, DIR_LEFT, c_left_offset)
            self.connections['left'] = connection_left
        if 'connection_right' in self.map.properties:
            c_right_map = load_pygame(map_dir + self.map.properties['connection_right'] + ".tmx")
            if 'outside' in c_right_map.properties:
                if c_right_map.properties['outside'] == "true":
                    if systime.get_time_of_day() == "Night":
                        print("It's night.")
                        c_right_map.tilesets[0].source = "../Tilesets/GSC overworld johto nite.png"
                        c_right_map.reload_images()
            if 'c_right_offset' in self.map.properties:
                c_right_offset = int(self.map.properties['c_right_offset'])
            connection_right = MapConnection(c_right_map, DIR_RIGHT, c_right_offset)
            self.connections['right'] = connection_right
        if 'connection_up' in self.map.properties:
            c_up_map = load_pygame(map_dir + self.map.properties['connection_up'] + ".tmx")
            if 'outside' in c_up_map.properties:
                if c_up_map.properties['outside'] == "true":
                    if systime.get_time_of_day() == "Night":
                        print("It's night.")
                        c_up_map.tilesets[0].source = "../Tilesets/GSC overworld johto nite.png"
                        c_up_map.reload_images()
            if 'c_up_offset' in self.map.properties:
                c_up_offset = int(self.map.properties['c_up_offset'])
            connection_up = MapConnection(c_up_map, DIR_UP, c_up_offset)
            self.connections['up'] = connection_up
        if 'connection_down' in self.map.properties:
            c_down_map = load_pygame(map_dir + self.map.properties['connection_down'] + ".tmx")
            if 'c_down_offset' in self.map.properties:
                c_down_offset = int(self.map.properties['c_down_offset'])
            connection_down = MapConnection(c_down_map, DIR_UP, c_down_offset)
            self.connections['up'] = connection_down

    def draw(self):
        gameDisplay.blit(self.surface, (- cam.x,- cam.y))
        for tile in map.animated_tiles:
            tile.draw()


class MapConnection():
    def __init__(self, map, direction, offset):
        self.map = map
        self.width = map.width
        self.height = map.height
        self.offset = offset
        self.direction = direction
        self.images = []
        self.surface = None
        self.load_tiles()

    def load_tiles(self):
        for y in range(self.height):
            for x in range(self.width):
                image = self.map.get_tile_image(x, y, 0)
                self.images.append((x, y, image))
        self.surface = pygame.Surface((self.width * block_size,self.height * block_size))
        for x,y,image in self.images:
            self.surface.blit(image, (x * block_size, y * block_size))

    def draw(self):
        if self.direction == DIR_LEFT:
            if 'left' in map.connections:
                gameDisplay.blit(self.surface, ((-self.width * block_size)-cam.x,(self.offset * block_size)-cam.y))
        elif self.direction == DIR_RIGHT:
            if 'right' in map.connections:
                gameDisplay.blit(self.surface, ((map.width * block_size)-cam.x,(self.offset * block_size)-cam.y))
        if self.direction == DIR_UP:
            if 'up' in map.connections:
                gameDisplay.blit(self.surface, ((self.offset * block_size)-cam.x,(-self.height * block_size)-cam.y))
        if self.direction == DIR_DOWN:
            if 'down' in map.connections:
                gameDisplay.blit(self.surface, ((self.offset * block_size)-cam.x,(map.height * block_size)-cam.y))


class GameData:
    def __init__(self):
        self.vars = []
        for x in range(100):
            self.vars.append(0)
        self.flags = []
        for x in range(100):
            self.flags.append(False)
        self.map_flags = dict()
        self.map_vars = dict()


class SaveData:
    def __init__(self):
        self.player = player.data
        self.game = gameData

    def sync(self):
        self.player = player.data
        self.game = gameData
        self.player_x = player.x
        self.player_y = player.y
        self.player_map = map
        self.player_dir = player.dir

    def export_(self,file_path):
        loop.run_until_complete(engine.save_game_async(self, file_path))

    def import_(self,file_path):
        global save
        save = loop.run_until_complete(engine.load_game_async(self, file_path))
        del self


class AnimatedTile:
    def __init__(self, loc, images):
        #print('new tile at ',loc[0],' ',loc[1])
        self.x = loc[0]
        self.y = loc[1]
        self.gidlist = images
        self.images = []
        for gid in self.gidlist:
            self.images.append(dmap.get_tile_image_by_gid(gid))
        self.frame = 0
        self.pause = 2
        self.max_frame = len(images) - 1

    def draw(self):
        self.pause -= 1
        if self.pause <= 0:
            if self.frame == self.max_frame:
                self.frame = 0
            else:
                self.frame += 1
            self.pause = 2
        gameDisplay.blit(self.images[self.frame],(self.x - cam.x, self.y - cam.y))


class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.center_on_player = True
        self.width = display_width
        self.height = display_height

    def realign(self):
        self.x = (((player.x - (display_width / 2)) / 32.0) * 32.0) + 32
        self.y = (((player.y - (display_height / 2)) / 32.0) * 32.0) + 16

    def set_pos(self, x=0, y=0):
        self.x = x
        self.y = y

    def draw(self):
        gameDisplay.blit(map.map_base, ((-64*3)-cam.x, (-64*3)-cam.y))


class ScreenCover:
    def __init__(self):
        self.type = 'cover'
        self.color = white
        self.visible = False

    def update(self):
        pass

    def draw(self):
        if self.visible:
            color_alpha = (self.color[0],self.color[1],self.color[2], 128)
            pygame.draw.rect(gameDisplay, color_alpha,(0,0,display_width,display_height))


class Player:
    def __init__(self):
        self.data = engine.PlayerData()
        self.layer = 0
        self.x = block_size * 10
        self.y = block_size * 8
        if self.data.on_bike:
            self.move_speed = 8
        else:
            self.move_speed = 4
        self.dir = DIR_DOWN
        self.dest_x = self.x
        self.dest_y = self.y
        self.isMoving = False
        self.isBusy = False
        self.step = 0
        self.m = 0
        self.spr_f = pygame.image.load('Player/Male/Gold.png')
        self.spr_down = pygame.transform.chop(pygame.transform.chop(self.spr_f, (32,0,0,0)), (32,32,128,128))
        self.spr_down_s0 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0,0,32,0)), (32,32,128,128))
        self.spr_down_s1 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0,0,96,0)), (32,32,128,128))
        self.spr_left = pygame.transform.chop(pygame.transform.chop(self.spr_f, (32,0,0,32)), (32,32,128,128))
        self.spr_left_s0 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0,0,32,32)), (32, 32, 128, 128))
        self.spr_left_s1 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0,0,96,32)), (32, 32, 128, 128))
        self.spr_right = pygame.transform.chop(pygame.transform.chop(self.spr_f, (32,0,0,64)), (32,32,128,128))
        self.spr_right_s0 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0,0,32,64)), (32, 32, 128, 128))
        self.spr_right_s1 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0,0,96,64)), (32, 32, 128, 128))
        self.spr_up = pygame.transform.chop(pygame.transform.chop(self.spr_f, (32,0,0,96)), (32,32,128,128))
        self.spr_up_s0 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0, 0,32,96)), (32,32,128,128))
        self.spr_up_s1 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0, 0,96,96)), (32,32,128,128))
        self.sprite = self.spr_left_s0
        self.update_image()

    def update_image(self):
        if self.data.isGirl:
            if self.data.on_bike:
                self.spr_f = pygame.image.load('Player/Female/Crystal-onbike.png')
            else:
                self.spr_f = pygame.image.load('Player/Female/Crystal.png')
        else:
            if self.data.on_bike:
                self.spr_f = pygame.image.load('Player/Male/Gold-onbike.png')
            else:
                self.spr_f = pygame.image.load('Player/Male/Gold.png')
        if self.data.surfing:
            self.spr_f = pygame.image.load('Player/surf.png')
        self.spr_down = pygame.transform.chop(pygame.transform.chop(self.spr_f, (32,0,0,0)), (32,32,128,128))
        self.spr_down_s0 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0,0,32,0)), (32,32,128,128))
        self.spr_down_s1 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0,0,96,0)), (32,32,128,128))
        self.spr_left = pygame.transform.chop(pygame.transform.chop(self.spr_f, (32,0,0,32)), (32,32,128,128))
        self.spr_left_s0 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0,0,32,32)), (32, 32, 128, 128))
        self.spr_left_s1 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0,0,96,32)), (32, 32, 128, 128))
        self.spr_right = pygame.transform.chop(pygame.transform.chop(self.spr_f, (32,0,0,64)), (32,32,128,128))
        self.spr_right_s0 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0,0,32,64)), (32, 32, 128, 128))
        self.spr_right_s1 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0,0,96,64)), (32, 32, 128, 128))
        self.spr_up = pygame.transform.chop(pygame.transform.chop(self.spr_f, (32,0,0,96)), (32,32,128,128))
        self.spr_up_s0 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0, 0,32,96)), (32,32,128,128))
        self.spr_up_s1 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0, 0,96,96)), (32,32,128,128))
        self.sprite = self.spr_left_s0

    def move(self, x=0, y=0):
        self.dest_x = self.x + (block_size * x)
        self.dest_y = self.y + (block_size * y)
        self.isMoving = True
        self.step += 1
        if self.step > 1:
            self.step = 0

    def update(self):
        if self.x % block_size == 0 and self.y % block_size == 0:
            if self.x == self.dest_x and self.y == self.dest_y:
                if KEY_UP:
                    if self.dir != DIR_UP:
                        self.dir = DIR_UP
                        self.m = 0
                    else:
                        self.m += 1
                    if self.m > 2:
                        if not KEY_CODE:
                            if self.data.surfing:
                                if get_tile_terrain(self.x,self.y - block_size) == "water":
                                    self.move(0, -1)
                                else:
                                    if get_tile_walkable(self.x,self.y - block_size, self.layer):
                                        player.data.surfing = False
                                        player.update_image()
                                        self.move(0, -1)
                            else:
                                if get_tile_walkable(self.x,self.y - block_size, self.layer):
                                    self.move(0, -1)
                        else:
                            self.move(0, -1)
                elif KEY_DOWN:
                    if self.dir != DIR_DOWN:
                        self.dir = DIR_DOWN
                        self.m = 0
                    else:
                        self.m += 1
                    if self.m > 2:
                        if not KEY_CODE:
                            if self.data.surfing:
                                if get_tile_terrain(self.x,self.y + block_size) == "water":
                                    self.move(0, 1)
                                else:
                                    if get_tile_walkable(self.x,self.y + block_size, self.layer):
                                        player.data.surfing = False
                                        player.update_image()
                                        self.move(0, 1)
                            else:
                                if get_tile_walkable(self.x, self.y + block_size, self.layer):
                                    self.move(0, 1)
                        else:
                            self.move(0, 1)
                elif KEY_LEFT:
                    if self.dir != DIR_LEFT:
                        self.dir = DIR_LEFT
                        self.m = 0
                    else:
                        self.m += 1
                    if self.m > 2:
                        if not KEY_CODE:
                            if self.data.surfing:
                                if get_tile_terrain(self.x - block_size,self.y) == "water":
                                    self.move(-1, 0)
                                else:
                                    if get_tile_walkable(self.x - block_size,self.y, self.layer):
                                        player.data.surfing = False
                                        player.update_image()
                                        self.move(-1, 0)
                            else:
                                if get_tile_walkable(self.x - block_size, self.y, self.layer):
                                    self.move(-1, 0)
                        else:
                            self.move(-1,0)
                elif KEY_RIGHT:
                    if self.dir != DIR_RIGHT:
                        self.dir = DIR_RIGHT
                        self.m = 0
                    else:
                        self.m += 1
                    if self.m > 2:
                        if not KEY_CODE:
                            if self.data.surfing:
                                if get_tile_terrain(self.x + block_size,self.y) == "water":
                                    self.move(1, 0)
                                else:
                                    if get_tile_walkable(self.x + block_size,self.y, self.layer):
                                        player.data.surfing = False
                                        player.update_image()
                                        self.move(1, 0)
                            else:
                                if get_tile_walkable(self.x + block_size, self.y, self.layer):
                                    self.move(1, 0)
                        else:
                            self.move(1,0)
                else:
                    self.m = 0
                if KEY_A_DOWN:
                    if self.dir == DIR_UP and not self.isBusy:
                        if get_tile_terrain(self.x, self.y - block_size) == "water" and not player.data.surfing:
                            show_text(project.str_list['surf_ask'],True)
                            result = engine.yes_no_box()
                            engine.clear_ui('text_box')
                            if result:
                                show_text(project.str_list['surf_use'].format(player.data.name),False)
                                self.dest_y -= block_size
                                self.data.surfing = True
                                self.data.on_bike = False
                                self.update_image()
                        else:
                            if get_tile_counter(self.x, self.y - block_size):
                                for obj in map.obj_list:
                                    if obj.y == self.y - (2*block_size) and obj.x == self.x:
                                        self.isBusy = True
                                        obj.interact()
                            else:
                                for obj in map.obj_list:
                                    if obj.y == self.y - block_size and obj.x == self.x:
                                        self.isBusy = True
                                        obj.interact()
                    elif self.dir == DIR_DOWN and not self.isBusy:
                        if get_tile_terrain(self.x, self.y + block_size) == "water" and not player.data.surfing:
                            show_text(project.str_list['surf_ask'],True)
                            result = engine.yes_no_box()
                            engine.clear_ui('text_box')
                            if result:
                                show_text(project.str_list['surf_use'].format(player.data.name),False)
                                self.dest_y += block_size
                                self.data.surfing = True
                                self.data.on_bike = False
                                self.update_image()
                        else:
                            for obj in map.obj_list:
                                if obj.y == self.y + block_size and obj.x == self.x:
                                    self.isBusy = True
                                    obj.interact()
                    elif self.dir == DIR_LEFT and not self.isBusy:
                        if get_tile_terrain(self.x - block_size, self.y) == "water" and not player.data.surfing:
                            show_text(project.str_list['surf_ask'],True)
                            result = engine.yes_no_box()
                            engine.clear_ui('text_box')
                            if result:
                                show_text(project.str_list['surf_use'].format(player.data.name),False)
                                self.dest_x -= block_size
                                self.data.surfing = True
                                self.data.on_bike = False
                                self.update_image()
                        else:
                            for obj in map.obj_list:
                                if obj.x == self.x - block_size and obj.y == self.y:
                                    self.isBusy = True
                                    obj.interact()
                    elif self.dir == DIR_RIGHT and not self.isBusy:
                        if get_tile_terrain(self.x + block_size, self.y) == "water" and not player.data.surfing:
                            show_text(project.str_list['surf_ask'],True)
                            result = engine.yes_no_box()
                            engine.clear_ui('text_box')
                            if result:
                                show_text(project.str_list['surf_use'].format(player.data.name),False)
                                self.dest_x += block_size
                                self.data.surfing = True
                                self.data.on_bike = False
                                self.update_image()
                        else:
                            for obj in map.obj_list:
                                if obj.x == self.x + block_size and obj.y == self.y:
                                    self.isBusy = True
                                    obj.interact()
        if self.dest_x > self.x:
            self.x += self.move_speed
        elif self.dest_x < self.x:
            self.x -= self.move_speed
        if self.dest_y > self.y:
            self.y += self.move_speed
        elif self.dest_y < self.y:
            self.y -= self.move_speed
        if (self.x == self.dest_x and self.y == self.dest_y) and self.isMoving:
            on_enter_tile(self.x, self.y)
            self.isMoving = False
        if self.data.on_bike:
            self.move_speed = 8
        else:
            self.move_speed = 4

    def draw(self):
        if self.dir == DIR_LEFT:
            if (self.x % block_size > self.move_speed) and (self.x % block_size < block_size - self.move_speed):
                if self.step == 0:
                    self.sprite = self.spr_left_s0
                else:
                    self.sprite = self.spr_left_s1
            else:
                self.sprite = self.spr_left
        elif self.dir == DIR_RIGHT:
            if (self.x % block_size > self.move_speed) and (self.x % block_size < block_size - self.move_speed):
                if self.step == 0:
                    self.sprite = self.spr_right_s0
                else:
                    self.sprite = self.spr_right_s1
            else:
                self.sprite = self.spr_right
        elif self.dir == DIR_UP:
            if (self.y % block_size > self.move_speed) and (self.y % block_size < block_size - self.move_speed):
                if self.step == 0:
                    self.sprite = self.spr_up_s0
                else:
                    self.sprite = self.spr_up_s1
            else:
                self.sprite = self.spr_up
        elif self.dir == DIR_DOWN:
            if (self.y % block_size > self.move_speed) and (self.y % block_size < block_size - self.move_speed):
                if self.step == 0:
                    self.sprite = self.spr_down_s0
                else:
                    self.sprite = self.spr_down_s1
            else:
                self.sprite = self.spr_down
        gameDisplay.blit(self.sprite, ((self.x - cam.x) , (self.y - cam.y) - 8))
        #pygame.draw.rect(gameDisplay, red, [self.x - cam.x, self.y - cam.y, block_size, block_size])


class NPC:
    def __init__(self, x, y, properties, img='char_ 44_D.png', direction = DIR_DOWN, mv_pattern = engine.mv_pattern_stationary, behavior = 'npcbehavior.py'):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.move_speed = 2
        self.mv_pattern = mv_pattern
        self.behavior = import_file(script_dir + behavior)
        self.properties = properties
        self.dir = direction
        self.radius = 3
        self.isMoving = False
        self.dest_x = self.x
        self.dest_y = self.y
        self.step = 0
        self.type = "npc"
        self.spr_f = pygame.image.load(spr_dir + img)
        self.spr_down = pygame.transform.chop(pygame.transform.chop(self.spr_f, (32,0,0,0)), (32,32,128,128))
        self.spr_down_s0 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0,0,32,0)), (32,32,128,128))
        self.spr_down_s1 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0,0,96,0)), (32,32,128,128))
        self.spr_left = pygame.transform.chop(pygame.transform.chop(self.spr_f, (32,0,0,32)), (32,32,128,128))
        self.spr_left_s0 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0,0,32,32)), (32, 32, 128, 128))
        self.spr_left_s1 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0,0,96,32)), (32, 32, 128, 128))
        self.spr_right = pygame.transform.chop(pygame.transform.chop(self.spr_f, (32,0,0,64)), (32,32,128,128))
        self.spr_right_s0 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0,0,32,64)), (32, 32, 128, 128))
        self.spr_right_s1 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0,0,96,64)), (32, 32, 128, 128))
        self.spr_up = pygame.transform.chop(pygame.transform.chop(self.spr_f, (32,0,0,96)), (32,32,128,128))
        self.spr_up_s0 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0, 0,32,96)), (32,32,128,128))
        self.spr_up_s1 = pygame.transform.chop(pygame.transform.chop(self.spr_f, (0, 0,96,96)), (32,32,128,128))
        self.sprite = self.spr_down
        self.m = None
        #

    def update(self):
        if self.mv_pattern != engine.mv_pattern_stationary:
            if self.mv_pattern == engine.mv_pattern_walk:
                if self.x % block_size == 0 and self.y % block_size == 0:
                    if self.x == self.dest_x and self.y == self.dest_y:
                        n = random.randrange(0,768)
                        if n <= 3:
                            self.dir = DIR_UP
                            if (self.y - block_size) >= self.start_y - (self.radius * block_size):
                                if get_tile_walkable(self.x, self.y - block_size):
                                    self.move(0, -1)
                        elif n <= 6:
                            self.dir = DIR_DOWN
                            if (self.y + block_size) <= self.start_y + (self.radius * block_size):
                                if get_tile_walkable(self.x, self.y + block_size):
                                    self.move(0, 1)
                        elif n <= 9:
                            self.dir = DIR_LEFT
                            if (self.x - block_size) >= self.start_x - (self.radius * block_size):
                                if get_tile_walkable(self.x - block_size, self.y):
                                    self.move(-1,0)
                        elif n <= 12:
                            self.dir = DIR_RIGHT
                            if (self.x + block_size) <= self.start_x + (self.radius * block_size):
                                if get_tile_walkable(self.x + block_size, self.y):
                                    self.move(1,0)
                        else:
                            pass
            elif self.mv_pattern == engine.mv_pattern_look:
                n = random.randrange(0,768)
                if n <= 3:
                    self.dir = DIR_UP
                elif n <= 6:
                    self.dir = DIR_DOWN
                elif n <= 9:
                    self.dir = DIR_LEFT
                elif n <= 12:
                    self.dir = DIR_RIGHT
                else:
                    pass
        if self.dest_x > self.x:
            self.x += self.move_speed
        elif self.dest_x < self.x:
            self.x -= self.move_speed
        if self.dest_y > self.y:
            self.y += self.move_speed
        elif self.dest_y < self.y:
            self.y -= self.move_speed
        if self.x == self.dest_x and self.y == self.dest_y:
            self.isMoving = False

    def move(self, x=0, y=0):
        self.dest_x = self.x + (block_size * x)
        self.dest_y = self.y + (block_size * y)
        self.isMoving = True
        self.step += 1
        if self.step > 1:
            self.step = 0

    def turn_toward_player(self):
        if self.x > player.x and self.y == player.y:
            self.dir = DIR_LEFT
        elif self.x < player.x and self.y == player.y:
            self.dir = DIR_RIGHT
        elif self.y > player.y and self.x == player.x:
            self.dir = DIR_UP
        elif self.y < player.y and self.x == player.x:
            self.dir = DIR_DOWN

    def interact(self):
        self.behavior.__init__(self)
        self.behavior.run()
        player.isBusy = False

    def draw(self):
        if self.dir == DIR_LEFT:
            if (self.x % block_size > self.move_speed) and (self.x % block_size < block_size - self.move_speed):
                if self.step == 0:
                    self.sprite = self.spr_left_s0
                else:
                    self.sprite = self.spr_left_s1
            else:
                self.sprite = self.spr_left
        elif self.dir == DIR_RIGHT:
            if (self.x % block_size > self.move_speed) and (self.x % block_size < block_size - self.move_speed):
                if self.step == 0:
                    self.sprite = self.spr_right_s0
                else:
                    self.sprite = self.spr_right_s1
            else:
                self.sprite = self.spr_right
        elif self.dir == DIR_UP:
            if (self.y % block_size > self.move_speed) and (self.y % block_size < block_size - self.move_speed):
                if self.step == 0:
                    self.sprite = self.spr_up_s0
                else:
                    self.sprite = self.spr_up_s1
            else:
                self.sprite = self.spr_up
        elif self.dir == DIR_DOWN:
            if (self.y % block_size > self.move_speed) and (self.y % block_size < block_size - self.move_speed):
                if self.step == 0:
                    self.sprite = self.spr_down_s0
                else:
                    self.sprite = self.spr_down_s1
            else:
                self.sprite = self.spr_down
        gameDisplay.blit(self.sprite, (self.x - cam.x, (self.y - cam.y) - 8))
        #pygame.draw.rect(gameDisplay, green, [self.x - cam.x, self.y - cam.y, block_size, block_size])


class Door:
    def __init__(self, x, y, dest_map, dest_x, dest_y, warp_type, width = block_size, height = block_size):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.dest_map = dest_map
        self.dest_x = dest_x
        self.dest_y = dest_y
        self.warp_type = warp_type
        self.type = 'door'

    def interact(self):
        pass

    @asyncio.coroutine
    def warp(self):
        print('start')
        project.se_list[1].play()
        cover.visible = True
        yield from asyncio.sleep(0.1)
        draw_all()
        engine.warp(self.dest_map, self.dest_x, self.dest_y)
        yield from asyncio.sleep(0.1)
        cover.visible = False
        draw_all()
        clock.tick(fps)
        print('end')
        print(player.x % block_size,player.y % block_size)

    def update(self):
        pass

    def draw(self):
        pass

    def inside_box(self, x, y):
        if ((x >= self.x) and (x < self.x + self.width)) and ((y >= self.y) and (y < self.y + self.height)):
            return True
        else:
            return False


class Signpost:
    def __init__(self, x, y, text):
        self.x = x
        self.y = y
        self.text = text
        self.type = "signpost"

    def interact(self):
        global inEvent
        inEvent = True
        print('start event')
        loop.run_until_complete(engine.show_text(self.text))
        print('event is done')
        player.isBusy = False
        inEvent = False

    def update(self):
        pass

    def draw(self):
        pass


class StepTrigger:
    def __init__(self, x, y, width, height, behavior):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.behavior = behavior
        self.type = 'trigger'

    def interact(self):
        self.behavior.__init__(self)
        self.behavior.run()

    def update(self):
        pass

    def inside_box(self, x, y):
        if ((x >= self.x) and (x < self.x + self.width)) and ((y >= self.y) and (y < self.y + self.height)):
            return True
        else:
            return False

    def draw(self):
        pass


class BerryTree:
    def __init__(self, x, y, berry):
        self.x = x
        self.y = y
        self.berry = berry
        self.type = "berrytree"

    def interact(self):
        global inEvent
        inEvent = True
        loop.run_until_complete(engine.show_text(project.str_list['berry_tree']))
        player.isBusy = False
        inEvent = False

    def update(self):
        pass

    def draw(self):
        pass


def on_enter_tile(x, y):
    if x // block_size < 0 and ('connection_left' in map.properties):
        connection = map.properties['connection_left']
        offset = map.connections['left'].offset
        unload_map()
        load_map(connection)
        player.x = (map.width - 1) * block_size
        player.y = y + (offset * block_size)
        player.dest_x = player.x
        player.dest_y = player.y
    elif x // block_size >= map.width and ('connection_right' in map.properties):
        connection = map.properties['connection_right']
        offset = map.connections['right'].offset
        unload_map()
        load_map(connection)
        player.x = 0
        player.y = y + (offset * block_size)
        player.dest_x = player.x
        player.dest_y = player.y
    elif y // block_size < 0 and ('connection_up' in map.properties):
        connection = map.properties['connection_up']
        offset = map.connections['up'].offset
        print('unload_map')
        unload_map()
        print('load_map')
        load_map(connection)
        player.x = x + (offset * block_size)
        player.y = (map.height - 1) * block_size
        player.dest_x = player.x
        player.dest_y = player.y
    elif y // block_size >= map.height and ('connection_down' in map.properties):
        connection = map.properties['connection_down']
        offset = map.connections['down'].offset
        unload_map()
        load_map(connection)
        player.x = x + (offset * block_size)
        player.y = 0
        player.dest_x = player.x
        player.dest_y = player.y
        print(player.x,player.y)
    for obj in map.obj_list:
        if obj.type == "door":
            if obj.inside_box(x,y):
                print('warp')
                loop.run_until_complete(obj.warp())
        elif obj.type == "trigger":
            if obj.inside_box(x,y):
                print('trigger_activated')
                obj.interact()


def get_tile_walkable(x,y,layer=0):
    for obj in map.obj_list:
        if obj.x == x and obj.y == y:
            if obj.type == "door":
                if obj.warp_type == "exit":
                    loop.run_until_complete(obj.warp())
                    player.dir = DIR_DOWN
                    player.dest_y = player.y + 32
    # if (x / block_size < 0 or x / block_size >= map.width) or (y / block_size < 0 or y / block_size >= map.height):
    #     return False
    if x / block_size < 0:
        if "left" in map.connections:
            c_left = map.connections['left'].map
            print((map.connections['left'].width - 1),(player.y+map.connections['left'].offset) // block_size, layer)
            props = c_left.get_tile_properties((map.connections['left'].width - 1),(player.y+map.connections['left'].offset) // block_size, 0)
            if props['isWalkable'] == "true":
                return True
            else:
                return False
        else:
            return False
    elif x / block_size >= map.width:
        if "right" in map.connections:
            props = map.connections['right'].map.get_tile_properties(0, (player.y+map.connections['right'].offset) / block_size, 0)
            if props['isWalkable'] == "true":
                return True
            else:
                return False
        else:
            return False
    elif y / block_size < 0:
        if "up" in map.connections:
            props = map.connections['up'].map.get_tile_properties((x+map.connections['up'].offset) / block_size,map.connections['up'].height * block_size, 0)
            if props['isWalkable'] == "true":
                return True
            else:
                return False
        else:
            return False
    elif y / block_size >= map.height:
        if "down" in map.connections:
            props = map.connections['down'].map.get_tile_properties((x+map.connections['down'].offset) / block_size,0, 0)
            if props['isWalkable'] == "true":
                return True
            else:
                return False
        else:
            return False
    if (player.x == x and player.y == y) or (player.dest_x == x and player.dest_y == y):
        return False
    for obj in map.obj_list:
        if obj.type == "npc":
            if (obj.x == x and obj.y == y) or (obj.dest_x == x and obj.dest_y == y):
                return False
    props = map.map.get_tile_properties(x / block_size, y / block_size, layer)
    if 'isWalkable' in props:
        if props['isWalkable'] == "true":
            return True
        else:
            return False


def get_tile_counter(x,y):
    if x // block_size > 0 and x // block_size < map.width and y // block_size > 0 and y // block_size < map.height:
        props = map.map.get_tile_properties(x / block_size, y / block_size, 0)
        if 'counter' in props:
            if props['counter'] == "true":
                return True
    return False


def get_tile_terrain(x,y):
    if x // block_size > 0 and x // block_size < map.width and y // block_size > 0 and y // block_size < map.height:
        props = map.map.get_tile_properties(x / block_size, y / block_size, 0)
        if 'terrain' in props:
            return props['terrain']
    return 'none'


@asyncio.coroutine
def screen_blink(seconds=1):
    cover.visible = True
    draw_all()
    yield from asyncio.sleep(seconds)
    cover.visible = False


def init_all():
    global ui_elements
    ui_elements = []
    ui_elements.append(cover)


def main():
    global exit_game
    global inMenu
    global KEY_LEFT
    global KEY_RIGHT
    global KEY_UP
    global KEY_DOWN
    global KEY_A_DOWN
    global KEY_A
    global KEY_NO_DIR
    global KEY_CODE
    while not exit_game:
        KEY_A_DOWN = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    exit_game = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    KEY_LEFT = True
                elif event.key == pygame.K_RIGHT:
                    KEY_RIGHT = True
                elif event.key == pygame.K_UP:
                    KEY_UP = True
                elif event.key == pygame.K_DOWN:
                    KEY_DOWN = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    KEY_LEFT = False
                elif event.key == pygame.K_RIGHT:
                    KEY_RIGHT = False
                elif event.key == pygame.K_UP:
                    KEY_UP = False
                elif event.key == pygame.K_DOWN:
                    KEY_DOWN = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    KEY_A = True
                    KEY_A_DOWN = True
                if event.key == pygame.K_LCTRL:
                    KEY_CODE = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_c:
                    KEY_A = False
                if event.key == pygame.K_LCTRL:
                    KEY_CODE = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LSHIFT:
                    inMenu = True
                    engine.open_menu()
                    inMenu = False
        if not KEY_LEFT and not KEY_RIGHT and not KEY_UP and not KEY_DOWN:
            KEY_NO_DIR = True
        else:
            KEY_NO_DIR = False
        if not inEvent:
            update_all()
        draw_all()
        clock.tick(fps)


def update_all():
    for obj in map.obj_list:
        obj.update()
    player.update()


def load_map(name):
    global map
    global dmap
    dmap = load_pygame(map_dir + name + '.tmx')
    if 'outside' in dmap.properties:
        if dmap.properties['outside'] == "true":
            if systime.get_time_of_day() == "Night":
                print("It's night.")
                dmap.tilesets[0].source = "../Tilesets/GSC overworld johto nite.png"
                dmap.reload_images()
    map = Map(dmap)
    del dmap


def unload_map():
    global map
    del map


# def load_map_from_connection(dir):
#     if dir == DIR_LEFT:
#         global map
#         name = map.properties['connection_left']
#         del map
#         map = load_pygame(map_dir + name + '.tmx')
#         player.x += connection_left.width; player.y -= c_left_offset
#         del connection_left
#         del c_left_offset
#     elif dir == DIR_RIGHT:
#         global map
#         name = map.properties['connection_right']
#         del map
#         map = load_pygame(map_dir + name + '.tmx')
#         player.x -= connection_right.width; player.y -= c_right_offset
#     elif dir == DIR_UP:
#         global map
#         name = map.properties['connection_up']
#         del map
#         map = load_pygame(map_dir + name + '.tmx')
#         player.y += connection_up.height; player.x -= c_up_offset
#     elif dir == DIR_DOWN:
#         global map
#         name = map.properties['connection_down']
#         del map
#         map = load_pygame(map_dir + name + '.tmx')
#         player.y -= connection_down.height; player.x -= c_down_offset


def draw_all():
    if cam.center_on_player:
        cam.realign()
    cam.draw()
    map.draw()
    for connection in map.connections:
        map.connections[connection].draw()
    for obj in map.obj_list:
        if (obj.x - cam.x > -32 and obj.x - cam.x < display_width + 32) and (
                            obj.y - cam.y > -32 and obj.y - cam.y < display_height + 32
        ):
            obj.draw()
    player.draw()
    for element in ui_elements:
        element.draw()
    cover.draw()
    winDisplay.blit(pygame.transform.scale(gameDisplay,(display_width * resolution_factor, display_height * resolution_factor),winDisplay),(0,0))
    pygame.display.update([0,0,display_width * resolution_factor,display_height * resolution_factor])

def show_text(string,keep_open = False):
    loop.run_until_complete(engine.show_text(string,keep_open))

print('Open game window...')
gameDisplay = pygame.Surface((display_width, display_height))
winDisplay = pygame.display.set_mode((display_width * resolution_factor, display_height * resolution_factor))
pygame.display.update()
pygame.display.set_caption(game_title)
loop = asyncio.get_event_loop()
inEvent = False
cam = Camera()
obj_list = []
ui_elements = []
inMenu = False
mainMenu = False
cover = ScreenCover()
gameData = GameData()
load_map('test')
player = Player()
save = SaveData()
# pygame.display.set_icon(game_icon)
print('Initializing game components...')
exit_game = False
if __name__ == '__main__':
    print('Entering main loop...')
    main()
pygame.quit()
quit()
