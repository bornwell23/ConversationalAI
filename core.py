import threading
import time
import sys
import signal
import msvcrt
import queue
import httpx


# Define multiple LLM endpoints dynamically
OLLAMA_ENDPOINTS = {
    "granite3.3:2b": {"model": "granite3.3:2b", "queue": queue.Queue(), "name": "Sapphira", "description": "Your D&D character is an elf druid named Kalina Eldaran. She is Elrion's brother. She is wise and deeply connected to nature. Sometimes she can be a bit aloof, but cares deeply for her friends and the natural world."},
    "granite3.3:2b_2": {"model": "granite3.3:2b", "queue": queue.Queue(), "name": "Jasper", "description": "Your D&D character is an elf ranger named Elrion Eldaran. He is Kalina's brother. He is a skilled tracker and hunter, with a deep respect for the balance of nature. He often serves as the group's scout, leading them through the wilderness."},
    "granite3.3:2b_3": {"model": "granite3.3:2b", "queue": queue.Queue(), "name": "Garnet", "description": "Your D&D character is a fighter dwarf named Thrain Stonefist. He is brave and strong, with a deep sense of honor. He often acts as the protector of the group, ready to face any challenge head-on."},
    "granite3.3:2b_4": {"model": "granite3.3:2b", "queue": queue.Queue(), "name": "Ruby", "description": "Your D&D character is a human cleric named Lira Allaster. She is compassionate and wise, always seeking to heal and help others. Her faith guides her actions, and she often serves as the moral compass of the group."},
}


class GlobalFlags:
    stop_event = threading.Event()  # Allows user to stop conversation
    paused = False  # Allows user to stop conversation
    data_pending = False  # Flag to indicate if data is pending
    time_since_last_message = time.time()  # Timer to track time without messages
    test_mode = False  # Flag for test mode, enters some test data for quick testing
    base_url = "http://localhost:11434"  # Base URL for Ollama API
    url  = f"{base_url}/api/chat"  # Default URL for Ollama API
    common_directions = f"You are playing Dungeons and Dragons with other players {', '.join(m['name'] for m in OLLAMA_ENDPOINTS.values())}, and the user who is the Dungeon Master (DM). " \
                        "You should primarily focus on responding to the user which is the DM." \
                        "You will respond with your character's actions and dialogue in context-appropriate ways, but also feel free to ask questions about the world, your character, or the game mechanics. " \
                        "You must only respond to messages that are relevant to your character, and ignore messages that are not directed at you. " \
                        "You must only respond with your character's actions and dialogue, and not with any other character's actions or dialogue. " \
                        "You must not speak for the DM, but you can ask questions or make suggestions to the DM. " \
                        "You don't always need to respond to every message either, if there is nothing relevant to say, you can simply reply 'pass' and wait for the next message. " \


class Message:
    """Represents a message in the conversation."""
    def __init__(self, role, content):
        self.role = role
        self.content = content

    def to_dict(self):
        return {"role": self.role, "content": self.content}


def add_message_to_queue(model, role, content):
    """Adds a message to the specified model's queue."""
    if model in OLLAMA_ENDPOINTS:
        OLLAMA_ENDPOINTS[model]["queue"].put(Message(role, content))
        GlobalFlags.data_pending = True
        GlobalFlags.time_since_last_message = time.time()
    else:
        print(f"DEBUG: Model {model} not found in endpoints.")


def add_message_to_all_queues(role, content):
    """Adds a message to all model queues."""
    for model_key in OLLAMA_ENDPOINTS:
        add_message_to_queue(model_key, role, content)


def query_ollama(client, model):
    """Sends prompt to specified LLM model."""
    messages: queue.Queue[Message] = OLLAMA_ENDPOINTS[model]["queue"]
    payload = {"model": OLLAMA_ENDPOINTS[model]["model"], "stream": False, "messages": [m.to_dict() for m in messages.queue]}
    response = client.post(GlobalFlags.url, json=payload)
    data = response.json()
    OLLAMA_ENDPOINTS[model]["queue"].queue.clear()
    return data.get("message", {}).get("content", "No response from LLM.")


