#!/usr/bin/python
#----------------------------------------
# Determinare la soundcard con il comando:
# cat /proc/asound/cards
# da inserire poi nel cmd6 e cmd7
#----------------------------------------
import smbus
import time
import os;
import subprocess;
str_pad = " " * 16  

# Define some device parameters
I2C_ADDR  = 0x20 # I2C device address
LCD_WIDTH = 16   # Maximum characters per line

# Define some device constants
LCD_CHR = 1 # Mode - Sending data
LCD_CMD = 0 # Mode - Sending command

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

LCD_BACKLIGHT  = 0x08  # On
#LCD_BACKLIGHT = 0x00  # Off

ENABLE = 0b00000100 # Enable bit

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

#Open I2C interface
#bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
bus = smbus.SMBus(1) # Rev 2 Pi uses 1

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
  # bits = the data
  # mode = 1 for data
  #        0 for command

  bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
  bits_low = mode | ((bits<<4) & 0xF0) | LCD_BACKLIGHT

  # High bits
  bus.write_byte(I2C_ADDR, bits_high)
  lcd_toggle_enable(bits_high)

  # Low bits
  bus.write_byte(I2C_ADDR, bits_low)
  lcd_toggle_enable(bits_low)

def lcd_toggle_enable(bits):
  # Toggle enable
  time.sleep(E_DELAY)
  bus.write_byte(I2C_ADDR, (bits | ENABLE))
  time.sleep(E_PULSE)
  bus.write_byte(I2C_ADDR,(bits & ~ENABLE))
  time.sleep(E_DELAY)

def lcd_string(message,line):
  # Send string to display

  message = message.ljust(LCD_WIDTH," ")

  lcd_byte(line, LCD_CMD)

  for i in range(LCD_WIDTH):
    lcd_byte(ord(message[i]),LCD_CHR)

# Definizione carattere (0) antenna
  lcd_byte(64,LCD_CMD)
  lcd_byte(0b11111,LCD_CHR)
  lcd_byte(0b01110,LCD_CHR)
  lcd_byte(0b01110,LCD_CHR)
  lcd_byte(0b00100,LCD_CHR)
  lcd_byte(0b00100,LCD_CHR)
  lcd_byte(0b00100,LCD_CHR)
  lcd_byte(0b00100,LCD_CHR)
  lcd_byte(0b00100,LCD_CHR)

# Definizione carattere (1) termometro
  lcd_byte(0b00100,LCD_CHR)
  lcd_byte(0b01010,LCD_CHR)
  lcd_byte(0b01010,LCD_CHR)
  lcd_byte(0b01110,LCD_CHR)
  lcd_byte(0b01110,LCD_CHR)
  lcd_byte(0b11111,LCD_CHR)
  lcd_byte(0b11111,LCD_CHR)
  lcd_byte(0b01110,LCD_CHR)

# Definizione carattere (2) gradi Celsius
  lcd_byte(0b00000,LCD_CHR)
  lcd_byte(0b00000,LCD_CHR)
  lcd_byte(0b01000,LCD_CHR)
  lcd_byte(0b00011,LCD_CHR)
  lcd_byte(0b00100,LCD_CHR)
  lcd_byte(0b00100,LCD_CHR)
  lcd_byte(0b00011,LCD_CHR)
  lcd_byte(0b00000,LCD_CHR)


