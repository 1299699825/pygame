import time 
import pygame
pygame.init() #or we could just call pygame.display.init() as thats all we need
pygame.mixer.quit() #This needs to be done, as the default sound system of the 
                    # ffmpeg-wrapper uses SDL_mixer, and this would cause major
                    # conflicts with the mixer module.
import pygame.nmovie as movie

print "Please give an (absolute)filename of a movie file you'd like to play: ",
#filename = raw_input()
filename="/home/tyler/War3.avi"
#initialization. It could also have a surface as a second argument, and every 
# frame will be blitted to that surface. It is the programmer's responsibility
# to be on time for rendering that surface.
# Without a surface argument, the ffmpeg-wrapper uses the sdl_overlay library. 
m = movie.Movie(filename)
print m.paused  #always False, unless .pause has been called
print m.playing #False until play has been called. Will return to false when
                # .stop() has been called.
                
print m.width   #default size values of the video file
print m.height  # They can be modified on the fly, as will be demonstrated.

print m         #calls __repr__, which will show the filename, and the current 
                # timestamp. 

m.play(-1)      #We're going to use infinite play, so we can demonstrate all 
                # the features.
time.sleep(10)  #sleep for ten seconds to let one see the video play, and hear 
                # the audio
print m.paused
print m.playing
print m

#Now we're going to play with the size of the window, affecting the video on 
# the fly. resize(width, height) is the main function, changes them both at
# the same time.
m.resize(m.width/2, m.height*2)
time.sleep(10) #another ten second nap.
m.width = m.width*4 
time.sleep(10)
m.width=m.width/2
m.height = m.height/2
#back to our original size
time.sleep(10)
#Here we demonstrate the use of pause. You pause, then call pause again to play
m.pause()
print m.paused
print m.playing
time.sleep(2)
m.pause()
print m.paused
print m.playing
#Here is the stop function. Right now, rewind is the exact same as stop.
m.stop()
time.sleep(3)
#And now we restart playing.
m.play(-1)

screen = pygame.display.set_mode((m.width, m.height))
#This will move the movie player from overlay mode to blitting to the surface 
# we've given it. This means it is our responsibility to update the display on 
# time.

counter = 0
actions = {5: lambda x: x.pause(), 10: lambda x: x.pause(), 15: lambda x: x.resize(x.width/2, x.height/2), 20:lambda x: x.stop(), 22: lambda x: x.play(-1)}
prev_time = time.time()
m.surface = screen
while(1):
    new_time=time.time()
    diff = int(new_time-prev_time)
    if(diff>=1):
        counter+=1
    prev_time=new_time
    if counter==30:
        break
    if actions.has_key(counter):
        actions[counter](m)
    pygame.display.update() #we can do this because we're blitting each frame of the movie to the main screen we instantiated.
    
del m
#the end

