# Author     : Jonathan Decker "Lokno"
# Description: Joins an IRC channel and parses the chat messages for
# percentages. It writes the average percentage from each unique
# user to a file. Idle contributions are removed after a number of 
# seconds, as defined by the variable lifeTime declared on line 19
# 
# Nick and Janel Variant - type dd%n for nick and dd%j for Janel
# dd% without a letter will default to nick.
#
# Reference:
# http://help.twitch.tv/customer/portal/articles/1302780-twitch-irc
 
import socket
import re,os,time
 
server   = "irc.chat.twitch.tv"
channel  = "#idlethumbs"
botnick  = "ACCOUNTNAME"
password = "OAUTHTOKEN"
 
updateMapInterval = 60
lifeTime          = 60*3  # Time before a user's vote expires
  
percNickRE    = re.compile("(?<![\d\.])(-?\d+\.?\d*)\%([nN]?)(?![jJ])")
percJanelRE   = re.compile("(?<![\d\.])(-?\d+\.?\d*)\%([jJ])")
nameRE        = re.compile("^:([^!]+)!")
filePathNick  = "internalization.txt"
filePathJanel = "internalization_janel.txt"
 
def writefile(nP,jP):
   with open(filePathNick,'w') as f:
      f.write("Nick: %d%%" % nP)
   with open(filePathJanel,'w') as f:
      f.write("Janel: %d%%" % jP)  
 
# Return of Ganon Font - https://zeldauniverse.net/media/fonts/
def writeMeterFiles(nP,jP):
   max_hearts = 10
   nFull = int(nP) / (100/max_hearts)
   jFull = int(jP) / (100/max_hearts)
   with open(filePathNick,'w') as f:
      f.write("Nick: "  + "#" * nFull + "*" * (max_hearts-nFull))
   with open(filePathJanel,'w') as f:
      f.write("Janel: " + "#" * jFull + "*" * (max_hearts-jFull))  
 
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
 
lastCheck  = time.time()
 
voteMapNick = {}
vsumNick    = 0
countNick   = 0
 
voteMapJanel = {}
vsumJanel    = 0
countJanel   = 0
 
writefile(0,0)
 
while 1:
   text     = irc.recv(2040)
   currTime = time.time()
 
   percNickM  = percNickRE.search(text)
   percJanelM = percJanelRE.search(text)
   nameM      = nameRE.search(text)
 
   if nameM and (percNickM or percJanelM):
      matches = []
      if percNickM:
         matches.append((percNickM.group(1),percNickM.group(2)))
      if percJanelM:
         matches.append((percJanelM.group(1),percJanelM.group(2)))
 
      for percM in matches:
         # nonsense numbers from chat are converted
         # to integers in the range [0,100]
         # what does 0.5% internalization even mean?
         # also this can be -inf or inf, which is fun
         whoStr = 'n'
         if percM[1] != '':
            whoStr = percM[1].lower()
         val = float(percM[0])
         val = int(max(0,min(val,100)))
 
         currName = nameM.group(1)
 
         # update sum, count and map
         if( whoStr == 'n' ):
            if currName in voteMapNick:
               vsumNick -= voteMapNick[currName][0]
            else:
               countNick += 1
            vsumNick += val
            voteMapNick[currName] = [val,currTime]
         else:
            if currName in voteMapJanel:
               vsumJanel -= voteMapJanel[currName][0]
            else:
               countJanel += 1
            vsumJanel += val
            voteMapJanel[currName] = [val,currTime]
 
      writefile(getAvg(vsumNick,countNick),getAvg(vsumJanel,countJanel))
 
   # refreshes the map to remove votes from idle users
   if (currTime-lastCheck) > updateMapInterval:
      lastCheck = currTime
 
      for k,v in voteMapNick.items():
         if (currTime-v[1]) >= lifeTime:
            del voteMapNick[k]
            vsumNick  -= v[0]
            countNick -= 1
 
      for k,v in voteMapJanel.items():
         if (currTime-v[1]) >= lifeTime:
            del voteMapJanel[k]
            vsumJanel  -= v[0]
            countJanel -= 1
 
      writefile(getAvg(vsumNick,countNick),getAvg(vsumJanel,countJanel))
     
   # sends 'PONG' if 'PING' received to prevent pinging out
   if text.find('PING') != -1: 
      irc.send('PONG ' + text.split() [1] + '\r\n')