def llm_conversation():
    """Continuously cycles responses between all models, with optional user input."""
    with httpx.Client(timeout=15) as client:
        print("DEBUG: Starting LLM loop")
        # Check connection to Ollama before starting conversation loop
        try:
            resp = client.get(GlobalFlags.base_url)
            if resp.status_code == 200:
                print("DEBUG: Successfully connected to Ollama API.")
            else:
                print(f"DEBUG: Ollama API returned status {resp.status}.")
        except Exception as e:
            print(f"DEBUG: Could not connect to Ollama API: {e}")
            GlobalFlags.stop_event.set()
            return
        
        for model in OLLAMA_ENDPOINTS:
            # Initialize each model with a common prompt
            initial_message = Message("system", f"Your name is {OLLAMA_ENDPOINTS[model]['name']}\n{GlobalFlags.common_directions}\n{OLLAMA_ENDPOINTS[model]['description']}")
            OLLAMA_ENDPOINTS[model]["queue"].put(initial_message)
            print(f"DEBUG: Initialized {model}")

        while not GlobalFlags.stop_event.is_set():
            if GlobalFlags.paused:
                print("Conversation paused. Press ESC to resume or type a message.")
                while GlobalFlags.paused:
                    time.sleep(1)
            while not GlobalFlags.data_pending:
                time.sleep(1)
                elapsed = time.time() - GlobalFlags.time_since_last_message
                if elapsed > 120:
                    print("DEBUG: No messages received for a long time. Ending conversation.")
                    GlobalFlags.stop_event.set()
                    return
                elif elapsed > 30:
                    print("Do you want to continue talking? Type a message to continue, or Ctrl+C to stop.")
            for model in OLLAMA_ENDPOINTS:
                response = query_ollama(client, model)
                for other_model in OLLAMA_ENDPOINTS:
                    if other_model != model:
                        # print(f"DEBUG: Adding {model}'s response to {other_model}'s queue: {response}")
                        OLLAMA_ENDPOINTS[other_model]["queue"].put(Message(OLLAMA_ENDPOINTS[model]["name"], response))
                print(f"\n\n{OLLAMA_ENDPOINTS[model]['name']}:\n{response}\n\n")

                time.sleep(1)  # Small delay for more natural interaction
    print("DEBUG: Conversation loop ended. No more messages to process.")


def handle_user_input():
    """Runs in a separate thread to allow user to interact with or end the conversation."""
    def signal_handler(sig, frame):
        print("\nDEBUG: Conversation stopped by Ctrl+C.")
        GlobalFlags.stop_event.set()

    signal.signal(signal.SIGINT, signal_handler)

    print("Press ESC to stop the conversation, or type a message and press Enter.")
    message = ""
    while not GlobalFlags.stop_event.is_set():
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\x1b':  # ESC key
                if GlobalFlags.paused:
                    GlobalFlags.paused = False
                    print("ESC pressed, resuming conversation.")
                else:
                    GlobalFlags.paused = True
                    print("ESC pressed, pausing conversation. Press ESC again to resume or type a message.")
            elif key == b'\r':  # Enter key
                print()  # Move to next line
                if message.strip():
                    add_message_to_all_queues("user", message)
                    # print(f"DEBUG: You entered: {message}")
                message = ""
            elif key == b'\x08':  # Backspace
                if message:
                    message = message[:-1]
                    # Move cursor back, erase char, move cursor back again
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            else:
                try:
                    char = key.decode('utf-8')
                    message += char
                    sys.stdout.write(char)
                    sys.stdout.flush()
                except UnicodeDecodeError:
                    print(f"DEBUG: Non-decodable key '{key}' pressed, ignoring.")
        time.sleep(0.1)


def main():
    if GlobalFlags.test_mode:
        print("DEBUG: Running in test mode.")
        background_thread = threading.Thread(target=llm_conversation, daemon=True)
        background_thread.start()
        time.sleep(2)
        add_message_to_all_queues("user", "What is your name?")
        background_thread.join()
        # llm_conversation()
    else:
        print("DEBUG: Starting main conversation loop.")
        background_thread = threading.Thread(target=llm_conversation, daemon=True)
        background_thread.start()
        handle_user_input()
    

if __name__ == "__main__":
    main()