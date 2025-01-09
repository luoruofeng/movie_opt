import os
import subprocess

def convert_mp4_to_mkv(directory="."):
    """
    遍历当前目录中的所有 MP4 文件，并将它们转换为 MKV 格式。
    
    Args:
        directory (str): 目标目录，默认为当前目录。
    """
    # 获取当前目录中所有 MP4 文件
    files = [f for f in os.listdir(directory) if f.lower().endswith(".mp4")]
    
    if not files:
        print("未找到任何 MP4 文件。")
        return
    
    # 遍历文件并进行转换
    for file in files:
        mp4_path = os.path.join(directory, file)
        mkv_path = os.path.join(directory, os.path.splitext(file)[0] + ".mkv")
        
        print(f"正在将 {mp4_path} 转换为 {mkv_path}...")
        
        # 使用 ffmpeg 转换 MP4 为 MKV
        result = subprocess.run(
            ["ffmpeg", "-i", mp4_path, "-c:v", "copy", "-c:a", "copy", mkv_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        if result.returncode == 0:
            print(f"转换成功: {mkv_path}")
        else:
            print(f"转换失败: {mp4_path}")
            print(result.stderr.decode())
    
    print("转换完成！")

if __name__ == "__main__":
    convert_mp4_to_mkv()
