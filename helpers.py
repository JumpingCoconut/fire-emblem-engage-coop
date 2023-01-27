import re
import interactions

# Stupid little function that just takes a letter and makes it a color
def assign_color_to_user(username):
        username_as_color_int = int(ord(username[0])) % 7
        color = interactions.Color.red() # Default
        if username_as_color_int == 0: 
            color = interactions.Color.blurple()
        elif username_as_color_int == 1: 
            color = interactions.Color.green()
        elif username_as_color_int == 2: 
            color = interactions.Color.yellow()
        elif username_as_color_int == 3: 
            color = interactions.Color.fuchsia()
        elif username_as_color_int == 4: 
            color = interactions.Color.red()
        elif username_as_color_int == 5: 
            color = interactions.Color.white()
        elif username_as_color_int == 6: 
            color = interactions.Color.black()
        return color

def stringToFilename(string):
    # Replace all non-alphanumeric characters with underscores
    filename = re.sub(r'[^\w\s]', '_', string)
    # Replace all whitespace with underscores
    filename = re.sub(r'\s+', '_', filename)
    # Convert to lowercase
    filename = filename.lower()
    return filename