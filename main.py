
#import main modules 

import signal
import sys
import RPi.GPIO as GPIO
from time import sleep
import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306


#setup screen 

RST = 24

# Note the following are only used with SPI:
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0

# 128x32 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

# Initialize library.
disp.begin()

# Clear display.
disp.clear()
disp.display()



#import computer vision module 
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import subprocess
from picamera import PiCamera
from time import sleep

#GPIO déclaration
GPIO.setmode(GPIO.BCM)
duty=100
ita_value=0
phototype='-'
light_button = 24
phototype_button = 23
ledpin = 13				# PWM pin connected to LED
GPIO.setwarnings(False)			#disable warnings
GPIO.setup(ledpin,GPIO.OUT)
pi_pwm = GPIO.PWM(ledpin,1000)		#create PWM instance with frequency
pi_pwm.start(100)				#start PWM of required Duty Cycle 

#Open camera stream
camera = PiCamera()
camera.start_preview()
sleep(5)
g=camera.awb_gains
print(g)
sleep(2)
camera.awb_mode='off'
camera.exposure_mode = 'off'
camera.awb_gains=(501/256,189/128)

#import serialisation and cv2 module
import cv2   
import numpy as np
import dill 

#declare efb background 
background = Image.open('test1.ppm').convert('1')

#open file from serialisation
with open('fred.dill','rb') as f:
        fred=dill.load(f)
with open('fgreen.dill','rb') as f:
        fgreen=dill.load(f)
with open('fbleu.dill','rb') as f:
        fbleu=dill.load(f)   

def signal_handler(sig, frame):
    GPIO.cleanup()
    sys.exit(0)

def light_button_pressed_callback(channel):
    global duty 
    duty+=10
    if(duty>100):
        duty=0
    print(duty)
    pi_pwm.ChangeDutyCycle(duty)
    screen_write(background,phototype,duty)

def increase_brightness(img, value):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    lim = 255 - value
    v[v > lim] = 255
    v[v <= lim] += value

    final_hsv = cv2.merge((h, s, v))
    img = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
    return img

def phototype_button_pressed_callback(channel):
    print('hello')
    global phototype
    global ita_value
    screen_write(background,'-',duty,0)
    if(isinstance(phototype, str)):
        phototype=0
    camera.capture('./picture.jpg')
    picture=cv2.imread('./picture.jpg')
    a,b,c=np.shape(picture)
    cropped_picture=picture[(int(a/2)-90):(int(a/2)+90),(int(b/2)-90):(int(b/2)+90)]
    cropped_picture=bgrCorrection(fbleu,fred,fgreen,cropped_picture)
    cropped_picture=increase_brightness(cropped_picture,70)
    bleu=np.average(cropped_picture[:,:,:1])
    green=np.average(cropped_picture[:,:,1:2])
    red=np.average(cropped_picture[:,:,2:3])
    rgb=[red,green,bleu]
    print(rgb)
    lab=rgbToLab(rgb)
    if lab[2]<0:
        lab[2]=0.2
    print(lab)
    ita_value=ita(lab)
    print(ita_value)
    phototype=fitzPatrickClassification(ita_value)
    cv2.imwrite('picture.jpg',cropped_picture)
    screen_write(background,phototype,duty,round(ita_value))

def fitzPatrickClassification(ita):
    
    """classifier used to match ita with Fitzpatrick Scale.
    Args:
        ita: double where -90<=ita<=90
    Return:
        Fitzpatrick indice in range [|0;6|]"""

    if 37<ita:
         return 1
    elif -20<ita<=37:
         return 2
    elif -50<ita<=-20:
         return 3
    elif -60<ita<=-50:
        return 4
    elif -85<ita<=-60:
        return 5
    elif ita<=-85:
        return 6

def ita(lab):
    
    """ Ita calulation from Lab color space.
    Args: 
        lab:A array that contains [L,a,B] value.
    Return: 
        Ita Value."""

    return np.arctan((lab[0]-50)/lab[2])*180/np.pi

