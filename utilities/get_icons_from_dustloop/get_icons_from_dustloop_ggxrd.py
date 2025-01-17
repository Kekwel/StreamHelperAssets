import requests
from bs4 import BeautifulSoup as BS
import json
from pathlib import Path
import sys

sys.setrecursionlimit(100)

dustloop_page = requests.get(
    "https://www.dustloop.com/w/Guilty_Gear_Xrd_REV_2", timeout=30)
dustloop_content = dustloop_page.text
dustloop_soup = BS(dustloop_content, features="html.parser")
character_table = dustloop_soup.findAll(
    'div', {'class': f'div-col columns column-width'})

temp_table = []
for table in character_table:
    if "Kum Haehyun" in str(table):
        temp_table.append(table)

character_table = temp_table

game_id = 36

download_folder_name = "../download_smashgg/download"
base_files_folder_name = f"{download_folder_name}/base_files"
portraits_folder_name = f"{download_folder_name}/full"
icon_folder_name = f"{base_files_folder_name}/icon"
for folder_name in (download_folder_name, base_files_folder_name, portraits_folder_name, icon_folder_name):
    Path(folder_name).mkdir(parents=True, exist_ok=True)

def robust_request(link):
    return_code = 404
    while return_code != 200:
        try:
            response = requests.get(link, timeout=30)
            return_code = response.status_code
        except requests.exceptions.ConnectionError:
            return(robust_request(link))
    return(response)

def get_icon_from_character_name(character_name):
    list_img_tags = dustloop_soup.findAll('img')
    for tag in list_img_tags:
        if (character_name.replace(" ", "_") in tag["src"]) and ("Icon.png" in tag["src"]):
            srcset = tag["srcset"].split(", ")
    url:str = srcset[-1].split(' ')[0]
    if "thumb" in url:
        url = url.replace("/thumb", "")
        url_split = url.split("/")
        url = '/'.join(url_split[:-1])
    return(f"http://dustloop.com{url}")


def get_portrait(character_name, page_link):
    character_page = robust_request(page_link)
    character_page_soup = BS(character_page.text, features="html.parser")
    character_page_links_tag_list = character_page_soup.findAll('a', href=True)
    for tag in character_page_links_tag_list:
        link = tag["href"]
        if ("_Portrait" in link or "_Potrait" in link) and ("File:GGXRD" in link):
            portrait_wiki_link = link
            break
    portrait_wiki_page = robust_request(f"http://dustloop.com{portrait_wiki_link}")
    portrait_wiki_soup = BS(portrait_wiki_page.text, features="html.parser")
    portrait_page_links_tag_list = portrait_wiki_soup.findAll('a', href=True)
    # print(portrait_page_links_tag_list)
    for tag in portrait_page_links_tag_list:
        text = tag.get_text()
        link = tag["href"]
        if (("Original file" in text) and ("_Portrait" in link)) or (("GGXRD" in text) and ("_Portrait.png" in text) and ("_Portrait" in link)):
            break
        if (("Original file" in text) and ("_Potrait" in link)) or (("GGXRD" in text) and ("_Potrait.png" in text) and ("_Potrait" in link)):
            break
    result = f"http://dustloop.com{link}"
    if result:
        return(f"http://dustloop.com{link}")
    else:
        raise("Portait not found")


