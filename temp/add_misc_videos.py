from ruamel.yaml import YAML

DONT_IGNORE = "temp/dont_ignore.txt"
IGNORE = "temp/ignore.txt"

def create_yaml_from_dict(data, fn="output.txt"):
    with open(fn, "w") as f:
            yaml = YAML()
            yaml.default_flow_style = False
            yaml.dump(data, f)

def TextFileToDictionary():
    data = [] # Blank list
    with open(IGNORE, "r") as file:  
        sections = file.read().split("\n\n")
        for section in sections:  
            lines = section.split("\n")
            if len(lines) < 2:         
                return "ERROR!"
            data.append({
                "video_type": "Ignored",
                "video_title": lines[0],
                "url": lines[1],
                "ignore": "true",
                })
    return data
            
data = TextFileToDictionary()
# with open(DONT_IGNORE, "r") as di:
#     data = di.read()

#     data = data.split("\n")
#     list_of_lists = [row.split("\n") for row in data]
#     final_list = [{"video_type": row[0].strip(),
#                    "url": row[1].strip(),
#                    "album": row[2].strip()} for row in list_of_lists]

    
        
        
        # data = {}
        # data["video_title"] = line.strip()
        # data["url"] = line.strip()
        # data["album"] = line.strip()
        # blank = 
        # if not blank == "\n":
        #     print(f"Should be blank line but its actually {blank}")
        #     exit()
        # vid_list.append(data)
    
create_yaml_from_dict(data)