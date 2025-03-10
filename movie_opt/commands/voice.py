import os
import traceback
import torch
from pydub import AudioSegment
import requests
from TTS.api import TTS
from pkg_resources import resource_filename
from gtts import gTTS
import asyncio
import logging
import edge_tts

from movie_opt.commands.ai import LaunageAI


def change_4_edge_tts_voice(content):
        # Define the punctuation replacements
    punctuation_replacements = {
        '：': '，',  # Chinese colon to Chinese comma
        '、': '，',  # Chinese enumerator to Chinese comma
        '？': '，',  # Chinese question mark to Chinese comma
        '；': '，',  # Chinese semicolon to Chinese comma
        '！': '，',  # Chinese exclamation mark to Chinese comma
        ':': ',',   # English colon to English comma
        ',': ',',   # English comma remains unchanged
        '?': ',',   # English question mark to English comma
        ';': ',',   # English semicolon to English comma
        '!': ',',   # English exclamation mark to English comma
    }

    # Replace the punctuation marks
    for old_punct, new_punct in punctuation_replacements.items():
        content = content.replace(old_punct, new_punct)
    return content


class VoiceOperater:
    def __init__(self,launageAI):
        self.launageAI:LaunageAI = launageAI
        self.device = "cuda" if torch.cuda.is_available() else "cpu"


    def edge_tts_voice(self, args):
        # 获取参数内容
        content = args.content
        save_path = args.save_path
        language = args.language
        voice = args.voice
        rate = getattr(args, 'rate', '+0%')  # 添加语速参数，默认为正常语速

        # 检查内容是否为空
        if not content:
            raise ValueError("Content cannot be empty")

        # 设置默认语言为英文
        if language is None:
            language = "en"

        # 设置默认语音
        if voice is None:
            if language == "en":
                voice = "en-US-MichelleNeural"  # 默认英文
            elif language == "en-child":
                voice = "en-US-AnaNeural"  # 默认儿童英文
            elif language == "zh-cn":
                voice = "zh-CN-XiaoxiaoNeural"  # 默认中文
            elif language == "zh-tw":
                voice = "zh-TW-HsiaoChenNeural"  # 默认台湾中文
            else:
                raise ValueError(f"Unsupported language: {language}")

        # 如果是中文将一些特殊标点符号替换为逗号以便断句
        if voice.split('-')[0] == "zh":
            content = change_4_edge_tts_voice(content)

        async def run_tts_with_retry():
            retries = 10
            for attempt in range(1, retries + 1):
                try:
                    communicate = edge_tts.Communicate(content, voice, rate=rate)
                    await communicate.save(save_path)
                    print(f"Audio saved successfully at {save_path}")
                    return
                except Exception as e:
                    logging.error(f"Attempt {attempt} failed: {e}")
                    traceback.print_exc()
                    if attempt == retries:
                        raise RuntimeError(f"Failed to generate TTS after {retries} attempts {e}")

        # 如果事件循环已存在，复用现有循环
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # 如果不存在事件循环，则创建新的
            loop = None

        if loop and loop.is_running():
            # 在已有事件循环中运行任务
            asyncio.ensure_future(run_tts_with_retry())
        else:
            asyncio.run(run_tts_with_retry())


    def gtts_voice(self,args): 
        # 获取参数内容
        content = args.content
        save_path = args.save_path
        language = args.language
        slow = args.slow

        # 设置默认语言为英文
        if language is None:
            language = "en"
        
        # 设置默认语速
        if slow is None:
            slow = False

        # 检查内容是否为空
        if not content:
            raise ValueError("Content cannot be empty")

        # 调用 gTTS 进行语音合成
        try:
            tts = gTTS(text=content, lang=language, slow=slow)
            # 保存为 MP3 文件
            tts.save(save_path)
            print(f"Audio saved successfully at {save_path}")
        except Exception as e:
            print(f"Error occurred during TTS: {e}")


    def youdao_voice(self,args): 
        # 获取参数内容
        content = args.content
        save_path = args.save_path
        type = args.type if args.type is not None else 1
        output_dir = args.output_dir if hasattr(args, 'output_dir') else './'
        
        # 构造请求 URL
        url = f"https://dict.youdao.com/dictvoice?audio={content}&type={type}"
        
        # 设置保存路径
        if save_path is None:
            save_path = f"./{content}.mp3"  # 使用内容作为文件名
        
        try:
            # 发送 GET 请求下载 MP3 文件
            print(f"Downloading audio from: {url}")
            response = requests.get(url, stream=True)
            response.raise_for_status()  # 检查请求是否成功
            
            # 保存 MP3 文件
            with open(save_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)
            
            print(f"MP3 file saved as: {save_path}")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading audio: {e}")



    def create_mp3_by_clone_voice(self,args):
        """
        Create a new MP3 audio file using xtts_v2 by cloning the voice from a given WAV file.

        Args:
            args: An object with the following attributes:
                content (str): The text content to synthesize.
                wav_path (str): The path to the input WAV file (used as the voice clone).
                output_path (str): The path to save the output MP3 file.
        """
        # Ensure required parameters are provided
        if not hasattr(args, 'content'):
            raise ValueError("Missing required parameters: 'content'")

        content = args.content
        wav_path = ""
        # 设置保存路径
        if args.save_path is None:
            args.save_path = f"./{content}.mp3"  # 使用内容作为文件名

        language = args.language

        # Initialize TTS model
        print("Initializing TTS model...")
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)

        # Generate new audio using TTS
        print("Generating synthetic audio...")
        wav_path = os.path.join(os.path.dirname(resource_filename(__name__,".")),'static', "demo1.wav")
        print("wav_path ",wav_path)
        tts.tts_to_file(text=content, speaker_wav=wav_path, language=language, file_path=args.save_path)

        # Convert WAV to MP3
        print("Converting WAV to MP3...")
        audio = AudioSegment.from_wav(args.save_path)
        audio.export(args.save_path, format="mp3")

        print(f"MP3 audio saved to: {args.save_path}")



    def clone_voice_conversion(self,args):
        # Initialize TTS model
        print("Initializing TTS model...")
        tts = TTS(model_name="voice_conversion_models/multilingual/vctk/freevc24",progress_bar=False).to(self.device)

        # Generate new audio using TTS
        print("Generating synthetic audio...")
        wav_path = os.path.join(os.path.dirname(resource_filename(__name__,".")),'static', "demo1.wav")
        print("wav_path ",wav_path)
        tts.voice_conversion_to_file(source_wav=wav_path,target_wav=args.target_wav,file_path=args.save_path)
        # Convert WAV to MP3
        print("Converting WAV to MP3...")
        audio = AudioSegment.from_wav(args.save_path)
        audio.export(args.save_path, format="mp3")

        print(f"MP3 audio saved to: {args.save_path}")
