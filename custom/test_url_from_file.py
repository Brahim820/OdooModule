from urllib import urlopen


def load_urls_from_file(file_path):
    try:
        with open(file_path) as f:
            content = f.readline()
            return content
    except FileNotFoundError:
        print("prafule" + file_path)
        exit(2)
    response = urlopen(file_path)
    