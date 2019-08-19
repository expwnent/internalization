# Author     : Jonathan Decker "Lokno"
# Description: Joins an IRC channel and parses the chat messages for
# percentages. It writes the average percentage from each unique
# user to a file. Idle contributions are removed after a number of 
# seconds, as defined by the variable lifeTime declared on line 19
#
# Reference:
# http://help.twitch.tv/customer/portal/articles/1302780-twitch-irc

import socket
import re,os,time
import wave

server   = "irc.chat.twitch.tv"
channel  = "#idlethumbs"
botnick  = "NickBreckon"
password = "oauth:tva0o6u2likuipjb72txu4w0n3084p"

# complete file path to sound file
# example: "C:\Users\Nick\Desktop\Internalization\6ae9a68b782af38ef94124e365fb1574-83e27023a610ddea33138268cc276bbf1fc14661\that_was_good_play.wav"
goodPlayFilePath = "C:\\Users\\nickb\\Desktop\\Internalization\\that_was_good_play.wav"

updateMapInterval = 60
lifeTime          = 60*5  # Time before a user's vote expires
cooldownSoundfile = 60*5  # Time until sound file can play again

percRE = re.compile("(?<![\d\.])(-?\d+\.?\d*)\%")
nameRE = re.compile("^:([^!]+)!")
percentOf = "Internalization"
filePath  = "internalization.txt"

def writefile(percent):
   with open(filePath,'w') as f:
      f.write("%s: %d%%" % (percentOf,percent))  

def getAvg(sum,count):
   avg = 0
   if count > 0:
      avg = sum/count
   return avg

irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print "connecting to:" + server
irc.connect((server, 6667))
print "connected!"
print "joining channel %s as %s..." % (channel,botnick)

irc.send("PASS " + password + "\n")
irc.send("NICK " + botnick  + "\n")
irc.send("JOIN " + channel  + "\n")

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

      if goodPlayFilePath != "":
         # plays a sound file at 100% is it wasn't 100% before this vote and some
         # period of time has past since the last time it played
         if percent == 100 and changed and (currTime-lastCooldownCheck) > cooldownSoundfile:
            os.system('powershell -c (New-Object Media.SoundPlayer "%s").PlaySync();' % goodPlayFilePath)   
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
