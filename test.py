import random

filename = "maps/easy/zobzob.txt"

with open(filename, "w", encoding="utf-8") as f:
    f.write("nb_drones: 1\n")
    f.write("start_hub: start -2 0\n")
    nb_layers = 30
    f.write(f"end_hub: end {nb_layers + 1} 0\n")

    layers: list[list[str]] = []
    for layer in range(nb_layers):
        layers.append([])
        for i in range(-8, 8):
            stri = str(i).replace("-", "m")
            layers[layer].append(f"n{layer}_{stri}")
            zone = random.choice(["restricted", "normal", "priority"])
            chance = random.randint(1, 100)
            if chance < 30:
                zone = "blocked"
            color = "yellow"
            if zone == "restricted":
                color = "red"
            elif zone == "priority":
                color = "cyan"
            elif zone == "blocked":
                color = "black"
            f.write(f"hub: n{layer}_{stri} {layer} {i} [color={color} zone={zone}]\n")

    for i in range(len(layers)):
        if i == 0:
            for node in layers[i]:
                f.write(f"connection: start-{node}\n")
        else:
            for nodei in range(len(layers[i])):
                f.write(
                    f"connection: {layers[i-1][nodei]}-{layers[i][nodei]}\n")
        for nodei in range(len(layers[i])):
            if nodei > 0:
                f.write(
                        f"connection: {layers[i][nodei - 1]}-{layers[i][nodei]}\n")
            if i < len(layers) - 1 and nodei < len(layers[i]) - 1:
                f.write(
                    f"connection: {layers[i][nodei]}-{layers[i + 1][nodei + 1]}\n")
            if i < len(layers) - 1 and nodei > 0:
                f.write(
                    f"connection: {layers[i][nodei]}-{layers[i + 1][nodei - 1]}\n")

    for node in layers[nb_layers - 1]:
        f.write(f"connection: end-{node}\n")