def get_all_links():
    list_characters_tag = character_table[0].findAll('a', href=True)
    list_characters_page_tag = character_table[0].findAll('a', href=True)

    character_dict = {}

    list_characters = []
    for tag in list_characters_tag:
        character_name = tag["title"].encode("ascii", "ignore").decode()
        if character_name not in list_characters and "Frame Data".lower() not in character_name.lower():
            list_characters.append(character_name)

    list_characters_page = []
    for tag in list_characters_page_tag:
        link = tag["href"]
        link = f"https://dustloop.com{link}"
        if (link not in list_characters_page) and ("Frame_Data" not in link):
            list_characters_page.append(link)

    for i in range(len(list_characters)):
        character_name = list_characters[i].encode("ascii", "ignore").decode().split('/')[-1]
        list_characters[i] = character_name

    for i in range(len(list_characters)):
        character_name = list_characters[i]
        icon_link = get_icon_from_character_name(
            list_characters[i].encode("ascii", "ignore").decode().split('/')[-1])
        portrait_link = get_portrait(
            list_characters[i], list_characters_page[i])
        character_dict[list_characters[i].encode("ascii", "ignore").decode()] = {
            "codename": list_characters[i].replace(' ', '').replace('&', '').replace('.', '').replace('(', '').replace(')', '').replace('-', '').replace("'", ''),
            "portrait_url": portrait_link,
            "icon_url": icon_link
        }

    return(character_dict)


def generate_configs(character_dict):
    with open(f"../download_smashgg/game_data.json", 'rt', encoding='utf-8') as game_data_file:
        game_data = json.loads(game_data_file.read())
    found = False
    for game in game_data:
        if game.get("smashgg_id") == game_id:
            game_name = game.get("name")
            image_type = game.get("image_type")
            challonge_id = game.get("challonge_id")
            found = True

    if not found:
        print("Game not found")
        exit(1)

    description = "Base config to use this game."
    credits = 'Files ripped from Dustloop Wiki'
    version = "1.0"

    config_dict: dict = {
        "name": str(game_name),
        "smashgg_game_id": game_id,
        "challonge_game_id": challonge_id,
        "character_to_codename": {},
        "stage_to_codename": {},
        "version": version,
        "description": str(description),
        "credits": str(credits)
    }

    icon_config_dict = {
        "prefix": "icon_",
        "postfix": "_",
        "type": ["icon"],
        "version": version
    }

    portrait_config_dict = {
        "name": "Portraits",
        "description": "Character portraits",
        "prefix": "full_",
        "postfix": "_",
        "type": ["full"],
        "credits": "",
        "version": version
    }

    for character_name in character_dict.keys():
        config_dict["character_to_codename"][character_name] = {
            "codename": character_dict.get(character_name).get("codename")
        }

    with open(f"{base_files_folder_name}/config.json", 'wt', encoding='utf-8') as main_config_file:
        config_file_content = json.dumps(config_dict, indent=2)
        main_config_file.write(config_file_content)

    with open(f"{icon_folder_name}/config.json", 'wt', encoding='utf-8') as icon_config_file:
        icon_config_file_content = json.dumps(icon_config_dict, indent=2)
        icon_config_file.write(icon_config_file_content)

    with open(f"{portraits_folder_name}/config.json", 'wt', encoding='utf-8') as portrait_config_file:
        portrait_config_file_content = json.dumps(
            portrait_config_dict, indent=2)
        portrait_config_file.write(portrait_config_file_content)

    return config_dict, icon_config_dict, portrait_config_dict


def download_all_images(character_dict: dict, icon_config_dict, portrait_config_dict):
    print(character_dict)
    for character_name in character_dict.keys():
        print(character_name)
        character_data = character_dict.get(character_name)
        icon_filename = f'{icon_folder_name}/{icon_config_dict.get("prefix")}{character_data.get("codename")}{icon_config_dict.get("postfix")}0.png'
        portrait_filename = f'{portraits_folder_name}/{portrait_config_dict.get("prefix")}{character_data.get("codename")}{portrait_config_dict.get("postfix")}0.png'
        with open(icon_filename, 'wb') as f:
            icon_file = robust_request(character_data.get("icon_url"))
            f.write(icon_file.content)
        with open(portrait_filename, 'wb') as f:
            portrait_file = robust_request(character_data.get("portrait_url"))
            f.write(portrait_file.content)


character_dict = get_all_links()
print(json.dumps(character_dict, indent=2))
main_config_dict, icon_config_dict, portrait_config_dict = generate_configs(
    character_dict)
download_all_images(character_dict, icon_config_dict, portrait_config_dict)
