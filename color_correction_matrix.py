# This script calculates color correction matrix for camera rgb sensor based on:
#  - captured image of 24 field color chart
#  - LAB data of this color chart
# Image of color chart should be 600x400 rgb linear(!) data, 24 bit, see examples
# Copyright Andriy Melnykov 2024


import numpy as np
from colormath.color_objects import LabColor, XYZColor, sRGBColor
from colormath.color_conversions import convert_color
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
from scipy.optimize import minimize


# draw synthetic target based on 24 rgb values
def draw_target(target_array, filename):
    rect_width = 100
    rect_height = 100

    img_width = rect_width * 6
    img_height = rect_height * 4
    image = Image.new('RGB', (img_width, img_height), 'black')
    draw = ImageDraw.Draw(image)    
    
    for i in range(0, 24):
        x = (i % 6) * rect_width
        y = (i // 6) * rect_height
        rectangle = [x+5, y+5, x + rect_width-5, y + rect_height-5]
        draw.rectangle(rectangle, fill=(round(target_array[i,0]*255),
                                        round(target_array[i,1]*255),
                                        round(target_array[i,2]*255), ))
    #image.show()
    image.save(filename)
    

# load target from image, 600x400 pixel, 24 color fields
def load_target(filename):
    image_path = filename
    img = Image.open(image_path)
    #img.show()

    #num_colors = 24  # number of color rectangles
    rect_width = 100  # approximate width of each color rectangle
    rect_height = 100  # approximate height of each color rectangle
    sample_size = 50  # size of the square to sample

    mean_colors = np.ndarray(shape=(24,3))
    
    for i in range(4):  # assuming the rectangles are laid out in 6x4 grid
        for j in range(6):
            # Calculate the center of each rectangle
            center_x = rect_width * (j + 0.5)
            center_y = rect_height * (i + 0.5)

            # Define the bounds of the rectangle to be sampled
            left = int(center_x - sample_size / 2)
            top = int(center_y - sample_size / 2)
            right = int(center_x + sample_size / 2)
            bottom = int(center_y + sample_size / 2)

            # Crop the rectangle
            crop_img = img.crop((left, top, right, bottom))
            #crop_img.show()
            
            # Convert cropped image to an array
            np_image = np.array(crop_img)

            # Calculate the mean color
            mean_color = np_image.mean(axis=(0, 1))
            #print(mean_color)
            mean_colors[i*6+j] = [mean_color[0]/255, mean_color[1]/255, mean_color[2]/255]

    return mean_colors


# calculate error with color matrix, for optimization
def calculate_error(matrix):
    matrix = np.reshape(matrix, (3, 3))
    
    err = 0
    
    for i in range(0, 23):
        C_my = [my_target_srgb_linear[i,0],my_target_srgb_linear[i,1],my_target_srgb_linear[i,2]]
        C_my = matrix@C_my
        
        single_err = (C_my[0]-reference_target_srgb_linear[i,0])**2 + (C_my[1]-reference_target_srgb_linear[i,1])**2 + (C_my[2]-reference_target_srgb_linear[i,2])**2
        single_err = single_err / (C_my[0] + C_my[1] + C_my[2])
        err = err + single_err
    
    return err


# linear regression
def linear_find(xs, ys):    #y=Ax+B
    # Fit the linear model
    A, B = np.polyfit(xs, ys, 1)
    
    return A, B


# calculate display gamma for srgb
def gamma_lin2srgb(p):
    if p<0.0031308:
        return 12.92*p
    else:
        return 1.055*( p**(1/2.4) ) - 0.055




#main function

# captured color target
target_image_file = "color_target_sun.tif"


# matrix for conversion xyz to linear srgb
xyz_to_srgb = np.array([[3.134, -1.617, -0.4906],     #linear!
                        [-0.9788, 1.916,  0.03345],
                        [0.07195,-0.2290, 1.405]])


# reference data of used 24 fields color chart, in LAB
reference_target_lab = np.array([
    [31.90,	18.24,	23.20], 
    [64.23,	19.90,	18.08], 
    [48.29,	-5.09,	-24.19], 
    [38.25,	-17.04,	31.28],   
    [52.40,	9.61,   -28.07], 
    [70.46,	-34.70,	-0.24], 
    
    [61.82,	37.93,	70.41], 
    [35.81,	11.95,	-52.91], 
    [47.82,	52.72,	19.27], 
    [21.28,	31.34,	-30.25], 
    [72.01,	-24.94,	64.71], 
    [71.54,	17.97,	79.11], 
    
    [21.24,	21.93,	-61.57], 
    [52.79,	-46.23,	39.97], 
    [40.69,	62.85,	38.64], 
    [81.02,	1.85,   90.10], 
    [49.27,	54.67,	-17.84], 
    [48.48,	-34.21,	-30.10], 
    
    [94.52,	-0.17,	-0.56], 
    [80.42,	-0.11,	-0.91], 
    [65.31,	0.19,  -0.67], 
    [51.15,	-0.05,	-0.30], 
    [36.21,	0.36,	0.45], 
    [15.39,	-0.23,	1.05]])


# calculate reference target in linear and display-gamma srgb
reference_target_srgb = np.ndarray(shape=(24,3))
reference_target_srgb_linear = np.ndarray(shape=(24,3))

for i in range(0, 24):
    lab = LabColor(reference_target_lab[i,0], reference_target_lab[i,1], reference_target_lab[i,2])
    
    srgb = convert_color(lab, sRGBColor)
    C_srgb = srgb.get_value_tuple()
    C_srgb = [C_srgb[0],C_srgb[1],C_srgb[2]]
    reference_target_srgb[i] = C_srgb
    
    xyz = convert_color(lab, XYZColor)
    C_xyz = xyz.get_value_tuple()
    C_xyz = [C_xyz[0],C_xyz[1],C_xyz[2]]
    C_srgb = xyz_to_srgb@C_xyz    #linear!
    reference_target_srgb_linear[i] = C_srgb

draw_target(reference_target_srgb, "ref_srgb_displaygamma.tiff")


# load captured image of the color chart (must be debayered and linear rgb! 600x400 pixels)
my_target_srgb_linear = load_target(target_image_file)


# find and apply gain and offset based on grey fields
Ar,Br = linear_find(my_target_srgb_linear[range(18,24),0], reference_target_srgb_linear[range(18,24),0])
Ag,Bg = linear_find(my_target_srgb_linear[range(18,24),1], reference_target_srgb_linear[range(18,24),1])
Ab,Bb = linear_find(my_target_srgb_linear[range(18,24),2], reference_target_srgb_linear[range(18,24),2])

my_target_srgb_linear[:,0] = my_target_srgb_linear[:,0] * Ar + Br
my_target_srgb_linear[:,1] = my_target_srgb_linear[:,1] * Ag + Bg
my_target_srgb_linear[:,2] = my_target_srgb_linear[:,2] * Ab + Bb


# find white balance based on gains
wb_r = Ar/Ag
wb_b = Ab/Ag
print ("White balance, rgb: ", wb_r, 1, wb_b)


# calculate captured target with applied white balance for dispaly gamma
my_target_wbonly = np.ndarray(shape=(24,3))
for i in range(0, 24):
    my_target_wbonly[i,0] = gamma_lin2srgb(my_target_srgb_linear[i,0])
    my_target_wbonly[i,1] = gamma_lin2srgb(my_target_srgb_linear[i,1])
    my_target_wbonly[i,2] = gamma_lin2srgb(my_target_srgb_linear[i,2])
draw_target(my_target_wbonly, "my_wbonly_displaygamma.tiff")


# check linearity of captured data, based on grey fields
x = reference_target_srgb_linear[range(18,24),0]
y = my_target_srgb_linear[range(18,24),0]
fig, ax = plt.subplots()
ax.scatter(x, y)
ax.plot([0, 1], [0, 1])
ax.grid()
plt.show()

x = reference_target_srgb_linear[range(18,24),1]
y = my_target_srgb_linear[range(18,24),1]
fig, ax = plt.subplots()
ax.scatter(x, y)
ax.plot([0, 1], [0, 1])
ax.grid()
plt.show()

x = reference_target_srgb_linear[range(18,24),2]
y = my_target_srgb_linear[range(18,24),2]
fig, ax = plt.subplots()
ax.scatter(x, y)
ax.plot([0, 1], [0, 1])
ax.grid()
plt.show()


# find color matrix with optimization algorithm
color_matrix = np.array([1, 0, 0, 0, 1, 0, 0, 0, 1])

print("Sum error before: ", calculate_error(color_matrix))
color_matrix = minimize(calculate_error, color_matrix)
color_matrix = color_matrix.x
matrix = np.reshape(color_matrix, (3, 3))
print("Sum error after: ", calculate_error(color_matrix))
print("Color matrix: ", matrix)


# apply color matrix to captured target
for i in range(0, 24):
    C_my = [my_target_srgb_linear[i,0],my_target_srgb_linear[i,1],my_target_srgb_linear[i,2]]
    C_my = matrix@C_my
    my_target_srgb_linear[i] = C_my


# calculate captured target with applied white balance and color matrix for dispaly gamma
my_target_srgb = np.ndarray(shape=(24,3))

for i in range(0, 24):
    my_target_srgb[i,0] = gamma_lin2srgb(my_target_srgb_linear[i,0])
    my_target_srgb[i,1] = gamma_lin2srgb(my_target_srgb_linear[i,1])
    my_target_srgb[i,2] = gamma_lin2srgb(my_target_srgb_linear[i,2])
 
draw_target(my_target_srgb, "my_corrected_displaygamma.tiff")
    