from movie_opt.commands.ai import LaunageAI
from movie_opt.commands.subtitle import SubtitleOperater
from movie_opt.commands.picture import PictureOperater
from movie_opt.commands.voice import VoiceOperater 

class Executor:
    def __init__(self):
        print(f"初始化Executor\n{'-'*22}")
        self.launageAI = LaunageAI()
        self.voiceOperater = VoiceOperater(self.launageAI)
        self.subtitleOperater = SubtitleOperater(self.launageAI)
        self.pictureOperater = PictureOperater(self.launageAI,self.voiceOperater)