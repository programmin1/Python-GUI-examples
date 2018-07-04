from time import time
import pygame

class Runner():
    def __init__(self):
        self.last = []
        self.lastwarn = 0
        #Init for ability to play sound:
        pygame.init()
        
    def run(self, found):
        self.last.append(found)
        #Clip results to last 50 true/false detection results:
        self.last = self.last[-50:]
        if sum(self.last) > 40 and self.lastwarn + 30 < time():
            print('Oven finished!')
            pygame.mixer.music.load("ovenwarning.wav")
            pygame.mixer.music.play()
            #Do not trigger again until 30s later or more...
            self.lastwarn = time()
