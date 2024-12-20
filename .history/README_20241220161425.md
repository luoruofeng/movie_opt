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

## 将srt字幕转化ass字幕文件
```
movie_opt.exe subtitle srt2ass --path="C:\Users\luoruofeng\Desktop\test"
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


##
```
movie_opt.exe ai get_hard_words_and_set_color --path="C:\Users\luoruofeng\Desktop\test2\test.srt"
```
