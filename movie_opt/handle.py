from movie_opt.commands.ai import LaunageAI
from movie_opt.commands.subtitle import SubtitleOperater
from movie_opt.commands.picture import PictureOperater
from movie_opt.commands.voice import VoiceOperater 
from movie_opt.commands.merge import MergeOperater 

class Executor:
    def __init__(self):
        print(f"初始化Executor\n{'-'*22}")
        self.launageAI:LaunageAI = LaunageAI()
        self.voiceOperater:VoiceOperater = VoiceOperater(self.launageAI)
        self.subtitleOperater:SubtitleOperater = SubtitleOperater(self.launageAI)
        self.pictureOperater:PictureOperater = PictureOperater(self.launageAI,self.voiceOperater)
        self.mergeOperater:MergeOperater = MergeOperater(self.launageAI)