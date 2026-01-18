# Vigil AI
Vigil AI is a real time edge AI crowd safety system that detects stampede precursors using granular based crowd dynamics.
Vigil AI treats the crowd as granular matter and detect a jamming transition by measuring accumulated deformation under continued motion, not speed or density.
## Steps To Run The Code
1. Make connections for raspberry pi with nRF24L01 as given in the table below.

| Component | PIN |
| --------- | --- |
| CE        | 22  |
| CSN       | 24  |
| SCK       | 23  |
| MOSI      | 19  |
| MISO      | 21  |

2. Clone the git repo using 
```sh 
$ git clone https://github.com/Gokul2406/VigilAI.git
```
3. Install the required packages. If you are using pip then use 
```sh
$ pip install -r requirements.txt
```
4. If you want to take the live video feed, change the OUTPUT = "camera" and if you want to use a pre-recorded video then set OUTPUT = "video" as well as the file path and run
```sh
$ python petertingle.py
```

## Scientific insight behind Vigil AI
In physics, a stampede is a jamming transition:
- External driving continues (people pushing)
- Degrees of freedom collapse (because people lose the ability to independently adjust their position due to physical confinement and contact forces).
- Deformation accumulates instead of relaxing

This is identical to:
- Granular flow failure
- Sand pile collapse
- Crowd crush dynamics ([Helbing, Johansson et al.](https://www.researchgate.net/publication/226065087_Pedestrian_Crowd_and_Evacuation_Dynamics))

So we are looking into deformation accumulation rather than velocity of the people.
## What Vigil AI measures
- Optical flow
- Velocity gradients
- Strain accumulation
- Kinetic energy
- Temporal evolution
## How the System Works
- **Capture Video (Live or File)**: Raspberry Pi Camera Module (via picamera2)Or prerecorded CCTV footage.
- **Convert to Grayscale & Enhance Low-Light**: CLAHE improves contrast for night / IR CCTV. Works in low-visibility conditions.
- **Compute Optical Flow**: Each pixel behaves like a “particle”. Produces a velocity field v(x,y,t).
- **Remove Bulk Motion (Co-Moving Frame)**: Global rushing toward an entrance is subtracted. Only internal pushing, compression, shear remain. This will prevent false positive in the case of marathons.
- **Compute Shear Strain**: $\sqrt{(\frac{\partial v_x}{\partial y})^2 + (\frac{\partial v_y}{\partial x})^2}$  
- **Accumulate Strain Over Time**: $\int |\nabla \vec v| dt$     

**Normal motion**: strain releases but in Stampede strain accumulates. This is stored mechanical stress. We track **Energy**. This will tell us if the motion is still being forced? if yes then its a stampede and if no then the situation has been settled. We measure the kinetic energy here which is mean of velocity in x direction and velocity in y direction.
**Temporal Decision**: We detect trends, not values:Is strain increasing compared to the recent past? Is motion still persistent? This makes Vigil AI: Scale Independent, Camera angle independent and Crowd size independent.
## Output States:
1. 0 -> Normal: Motion continues, stress relaxed.
2. 1 -> Pre-Alert: Stress building, early warning.
3. 2 -> Stampede: Stress accumulating under force.

# Tech Stack Used
We've made the model in python using opencv to perform the required analysis. The live feed is taken via the Raspberry Pi Camera Module 3 attached with the Raspberry Pi. 
We also use an Arduino Uno to act as a receiver for the outputs from the raspberry pi and to act as an alert for the local authorities. 
The NRF24L01 was controlled in the Raspberry pi using the pyrf24 module. 
## Acutation:
- Buzzer on Raspberry pi will alert by buzzing.
- Raspberry Pi Camera Module (via picamera2)
- Buzzer (GPIO)
- NRF24L01 (SPI)
# Creators
1. [V S Abhishek](https://www.github.com/abhigator)
2. [Gokul P Bharathan](https://github.com/Gokul2406)
# Contact
For any further information regarding the model and the device kindly contact the creators via email
- [V S Abhishek](mailto:abhishek.mtp@gmail.com)
- [Gokul P Bharathan](gokulpbharathan89@gmail.com)
