#!/usr/bin/python
# -*- coding: utf-8 -*-
#--------------------------------------
#
# The LCD Driver portion of this code
# created by:
#    ___  ___  _ ____
#   / _ \/ _ \(_) __/__  __ __
#  / , _/ ___/ /\ \/ _ \/ // /
# /_/|_/_/  /_/___/ .__/\_, /
#                /_/   /___/
#
#  lcd_16x2.py
#  20x4 LCD Test Script with
#  backlight control and text justification
#
# Author : Matt Hawkins
# Date   : 06/04/2015
#
# https://www.raspberrypi-spy.co.uk/
#--------------------------------------
#
# The Moode audio portion of the code
# created by:
#
# Author : Bryce Jeannotte
# Date   : 08/31/2017
#
#--------------------------------------
# The wiring for the LCD is as follows:
# 1 : GND
# 2 : 5V
# 3 : Contrast (0-5V)*
# 4 : RS (Register Select)
# 5 : R/W (Read Write)       - GROUND THIS PIN
# 6 : Enable or Strobe
# 7 : Data Bit 0             - NOT USED
# 8 : Data Bit 1             - NOT USED
# 9 : Data Bit 2             - NOT USED
# 10: Data Bit 3             - NOT USED
# 11: Data Bit 4
# 12: Data Bit 5
# 13: Data Bit 6
# 14: Data Bit 7
# 15: LCD Backlight +5V**
# 16: LCD Backlight GND

#import
import os
import RPi.GPIO as GPIO
import time

# Define GPIO to LCD mapping
# Change this table to match the BGM GPIO
# numbers to your display wiring
LCD_RS = 7
LCD_E  = 8
LCD_D4 = 25
LCD_D5 = 24
LCD_D6 = 23
LCD_D7 = 14
LED_ON = 15

# Define some device constants
LCD_WIDTH = 20    # Maximum characters per line
LCD_CHR = True
LCD_CMD = False

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

# Scrolling constants
ST_DELAY = 1.5     # Delay before scrolling first line
SF_DELAY = .5      # Delay before scrolling second and third line
SC_DELAY = .25     # Delay between scrolling characters
SC_COUNT = 2       # Number of characters to scroll at one time
SC_REPEAT = True   # Continous scrolling switch
SR_DELAY = 10      # Delay before repeating the scrolling
VD_DISPLAY = True  # Volume display switch
VD_DELAY = 2.5     # Number of seconds to display volume change

# Cool our jets
time.sleep(15)

# currentsont.txt timestamp
csts = os.stat("/var/local/www/currentsong.txt").st_mtime
ivol = 0

