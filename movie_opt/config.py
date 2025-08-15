# config.py

# The model name for the AI.使用的本地ai模型
QWEN_MODEL_NAME = "qwen2.5:32b"

# The filter score for picture command.过滤超过FILTER_SCORE分的字幕
FILTER_SCORE = 4

# The filter count for picture and subtitle command.过滤超过FILTER_COUNT个字幕的视频
FILTER_COUNT = 11

#过滤超过了平均长度+FILTER_MORE_COUNT单词数量的字幕
FILTER_MORE_COUNT = 4

# The number of composite images to generate.生成图片数量
COMPOSITE_IMAGE_COUNT = 11