# color_correction_matrix
This python script calculates color correction matrix for camera rgb sensor based on:
 - captured image of 24 field color chart
 - LAB data of this color chart

Image of color chart should be 600x400 pixels debayered rgb linear(!) data, 3x8 bit, see example: color_target_sun.tif, captured without saturation.
Illumination must be as uniform as possible: no correction for this in the script.
Median filter applied to the image helps achieving better results.

Here is an example of captured image (linear data without gamma correction is displayed too dark):

<p align="center">
<img src="https://github.com/andriymelnykov/color_correction_matrix/blob/main/images/color_target_sun.png" width="400"/>
</p>

Results are 3 gains for white balance and 9 elements of color correction matrix.
Applying this white balance and color correction matrix to camera rgb data one gets sRGB linear data.

Example results with ZWO ASI533MC camera and Optolong UV/IR filter, with WB_R=50 and WB_B=50 camera settings, sunlight illumination:

White balance:

```
1.43	1.0	1.77
```

Color correction matrix:

```
1.387698	-0.37278958	-0.07946052

-0.40483978	1.69918117	-0.27936073

0.05144559	-0.74390103	1.66072276
``` 

Here are the colors of captured target with **white balance only** (display gamma):

<p align="center">
<img src="https://github.com/andriymelnykov/color_correction_matrix/blob/main/images/my_wbonly_displaygamma.png" width="400"/>
</p>

Andriy Melnykov 2024
