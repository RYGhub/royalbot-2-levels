import requests
import asyncio
import functools
loop = asyncio.get_event_loop()

# Load Telegram API key from the telegramtoken.txt file
file = open("telegram.txt", "r")
token = file.read()
file.close()

# Send a message
async def send_message(msg: str, to: int):
    # Send the message
    params = {
        "chat_id": to,
        "text": msg
    }
    r = loop.run_in_executor(None, functools.partial(requests.get, params=params),
                             "https://api.telegram.org/bot{token}/sendMessage".format(token=token))
    if r.status_code == 200:
        return
    else:
        raise Exception("Qualcosa è andato storto su Telegram. Ops.")