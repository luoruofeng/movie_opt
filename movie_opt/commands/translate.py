import sqlite3
import json
from google.cloud import translate_v2 as translate
import os

def google_translate_demo(text, target_language="zh"):
    """
    Translate the input text into the target language using Google Translate API.

    Args:
        text (str): Text to be translated.
        target_language (str): Language code to translate the text into (default: Chinese - "zh").

    Returns:
        str: Translated text.
    """
    # Initialize the Google Translate client
    translate_client = translate.Client()

    # Perform the translation
    result = translate_client.translate(text, target_language=target_language)

    # Extract and return the translated text
    return result['translatedText']


def find_db_word(args):
    content = args.word

    # Initialize SQLite connection
    # 相对路径
    relative_db_path = '../db/english_data.db'
    # 获取脚本所在的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 拼接绝对路径
    db_path = os.path.abspath(os.path.join(script_dir, relative_db_path))
    print(f"Absolute DB Path: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
       # Query all columns from the english_data table
        query = "SELECT * FROM english_data WHERE word = ?"
        cursor.execute(query, (content,))
        rows = cursor.fetchall()

        # Convert the result to a JSON list of dictionaries (to handle multiple columns)
        column_names = [description[0] for description in cursor.description]
        result_list = [dict(zip(column_names, row)) for row in rows]
        result_json = json.dumps(result_list, ensure_ascii=False)

        # Check if the list is not empty
        if result_list:
            print("Found in database:", result_json)
            return result_list[0]  # Return the first matching row as a dictionary
        else:
            return None

    except sqlite3.Error as e:
        print("SQLite error:", e)
        return None

    finally:
        cursor.close()
        conn.close()