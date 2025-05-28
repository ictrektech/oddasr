import requests


def test_stream():
    # 设置服务的 URL
    url = "http://127.0.0.1:12340/v1/asr"

    # 准备音频文件路径
    audio_path = "./test_cn_male_9s.wav"

    # 定义 hotwords
    hotwords = "小落 小落同学 奥德元 小奥"

    # 发送 POST 请求
    with open(audio_path, "rb") as audio_file:
        response = requests.post(url, files={"audio": audio_file}, data={"hotwords": hotwords, "mode": "file"})

    # 输出结果
    if response.status_code == 200:
        try:
            print("Recognition Result:", response.json()["text"])
        except ValueError:
            print("Non-JSON response:", response.text)  # Print the raw response
    else:
        print("Error:", response.text)  # Print the raw error message


def test_file(output_format: str = "txt"):
    # 设置服务的 URL
    url = "http://127.0.0.1:12340/v1/asr"
    # 准备音频文件路径
    audio_path = "./aketao.wav"
    # 定义 hotwords
    hotwords = "小落 小落同学 奥德元 小奥"
    # 打开音频文件
    with open(audio_path, "rb") as audio_file:
        # 发送 POST 请求
        response = requests.post(url, files={"audio": audio_file}, data={"hotwords": hotwords, "mode": "file", "output_format": output_format})
        # 输出结果
        if response.status_code == 200:
            try:
                print("Recognition Result:", response.json()["text"])
            except ValueError:
                print("Non-JSON response:", response.text)  # Print the raw response
        else:
            print("Error:", response.text)  # Print the raw error message


if __name__ == "__main__":
    # test_file("txt")
    test_file("spk")
    # test_file("srt")
