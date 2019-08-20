#internalization_solo.py
#author expwnent
#based on script by lokno https://gist.github.com/Lokno/add0dab1f8b76aa03334d839b936b228 https://gist.github.com/Lokno/6ae9a68b782af38ef94124e365fb1574
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License along
#    with this program in the file gpl-2.0.txt.

import socket
import re,os,time
import wave
import configparser
from playsound import playsound

# Loading configuration file (ini format)
config = configparser.ConfigParser()

configFile = 'internalization.cfg'
if not config.read(configFile):
    print('ERROR: could not open file %s' % configFile)
    sys.exit(-1)

server   = config.get('MAIN','server')
channel  = '#' + config.get('MAIN','channel')
botnick  = config.get('MAIN','botnick')
password = config.get('MAIN','password')
updateMapInterval = config.getint('TIMING','updateMapInterval')
lifeTime          = config.getint('TIMING','lifeTime')
cooldownSoundfile = config.getint('TIMING','cooldownSoundfile')
percentOf = config.get('FILES','percentOf')
filePath  = config.get('FILES','filePath')
internalization100Sound = config.get('FILES','internalization100Sound')
internalization000Sound = config.get('FILES','internalization000Sound')

#goodPlayFilePath = config.get('FILES','goodPlayFilePath')

percRE = re.compile("(?<![\d\.])(-?\d+\.?\d*)\%")
nameRE = re.compile("^:([^!]+)!")

def writefile(percent):
    with open(filePath,'w') as f:
        f.write("%s: %d%%" % (percentOf,percent))  

def getAvg(sum,count):
    avg = 0
    if count > 0:
        avg = sum/count
    return avg


irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print("connecting to:" + server)
irc.connect((server, 6667))
print("connected!")
print("joining channel %s as %s..." % (channel,botnick))



irc.send(("PASS " + password + "\n").encode())
irc.send(("NICK " + botnick  + "\n").encode())
irc.send(("JOIN " + channel  + "\n").encode())

initialVal = 0
lastCheck  = time.time()
voteMap    = {}
vsum       = 0
count      = 0
changed    = True
lastCooldownCheck = 0

writefile(0)


while 1:
    text     = irc.recv(2040)
    text = text.decode()
    #if len(text) > 0:
    #    print ("Text = %s" % text)
    currTime = time.time()

    percM = percRE.search(text)
    nameM = nameRE.search(text)

    if nameM and percM:
        # nonsense numbers from chat are converted
        # to integers in the range [0,100]
        # what does 0.5% internalization even mean?
        # also this can be -inf or inf, which is fun
        val = float(percM.group(1))
        val = int(max(0,min(val,100)))

        currName = nameM.group(1)

        # update sum, count and map
        if currName in voteMap:
           vsum -= voteMap[currName][0]
        else:
           count += 1
        vsum += val
        voteMap[currName] = [val,currTime]

        percent = getAvg(vsum,count)
        writefile(percent)

        if internalization100Sound != "":
            # plays a sound file at 100% is it wasn't 100% before this vote and some
            # period of time has past since the last time it played
            if percent == 100 and changed and (currTime-lastCooldownCheck) > cooldownSoundfile:
                #os.system('powershell -c (New-Object Media.SoundPlayer "%s").PlaySync();' % internalization100Sound)
                playsound(internalization100Sound)
                lastCooldownCheck = currTime
            elif percent != 100:
                changed = True
        if internalization000Sound != "":
            if percent == 0   and changed and (currTime-lastCooldownCheck) > cooldownSoundfile:
                #os.system('powershell -c (New-Object Media.SoundPlayer "%s").PlaySync();' % internalization000Sound)
                playsound(internalization000Sound)
                lastCooldownCheck = currTime
            elif percent != 100:
                changed = True
    # refreshes the map to remove votes from idle users
    if (currTime-lastCheck) > updateMapInterval:
        lastCheck = currTime
        for k,v in voteMap.items():
            if (currTime-v[1]) >= lifeTime:
                del voteMap[k]
                vsum  -= v[0]
                count -= 1

        percent = getAvg(vsum,count)
        writefile(percent)

    # sends 'PONG' if 'PING' received to prevent pinging out
    if text.find('PING') != -1: 
        irc.send('PONG ' + text.split() [1] + '\r\n') 

