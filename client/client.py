from aiohttp import ClientSession
import asyncio
import signal
import os
from dotenv import load_dotenv
from utils.logger import logger
from modules.handle_speech import SpeechHandler


# This flag will be used to stop the script
stop_flag = False

# Replace 'MICROPHONE_INDEX' with the index of your microphone
MICROPHONE_INDEX = 1

load_dotenv()

key_phrases = ['ava', 'eva']
current_user = None
speech = SpeechHandler()

def signal_handler(signal, frame):
    global stop_flag
    stop_flag = True
    logger.info('Stopping...')
    exit(0)

async def main():
    global stop_flag    
    global current_user
    client_server_route = "http://10.0.0.229:5001/"

    # login on the server
    try:
        username = os.getenv('SERVER_USERNAME')
        password = os.getenv('SERVER_PASSWORD')
        current_user = None

        try: 
            # Login
            async with ClientSession() as client:
                response = await client.post(f'{client_server_route}/user/login', json={'username': username, 'password': password})
                response_data = await response.json()
                current_user = response_data['user']
                logger.info(f"Logged in as: {current_user['username']}")
        except Exception as e:
            logger.error(f'Error in login: {e}')
            stop_flag = True

        if current_user:
            # Start listening
            try:
                while not stop_flag:
                    text = await speech.start_listening()
                    
                    logger.info(f'Sending message: {text}')
                    async with ClientSession() as client:
                        formated_request = {
                            "status": "request",
                            "user": current_user,
                            "data": {
                                "type": "text",
                                "content": text
                            }
                        }
                        logger.info(f'Sending request: {formated_request}')
                        response = await client.post(f'{client_server_route}/send_message/{current_user["_id"]}', json=formated_request)
                        if response is not None:
                            response_data = await response.json()
                            logger.info(f'Response: {response_data}')

                            # Convert text to speech in asyncio event loop
                            loop = asyncio.get_event_loop()
                            await loop.run_in_executor(None, speech.text_to_speech, response_data["data"]["content"])

            except Exception as e:
                logger.error(f'Error getting speech: {e}')
                stop_flag = True
        else:
            stop_flag = True
    except Exception as e:
        logger.error(f'Error in main: {e}')
        stop_flag = True

# Set the signal handler
signal.signal(signal.SIGINT, signal_handler)

signal.signal(signal.SIGTERM, signal_handler)
        
# Run the main function
asyncio.run(main())