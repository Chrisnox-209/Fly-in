import os

folder_maps = "./maps"
list_folder = []
for subfolder in os.listdir(folder_maps):
    path = os.path.join(folder_maps, subfolder)
    if os.path.isdir(path) is True:
        list_folder.append(path)

print()
for folder in list_folder:
    print(f"\n{str(folder):-^50}")
    for file in os.listdir(folder):
        print(file)
print()


text = "   start_hub     :    hub    0    0    [zone=restricted color=red]"

left, right = text.split(":", 1)
left = left.strip()
print(left)


hub_part = right[:right.index("[")].strip()
print(hub_part)

tags = right[right.index("["):].strip()
print(tags)