def main():

 GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
 GPIO.setup(LCD_E, GPIO.OUT)  # E
 GPIO.setup(LCD_RS, GPIO.OUT) # RS
 GPIO.setup(LCD_D4, GPIO.OUT) # DB4
 GPIO.setup(LCD_D5, GPIO.OUT) # DB5
 GPIO.setup(LCD_D6, GPIO.OUT) # DB6
 GPIO.setup(LCD_D7, GPIO.OUT) # DB7
 GPIO.setup(LED_ON, GPIO.OUT) # Backlight enable

 # Initialise display
 splash_screen()
 lcd_backlight(False)
 while True:
     global csts, ivol
     # Has currentsong.txt changed?
     if (csts <> os.stat("/var/local/www/currentsong.txt").st_mtime):
         csts = os.stat("/var/local/www/currentsong.txt").st_mtime

         try:
             # Read the currentsong.txt file and format the diplay lines
             with open("/var/local/www/currentsong.txt","r") as currentsong:
                 lines = currentsong.readlines()

                 a,artist = lines[1].split("=")
                 a,album = lines[2].split("=")
                 a,title = lines[3].split("=")
                 a,year = lines[6].split("=")
                 a,encoded = lines[8].split("=")
                 a,bitrate = lines[9].split("=")
                 a,volume = lines[10].split("=")
                 a,mute = lines[11].split("=")
                 a,status = lines[12].split("=")

                 # Remove white space
                 artist = artist.strip()
                 album = album.strip()
                 title = title.strip()
                 year = year.strip()
                 encoded = encoded.strip()
                 bitrate = bitrate.strip()
                 volume = volume.strip()
                 mute = mute.strip()
                 status = status.strip()

                 # Remove accented characters for LCD display
                 artist = remove_accent(artist)
                 album = remove_accent(album)
                 title = remove_accent(title)

                 # Flip bit depth and sample rate
                 if ("/" in encoded):
                     encoded_only = encoded.split(" ",1)
                     bitdepth,samplerate = encoded_only[0].split("/")
                     encoded = "%s-%s" % (samplerate, bitdepth)

                 # Build the display lines
                 if status == "stop":
                     line1 = " moOde Audio Player"
                     line2 = "We are done for now!"
                     line3 = ""
                     line4 = "  <== Stopped ==>"
                lcd_backlight(False)
                 else:
                     if artist == "Radio station":
                    lcd_backlight(True)
                         line1 = artist
                         line2 = album
                         if (title[:5] == "http:"):
                             line3 = "Internet stream"
                         else:
                             line3 = title
                     else:
                    lcd_backlight(True)
                         line1 = artist
                         line2 = title
                         line3 = album
                     if status == "pause":
                         line4 = "   <== Paused ==>"
                    lcd_backlight(False)
                     elif VD_DISPLAY:
                         if mute == "1":
                             ivol = -1
                             line4 = "   <== Muted ==>"
                             lcd_init()
                         else:
                             if ivol == volume:
                                 line4 = "%s | %s" % (encoded, bitrate)
                             else:
                                 ivol = volume
                                 line4 = "%s %s%s" % (" <== Volume", volume, "% ==>")
                     else:
                         line4 = "%s | %s" % (encoded, bitrate)

                 # Send the lines to the display
                 lcd_string(line1,LCD_LINE_1,1)
                 lcd_string(line2,LCD_LINE_2,1)
                 lcd_string(line3,LCD_LINE_3,1)
                 lcd_string(line4,LCD_LINE_4,1)

                 # Close currentsong.txt
                 currentsong.close()

                 # Check if we need to display volume change
                 if ("Volume" in line4 and VD_DISPLAY):
                     sleep_for(VD_DELAY)
                     csts = -1

                 # Check if we need to scroll
                 if (status == "play" and SC_REPEAT):
                     rc = 0
                     while rc>= 0:
                    rc = check_scrolling(line1, line2, line3, csts)
                 elif (status == "play"):
                check_scrolling(line1, line2, line3, csts)

         except Exception:
             pass

     else:
         sleep_for(.3)

def splash_screen():
 # Splash screen text
 lcd_init()
 line1 = "Welcome to the"
 line2 = "moOde Audio Player"
 line3 = "--------------------"
 line4 = "Enjoy the Music!"

 # Display the splash screen
 lcd_string(line1,LCD_LINE_1,2)
 lcd_string(line2,LCD_LINE_2,2)
 lcd_string(line3,LCD_LINE_3,2)
 lcd_string(line4,LCD_LINE_4,2)

def remove_accent(text):
 # Remove Accents
 text = text.replace("à", "a")
 text = text.replace("á", "a")
 text = text.replace("â", "a")
 text = text.replace("ã", "a")
 text = text.replace("ä", "a")
 text = text.replace("è", "e")
 text = text.replace("é", "e")
 text = text.replace("ê", "e")
 text = text.replace("ë", "e")
 text = text.replace("ì", "i")
 text = text.replace("í", "i")
 text = text.replace("î", "i")
 text = text.replace("ï", "i")
 text = text.replace("ñ", "n")
 text = text.replace("ò", "o")
 text = text.replace("ó", "o")
 text = text.replace("ô", "o")
 text = text.replace("õ", "o")
 text = text.replace("ö", "o")
 text = text.replace("ù", "u")
 text = text.replace("ú", "u")
 text = text.replace("û", "u")
 text = text.replace("ü", "u")
 text = text.replace("ý", "y")
 text = text.replace("ÿ", "y")
 text = text.replace("ç", "c")
 return text

