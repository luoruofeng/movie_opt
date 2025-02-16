# movie-opt
learn english by movie


# 字体安装
```
https://www.alibabafonts.com/#/font
```

如果要使用阿里千万api请配置环境变量DASHSCOPE_API_KEY


# 使用

## 将pc裁剪为手机
```
movie_opt.exe picture cut_pc2phone --path="C:\Users\luoruofeng\Desktop\test"
```

## 创建封面
```
movie_opt.exe picture generate_images --path="C:\Users\luoruofeng\Desktop\test\video.mp4"
```

## 将英文的srt文件中的英文重新排版
```
movie_opt.exe subtitle reposition_srt --path="C:\Users\luoruofeng\Desktop\a.srt"
```


## 将srt字幕转化ass字幕文件
```
movie_opt.exe subtitle srt2ass --path="C:\Users\luoruofeng\Desktop\test"
```

## 将ass字幕转化srt字幕文件
```
movie_opt.exe subtitle convert_ass_to_srt --path="C:\Users\luoruofeng\Desktop\test\test.ass"
```


## ass文件的复杂单词修改颜色样式 
```
movie_opt.exe subtitle change_ass_hard_word_style --path="C:\Users\luoruofeng\Desktop\test\test.ass"
```



## 统计srt文件中的对话行数和英语词汇量
```
movie_opt.exe subtitle count_srt_statistics --path="C:\Users\luoruofeng\Desktop\test\test.srt"
```


## 给视频添加ass字幕
```
movie_opt.exe subtitle addass --path="C:\Users\luoruofeng\Desktop\test"
```

## 合并两个srt文件
```
movie_opt.exe subtitle mergesrt --path="C:\Users\luoruofeng\Desktop\test"
```

## 顺序显示srt字幕中的每一行
```
movie_opt.exe subtitle sequencesrt --path="C:\Users\luoruofeng\Desktop\test"
```

## srt字幕内容转png图片
```
movie_opt.exe subtitle srt2txtpng --path="C:\Users\luoruofeng\Desktop\test"
```



## 从数据库查询英文单词
```
movie_opt.exe translate find_db_word --word="innovation"
```



## 将srt文件安装时间间隔分段保存为新的srt文件
```
movie_opt.exe subtitle srtsegment --path="C:\Users\luoruofeng\Desktop\test" --second=13
```


## 根据已有wav克隆新的声音（英文或中文）
```
movie_opt.exe voice create_mp3_by_clone_voice --content="阅读这段内容" --save_path="C:\Users\luoruofeng\Desktop\test\content.mp3" --language="cn"
```

## 有道词典发音(英文)
```
movie_opt.exe voice youdao_voice --content="i am exploring here" --save_path="C:\Users\luoruofeng\Desktop\test\youdao.mp3" --type=2
```

## 创建gtts发音
```
movie_opt.exe voice gtts_voice --content="i am exploring here" --save_path="C:\Users\luoruofeng\Desktop\test\edge.mp3" --language="en"
```

## 创建edge_tts_voice发音
```
movie_opt.exe voice edge_tts_voice --content="i am exploring here" --save_path="C:\Users\luoruofeng\Desktop\test\edge.mp3" --language="en-child"
```



## 将wav转化为克隆的声音（英文或中文）
```
movie_opt.exe voice clone_voice_conversion   --save_path="C:\Users\luoruofeng\Desktop\test\new.mp3" --target_wav="C:\Users\luoruofeng\Desktop\test\content.wav"
```


## 将视频分段
```
movie_opt.exe picture video_segment   --srt_path="C:\Users\luoruofeng\Desktop\test\srt分段" --video_path="C:\Users\luoruofeng\Desktop\test\test_subtitled.mkv"
```

# 按照字幕行，生成视频中每一句的朗读视频和跟读视频（通过视频和字幕文件）
```
movie_opt.exe picture split_video   --srt_path="C:\Users\luoruofeng\Desktop\test\srt分段2\Lion King 2 1998-en@cn-3.srt"  --video_path="C:\Users\luoruofeng\Desktop\test\视频片段\Lion King 2 1998-en@cn-3.mkv"
```


# 将srt文件的第一行字幕改为00:00:00,000开始
```
movie_opt.exe subtitle convert_time --path="C:\Users\luoruofeng\Desktop\test\srt分段"
```


# 逐行拼接“1中英文对照 2跟读 3磨耳朵”视频
```
movie_opt.exe merge merge1  --path="C:\Users\luoruofeng\Desktop\test\视频片段"
```


# 相同编号的“1中英文对照 2跟读 3磨耳朵”视频拼接起来
```
movie_opt.exe merge merge2  --path="C:\Users\luoruofeng\Desktop\test\视频片段"
```

# 将 所有“中英文对照”， 所有“跟读”， 所有“磨耳朵”视频拼接起来,形成三部完整的电影
```
movie_opt.exe merge merge3  --path="C:\Users\luoruofeng\Desktop\test\视频片段"
```


# 操作多个包含了有双语srt和视频的动画片的文件夹
```
movie_opt.exe custom custom1  --path="C:\Users\luoruofeng\Desktop\test9"  --segment_second=28
```


# pdf转txt
```
movie_opt.exe pdf pdf_to_txt_pdfplumber --path="C:\Users\luoruofeng\Desktop\test5"
```


# txt转mp3
```
movie_opt.exe pdf split_sentences_2voice --path="C:\Users\luoruofeng\Desktop\test5"
```

