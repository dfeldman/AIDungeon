import twitter
import time
import sys
import os
from story.story_manager import *
from generator.gpt2.gpt2_generator import *
from story.utils import *
from termios import tcflush, TCIFLUSH
import time, sys, os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


try:
    from urllib.parse import urlparse
except ImportError:
     from urlparse import urlparse

consumer_key=os.environ["consumer_key"]
consumer_secret=os.environ["consumer_secret"]
access_token_key=os.environ["access_token_key"]
access_token_secret=os.environ["access_token_secret"]

api = twitter.Api(consumer_key=consumer_key, consumer_secret=consumer_secret, access_token_key=access_token_key, access_token_secret=access_token_secret)

def tweet(msg):
    status=api.PostUpdates(msg)[-1]
    print(status)
    time.sleep(60)
    replies=[]
    while True:
        all_replies = api.GetReplies()
        replies = [x for x in all_replies if x.in_reply_to_status_id==status.id]
        if len(replies) > 0: 
            break
        print("Waiting")
        time.sleep(60)
    replies.sort(key=lambda x:x.favorite_count, reverse=True)
    print(replies[0])
    return replies[0].text

def tweet_numeric(msg, mx):
    val = tweet(msg)
    try:
        val = int(val)
    except:
        val = 0
    if msg > max:
        val = 0
    if msg < 0:
        val = 0
    return val

def select_game():
    with open(YAML_FILE, 'r') as stream:
        data = yaml.safe_load(stream)

    txt="Pick a setting."
    settings = data["settings"].keys()
    for i, setting in enumerate(settings):
        txt += str(i) + ") " + setting +"\n"

    txt+=str(len(settings)) + ") custom"
    choice = tweet_numeric(txt, len(settings)+1)

    if choice == len(settings):
        context = ""
        prompt = tweet("Starting Prompt: ")
        return context, prompt

    setting_key = list(settings)[choice]

    txt = "\nPick a character"
    characters = data["settings"][setting_key]["characters"]
    for i, character in enumerate(characters):
        txt+=str(i) + ") " + character
    character_key = list(characters)[tweet_numeric(txt, len(characters))]

    name = tweet("\nWhat is your name? ")
    setting_description = data["settings"][setting_key]["description"]
    character = data["settings"][setting_key]["characters"][character_key]

    context = "You are " + name + ", a " + character_key + " " + setting_description + \
              "You have a " + character["item1"] + " and a " + character["item2"] + ". "
    prompt_num = np.random.randint(0, len(character["prompts"]))
    prompt = character["prompts"][prompt_num]

    return context, prompt


def play_aidungeon_2():
    upload_story = False

    print("\nInitializing AI Dungeon! (This might take a few minutes)\n")
    generator = GPT2Generator()
    story_manager = UnconstrainedStoryManager(generator)
    print("\n")

    with open('opening.txt', 'r') as file:
        starter = file.read()
    output = starter

    while True:
        if story_manager.story != None:
            del story_manager.story

        print("\n\n")
        context, prompt = select_game()
        tweet(instructions())
        print("\nGenerating story...")

        story_manager.start_new_story(prompt, context=context, upload_story=upload_story)

        print("\n")
        console_print(str(story_manager.story))
        while True:
            action = tweet(output)
            if action == "":
                action = ""
                result = story_manager.act(action)
                output=result

            elif action[0] == '"':
                action = "You say " + action

            else:
                action = action.strip()
                action = action[0].lower() + action[1:]

                if "You" not in action[:6] and "I" not in action[:6]:
                    action = "You " + action

                if action[-1] not in [".", "?", "!"]:
                    action = action + "."

                action = first_to_second_person(action)

                action = "\n> " + action + "\n"

                output = story_manager.act(action)
            if len(story_manager.story.results) >= 2:
                similarity = get_similarity(story_manager.story.results[-1], story_manager.story.results[-2])
                if similarity > 0.9:
                    story_manager.story.actions = story_manager.story.actions[:-1]
                    story_manager.story.results = story_manager.story.results[:-1]
                    output="Woops that action caused the model to start looping. Try a different action to prevent that."
                    continue

            if player_won(result):
                tweet(result + "\n CONGRATS YOU WIN")
                break
            elif player_died(result):
                tweet(result + "\n YOU DIED. GAME OVER.")
                break




if __name__ == '__main__':
    play_aidungeon_2()