def bgrCorrection(fb,fg,fr,img):
    print("debug") 
    """Apply correction to each pixel image where Pixel_correct=f(Pixel_raw)*Prixel_raw.
    Args:
        fb: function that returns the correction factor for bleu pixel.
        fg: function that returns the correction factor for green pixel.
        fr: function that returns the correction factor for red pixel.
        img: numpy.array with the following shape (x,y,3) where x,y are int.
    Returns:
        Image with correction."""
    img[:,:,:1]=np.multiply(fbleu(img[:,:,:1]),img[:,:,:1])
    img[:,:,1:2]=np.multiply(fgreen(img[:,:,1:2]),img[:,:,1:2])
    img[:,:,2:3]=np.multiply(fred(img[:,:,2:3]),img[:,:,2:3])
    print("debug1")
    """wid,lgt,size=np.shape(img)
    for i in range(wid):
        for k in range(lgt):
            img[i,k,0]*=fb(img[i,k,0])
            img[i,k,1]*=fg(img[i,k,1])
            img[i,k,2]*=fr(img[i,k,2])"""
    return img




def rgbToLab(inputColor):
    
    """Convert color from RGB colorspace to Lab colorsacpe
    Args:
        inputColor: A array that contains [R,G,B] int values (0<R,G,B<255).
    Returns:
        A array that contains [L,a,b] value."""

    num=0
    RGB=[0, 0, 0]
    for value in inputColor :
        value=float(value)/255
        if value>0.04045 :
           value=((value + 0.055)/1.055 )**2.4
        else :
           value=value/12.92
        RGB[num]=value * 100
        num=num + 1
    XYZ=[0, 0, 0,]

    X=RGB[0]*0.4124+RGB[1]*0.3576+RGB[2]*0.1805
    Y=RGB[0]*0.2126+RGB[1]*0.7152+RGB[2]*0.0722
    Z=RGB[0]*0.0193+RGB[1]*0.1192+RGB[2]*0.9505
   
    XYZ[0]=round(X,4)
    XYZ[1]=round(Y,4)
    XYZ[2]=round(Z,4)

    XYZ[0]=float(XYZ[0])/95.047    
    XYZ[1]=float(XYZ[1])/100.0          
    XYZ[2]=float(XYZ[2])/108.883       

    num=0
    for value in XYZ :
        if value>0.008856 :
            value=value**(0.3333333333333333)
        else:
            value=(7.787*value)+(16/116)

        XYZ[num]=value
        num=num+1

    Lab=[0,0,0]

    L=(116*XYZ[1])-16
    a=500*(XYZ[0]-XYZ[1])
    b=200*(XYZ[1]-XYZ[2])

    Lab[0]=round(L,4)
    Lab[1]=round(a,4)
    Lab[2]=round(b,4)

    return Lab

   
def screen_write(background,phototype,light,ita_value):
    image = background.copy()
    font = ImageFont.load_default()
    draw = ImageDraw.Draw(image)
    draw.text((83,0),"Light",font=font,fill=255)
    if(light==100):
        draw.text((86,15),"100%",font=font,fill=255)
    elif(light==0):
        draw.text((93,15),"0%",font=font,fill=255)
    else:
        draw.text((89,15),str(light)+'%',font=font,fill=255)
    draw.text((47,0),"Skin",font=font,fill=255)
    draw.text((45,15),str(phototype),font=font,fill=255)
    draw.text((50,15),'|',font=font,fill=255)
    draw.text((55,15),str(ita_value),font=font,fill=255)
    disp.image(image)
    disp.display()




if __name__ == '__main__':
    screen_write(background,phototype,duty,ita_value)
    GPIO.setup(light_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(light_button, GPIO.FALLING,callback=light_button_pressed_callback, bouncetime=300)
    GPIO.setup(phototype_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(phototype_button, GPIO.FALLING,callback=phototype_button_pressed_callback, bouncetime=1000)
    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()
    camera.stop_preview()
    







"""image = Image.open('test1.ppm').convert('1')
font = ImageFont.load_default()
draw = ImageDraw.Draw(image)
draw.text((83,0),"Ligth",font=font,fill=255)
#draw.text((89,15),"10%",font=font,fill=255)
draw.text((86,15),"100%",font=font,fill=255)
draw.text((47,0),"Skin",font=font,fill=255)
draw.text((55,15),"1",font=font,fill=255)
disp.image(image)
disp.display()"""




