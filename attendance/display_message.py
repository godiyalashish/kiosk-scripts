import sys
import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# Raspberry Pi pin configuration:
RST = None  # on the PiOLED this pin isn't used
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0

# Initialize the SSD1306 display
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)
disp.begin()

# Clear the display
disp.clear()
disp.display()

# Create a blank image for drawing
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image
draw = ImageDraw.Draw(image)


font = ImageFont.load_default()


# Load a smaller font
# font = ImageFont.truetype('/home/admin/Desktop/faceRecognition/RobotoRegular.ttf')

# Get texts to display from command line arguments
texts = sys.argv[1:]

# Calculate text positions
text_heights = []
total_height = 0
for text in texts:
    text_width, text_height = draw.textsize(text, font)
    text_heights.append(text_height)
    total_height += text_height

# Calculate total text height and space between lines
total_text_height = sum(text_heights)
space_between_lines = (height - total_text_height) // (len(texts) + 1)

# Starting y position for drawing text
y = space_between_lines

# Clear the image and draw the text
draw.rectangle((0, 0, width, height), outline=0, fill=0)
for text, text_height in zip(texts, text_heights):
    text_width, _ = draw.textsize(text, font)
    x = (width - text_width) // 2
    draw.text((x, y), text, font=font, fill=255)
    y += text_height + space_between_lines

# Display the image
disp.image(image)
disp.display()