def check_scrolling(line1, line2, line3, csts):
 # Check if display line needs to be scrolled
                     S_DELAY = True
                     if (len(line1) > LCD_WIDTH):
                         S_DELAY = False
                         time.sleep(ST_DELAY)
                         # Scroll Line 1
                         rc = scroll_line(line1, LCD_LINE_1, csts)
                         if rc < 0:
                             return rc

                     if (len(line2) > LCD_WIDTH):
                         if S_DELAY:
                             S_DELAY = False
                             time.sleep(ST_DELAY)
                         else:
                             time.sleep(SF_DELAY)
                         # Scroll Line 2
                         rc = scroll_line(line2, LCD_LINE_2, csts)
                         if rc < 0:
                             return rc

                     if (len(line3) > LCD_WIDTH):
                         if S_DELAY:
                             S_DELAY = False
                             time.sleep(ST_DELAY)
                         else:
                             time.sleep(SF_DELAY)
                         # Scroll Line 3
                         rc = scroll_line(line3, LCD_LINE_3, csts)
                         if rc < 0:
                             return rc

                     if (SC_REPEAT and not S_DELAY):
                         rc = sleep_for(SR_DELAY)
                         return rc
                     else:
                         rc = sleep_for(.3)
                         return rc

def scroll_line(text, line, csts):
 # Scroll display line
 if (len(text) % SC_COUNT == 0):
     line_length = len(text) + 1
 else:
     line_length = len(text) + SC_COUNT
 for num in xrange(SC_COUNT,line_length,SC_COUNT):
     if (csts <> os.stat("/var/local/www/currentsong.txt").st_mtime):
         return -1
     scrollpart = text[num:num + 20]
     lcd_string(scrollpart,line,1)
     if scrollpart == "":
         time.sleep(SF_DELAY)
     else:
         time.sleep(SC_DELAY)
 lcd_string(text,line,1)
 return 0

def sleep_for(count):
 # Sleep for count seconds and check for exit every .1 seconds
 count = int((count * 10)//1)
 for num in xrange(1,count,1):
     if (csts <> os.stat("/var/local/www/currentsong.txt").st_mtime):
         return -1
     else:
         time.sleep(.1)
 return 0

def lcd_init():
 # Initialise display
 lcd_byte(0x33,LCD_CMD) # 110011 Initialise
 lcd_byte(0x32,LCD_CMD) # 110010 Initialise
 lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
 lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
 lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
 lcd_byte(0x01,LCD_CMD) # 000001 Clear display
 time.sleep(E_DELAY)

def lcd_byte(bits, mode):
 # Send byte to data pins
 # bits = data
 # mode = True  for character
 #        False for command

 GPIO.output(LCD_RS, mode) # RS

 # High bits
 GPIO.output(LCD_D4, False)
 GPIO.output(LCD_D5, False)
 GPIO.output(LCD_D6, False)
 GPIO.output(LCD_D7, False)
 if bits&0x10==0x10:
     GPIO.output(LCD_D4, True)
 if bits&0x20==0x20:
     GPIO.output(LCD_D5, True)
 if bits&0x40==0x40:
     GPIO.output(LCD_D6, True)
 if bits&0x80==0x80:
     GPIO.output(LCD_D7, True)

# Toggle 'Enable' pin
 lcd_toggle_enable()

 # Low bits
 GPIO.output(LCD_D4, False)
 GPIO.output(LCD_D5, False)
 GPIO.output(LCD_D6, False)
 GPIO.output(LCD_D7, False)
 if bits&0x01==0x01:
     GPIO.output(LCD_D4, True)
 if bits&0x02==0x02:
     GPIO.output(LCD_D5, True)
 if bits&0x04==0x04:
     GPIO.output(LCD_D6, True)
 if bits&0x08==0x08:
     GPIO.output(LCD_D7, True)

 # Toggle 'Enable' pin
 lcd_toggle_enable()

def lcd_toggle_enable():
 # Toggle enable
 time.sleep(E_DELAY)
 GPIO.output(LCD_E, True)
 time.sleep(E_PULSE)
 GPIO.output(LCD_E, False)
 time.sleep(E_DELAY)

def lcd_string(message,line,style):
 # Send string to display
 # style=1 Left justified
 # style=2 Centred
 # style=3 Right justified

 if style==1:
     message = message.ljust(LCD_WIDTH," ")
 elif style==2:
     message = message.center(LCD_WIDTH," ")
 elif style==3:
     message = message.rjust(LCD_WIDTH," ")

 lcd_byte(line, LCD_CMD)

 for i in range(LCD_WIDTH):
     lcd_byte(ord(message[i]),LCD_CHR)

def lcd_backlight(flag):
 # Toggle backlight on-off-on
 GPIO.output(LED_ON, flag)

if __name__ == '__main__':

 try:
     main()
 except KeyboardInterrupt:
     pass
 finally:
     lcd_init()
     GPIO.cleanup()