def main():
 lcd_init()

 while True:
  for counter in range (4):

   cmd1 = "mpc | head -1"        #gets the currently playing song from mpc
   process = subprocess.Popen(cmd1, stdout=subprocess.PIPE , shell=True)
   os.waitpid(process.pid, 0)[1]
   mpc_song = process.stdout.read().strip()

   cmd2 = "mpc | head -2 | tail -1 | awk '{print $1}'" # gets the player state ie paused playing etc
   process = subprocess.Popen(cmd2, stdout=subprocess.PIPE , shell=True)
   os.waitpid(process.pid, 0)[1]
   mpc_state = process.stdout.read().strip()

   cmd3 = "hostname -I"  #gets the current ip of the boombox
   process = subprocess.Popen(cmd3, stdout=subprocess.PIPE , shell=True)
   os.waitpid(process.pid, 0)[1]
   ip_addr = process.stdout.read().strip()

   cmd4 = "iwconfig wlan0 | grep Signal | awk '{print $4}' | cut -d= -f2" #check wifi signal strength
   process = subprocess.Popen(cmd4, stdout=subprocess.PIPE , shell=True)
   os.waitpid(process.pid, 0)[1]
   wifi_strength = process.stdout.read().strip()
 
   cmd5 = "/opt/vc/bin/vcgencmd measure_temp | cut -c6-9"   #Misura la temperatura della CPU
   process = subprocess.Popen(cmd5, stdout=subprocess.PIPE , shell=True)
   os.waitpid(process.pid, 0)[1]
   temp  = process.stdout.read().strip()

   cmd6 = "awk '/^format/{print substr($2,2,2)}' /proc/asound/card0/pcm0p/sub0/hw_params"   #Misura bitrate
   process = subprocess.Popen(cmd6, stdout=subprocess.PIPE , shell=True)
   os.waitpid(process.pid, 0)[1]
   freq1  = process.stdout.read().strip()

   cmd7 = "awk '/^rate/{print $2/1000}' /proc/asound/card0/pcm0p/sub0/hw_params"   #Misura bitrate
   process = subprocess.Popen(cmd7, stdout=subprocess.PIPE , shell=True)
   os.waitpid(process.pid, 0)[1]
   freq2  = process.stdout.read().strip()

   cmd8 = "cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"   #Misura CPU Speed
   process = subprocess.Popen(cmd8, stdout=subprocess.PIPE , shell=True)
   os.waitpid(process.pid, 0)[1]
   cpu  = process.stdout.read().strip()

   cmd9 = "top -b -n1 | grep Cpu | awk '{print $2 + $4}'"   #Misura CPU libera
   process = subprocess.Popen(cmd9, stdout=subprocess.PIPE , shell=True)
   os.waitpid(process.pid, 0)[1]
   cpuload  = process.stdout.read().strip()
   
   
   if counter == 0:  # Scrive riga 2 - Indirizzo IP e potenza WiFi
     lcd_string(ip_addr,LCD_LINE_2)
    
   if counter == 1:   # Scrive riga 2 - Temperatura CPU e Frequenza
     # Frequenza audio
     freq = freq1 + "/" + freq2 + "kHz"
     lcd_string(freq,LCD_LINE_2)
     # Temperatura CPU
     lcd_string(temp,LCD_LINE_2+13)
     # Simbolo termometro
     lcd_byte(LCD_LINE_2+12, LCD_CMD)
     lcd_byte(1,LCD_CHR)
     # Simbolo gradi Celsius
     lcd_byte(LCD_LINE_2+15, LCD_CMD)
     lcd_byte(2,LCD_CHR)

   if counter == 2:   #Scrive riga 2 - potenza wifi - CPU speed
     lcd_byte(LCD_LINE_2, LCD_CMD)
     lcd_byte(0,LCD_CHR) #Simbolo antenna
     lcd_string(wifi_strength,LCD_LINE_2+1)
     cpu = str(int(cpu)/1000) + "MHz"
     lcd_string(cpu, LCD_LINE_2+10)

   if counter == 3:  #Scrive riga 2 - CPU Load
     cpuload = "CPU Load " + cpuload + "%"
     lcd_string(cpuload,LCD_LINE_2)

   # Scrive riga 1
   my_long_string = str_pad + mpc_state + " " + mpc_song
   for i in range (0, len(my_long_string)):  
    lcd_text = my_long_string[i:(i+LCD_WIDTH)]  
    lcd_string(lcd_text,LCD_LINE_1)  
    time.sleep(0.1)  
   lcd_string(str_pad,LCD_LINE_1)  
   

if __name__ == '__main__':

  try:
    main()
  except KeyboardInterrupt:
    pass
  finally:
    lcd_byte(0x01, LCD_CMD)
    lcd_string("Goodbye!",LCD_LINE_1)
