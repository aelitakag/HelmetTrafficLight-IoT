import requests

# server address
SERVER_URL = "http://192.168.54.209:5000/analyze"


def send_image(image_path):
    try:
        # send image to server
        with open(image_path, "rb") as img:
            files = {"image": img}
            response = requests.post(SERVER_URL, files=files)

        # return response if successful
        if response.status_code == 200:
            return response.json()

        return None

    except Exception:
        return None


if __name__ == "__main__":
    test_path = "photo/latest.jpg"
    result = send_image(test_path)

    if result:
        print(result)
        
        