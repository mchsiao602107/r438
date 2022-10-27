from parse import parse

increment = (-12)

tsn_count = 40
filenames = ["mesh-iso40-aud20-01-a.yaml", "mesh-iso40-aud20-01-b.yaml"]
for filename in filenames:
    count, lines = 0, list()
    with open("./streams/" + filename, "r") as my_file:
        for line in my_file:
            result = parse("  size: {}\n", line)
            if result and count < tsn_count:
                lines.append("  size: {}\n".format(int(result[0]) + increment))
                count += 1
            else:
                lines.append(line)
    with open("./streams/" + filename, "w") as my_file:
        my_file.writelines(lines)