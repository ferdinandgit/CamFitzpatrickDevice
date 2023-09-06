import cv2 
import numpy as np
import scipy
from scipy.interpolate import *
import csv
import dill

storecsv=[] # array for csv rows
gammared=[] #store correction factor for red image correction 
gammableu=[] #store correction factor for bleu image correction
gammagreen=[] #store correction factor for green image correction 
mesureredlist=[] #store red measure of each pixel from the camera
mesuregreenlist=[] #store green measure of each pixel from the camera
mesurebleulist=[] #store bleu measure of each pixel from the camera

with open('calibration.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            storecsv.append([row['R_ref'],row['G_ref'],row['B_ref'], row['R'],row['G'],row['B']])

#Remove the column descriptor of the csv file.
storecsv.pop(1)

#Store value for interpolation calculation 
for couple in storecsv:
    gammared.append(float(couple[0])/float(couple[3]))
    gammagreen.append(float(couple[1])/float(couple[4]))
    gammableu.append(float(couple[2])/float(couple[5]))
    mesureredlist.append(float(couple[3]))
    mesuregreenlist.append(float(couple[4]))
    mesurebleulist.append(float(couple[5]))

    
#determine R,G,B correction function
fbleu=scipy.interpolate.interp1d(mesurebleulist,gammableu,bounds_error=False,fill_value="extrapolate")
fgreen=scipy.interpolate.interp1d(mesuregreenlist,gammagreen,bounds_error=False,fill_value="extrapolate")
fred=scipy.interpolate.interp1d(mesureredlist,gammared,bounds_error=False,fill_value="extrapolate")



with open('fbleu.dill','wb') as out:
    dill.dump(fbleu,out)
with open('fred.dill','wb') as out:
    dill.dump(fbleu,out)
with open('fgreen.dill','wb') as out:
    dill.dump(fbleu,out)


