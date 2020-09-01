# SkyNet

**SkyNet is published as a conference paper at [Conference on Machine Learning and Systems (MLSys)](https://mlsys.org/Conferences/2020/Schedule?type=Oral).**

This is a repository for SkyNet, a new hardware-efficient DNN specialized in object detection and tracking.  
SkyNet is developed based on the SkyNet design methodology to facilitate edge AI solutions,  
and demonstrated in [the 56th IEEE/ACM Design Automation Conference System Design Contest (DAC-SDC)](http://www.cse.cuhk.edu.hk/~byu/2019-DAC-SDC/index.html),  
a low power object detection challenge for real-life unmanned aerial vehicle (UAV) applications.  
SkyNet won the first place award for both GPU and FPGA tracks of the contest:  
we deliver 0.731 Intersection over Union (IoU) and 67.33 frames per second (FPS) on a TX2 GPU,  
and deliver 0.716 IoU and 25.05 FPS on an Ultra96 FPGA.

The GPU team (iSmart3-SkyNet) members are:  
Xiaofan Zhang*, Haoming Lu*, Jiachen Li, Cong Hao, Yuchen Fan, Yuhong
Li, Sitao Huang, Bowen Cheng, Yunchao Wei, Thomas Huang, Jinjun Xiong, Honghui Shi, Wen-mei Hwu, Deming Chen. 

The FPGA team (iSmart3) members are:  
Cong Hao*, Xiaofan Zhang*, Yuhong Li, Yao Chen, Xingheng Liu, Sitao Huang, Kyle Rupnow, Jinjun Xiong, Wen-mei Hwu, Deming Chen. 

(*equal contributors)


---

# FPGA


## Platform

[Xilinx Ultra96](https://www.xilinx.com/products/boards-and-kits/1-vad4rl.html)

## Software prerequisites
[Vivado Design Suite - HLx Editions](https://www.xilinx.com/products/design-tools/vivado.html#overview)



## Build the Bitstream and Weights from scratch

In this work, the SkyNet FPGA implementation is written in C code.  
To deploy the SkyNet on FPGA, we go through three major steps:

1. **Vivado HLS: (HLS)**  
  the C code is synthesized by Vivado High Level Synthesis (HLS) tool to generate RTL (Verilog code) code,  
  and exported as an HLS IP.
2. **Vivado: (RTL)**  
  the exported Verilog code is synthesized by Vivado to generate bitstream for FPGA configuration.
3. **Embedded B/D: (Deploy)**  
  upload the generated bitstream file (.bit), the hardware description file (.hwh), and the weight file (.bin)  
  generated by Vivado HLS to FPGA, and finish the host code running in the embedded ARM core (in Python or C).


### 1. Vivado HLS (HLS)
The C source code of SkyNet can be found in ./FPGA/HLS/ folder.  

There are typically four steps:
  1. C code simulation (takes roughly 20 min.)
  2. C code synthesis (takes roughly 40 min.)
  3. C and Verilog co-simulation (takes roughly hours.)
  4. Export RTL(Verilog/VHDL) (takes roughly 2 min.)

  the C and Verilog co-simulation takes hours so it is commented in this script;
  You may comment/uncomment the corresponding commands in script.tcl based on your necessity.
  The output of this step is an exported HLS IP, written in Verilog.


You may go through the Vivado HLS flow by running:
```
  $ cd ./FPGA/HLS/
  $ vivado_hls -f script.tcl
```



### 2. Vivado (RTL)
  In this step we integrate the generated HLS IP into the whole system,  
  and generate the bitstream (.bit) and the hardware configuration file (.hwh).


You may go through the Vivado flow by running:
```
(edit  /FPGA/RTL/script.tcl)
-> em.avnet.com:ultra96v1:part0:1.2     ( for Ultra96 v1),,  v2:part0:1.0 for ultra96v2
-> xilinx.com:ip:zynq_ultra_ps_e:3.3     (for above vivado 2019.1)

$ cd ./FPGA/RTL/
$ vivado -mode batch -source script.tcl -tclargs skynet ./ ../HLS/model/solution1/impl/ip  
  "skynet"($Your_Project_Name) "./"($Path_To_Your_RTL_Project) "../HLS/model/solution1/impl/ip"($Path_To_Your_HLS_Project)
```

In this configuration, the Zynq processor works under 214MHz.  
Two high performance AXI buses from Zynq are connected to the m_axi ports of HLS IP, INPUT and OUTPUT respectively.  
(After running this script, the generation of bitstream (.bit) is not completed even though the script shows to be terminated.  
 It takes 40 minutes to an hour for bitstream generation, and you may observe the progress in vivado GUI.)


### 3. Embedded B/D - Ultra96 (Deploy)
  After generating the bitstream, the final step is to finish the host code running in the processing system,  
  in this case the embedded ARM core.  
  Usually it is written in C, but in Ultra96 and Pynq Series, it allows us to write in Python.  
  In this example we use Python.


First, find the following three files to upload to the board (default name and path):

1. **design_1_wrapper.bit**  
  ($Path\_To\_Your\_RTL\_Project/$Project\_Name/$Project\_Name.runs/impl\_1)
2. **design_1.hwh**  
  ($Path\_To\_Your\_RTL\_Project/$Project\_Name/$Project\_Name.srcs/sources\_1/bd/design\_1/hw\_handoff)
3. **weights_fixed.bin**, generated by Vivado HLS after reordering and transforming to fixed point  
  ($Path\_to\_your\_HLS\_project/$Project\_name/solution1/csim/build)


Rename the .bit and .hwh file, .bin to **SkyNet.bit** and **SkyNet.hwh**,  **SkyNet.bin**     or anything but need to be the same.


Second, in the Python host file, allocate memory for weights, off-chip buffers, load parameters,  
download the overlay (.bit) to program the FPGA logic and specify the IP addresses.  

You may refer to the SkyNet.py in the ./FPGA/Deploy. 



## Directly run the demo on the FPGA (Ultra96)

This example allows you to directly try our bitstream and weights by running over 16 test images,  
stored in test_images from 0.jpg to 15.jpg.  
The images are processed with a batch size of 4.  
The host code (SkyNet.py) runs on the embedded ARM core.  
It first loads the weight file (SkyNet.bin),  
and then loads the binary file (SkyNet.bit) to configure the FPGA program logic.  
Then it activates the SkyNet IP to execute the inference of input images,  
and outputs the coordinates of detected bounding boxes.  
Finally it shows the total execution time (s) and energy consumption (J).


To run the demo:  

```
(Edit 60 line in SkyNet.py)  
  IMG_DIR = '/home/max/work/SkyNet/FPGA/Deploy/test_images/'

$ cd ./FPGA/Deploy/
$ sudo python3 SkyNet.py
```
The initial password for the board is "xilinx".

You should be able to see outputs like:

```
**** Running SkyNet
Allocating memory done
Parameters loading done
Bitstream loaded

**** Start to detect
['0.jpg', '1.jpg', '2.jpg', '3.jpg']
[307, 377, 135, 238]
[290, 311, 129, 171]
[557, 573, 232, 255]
[240, 261, 159, 215]
['4.jpg', '5.jpg', '6.jpg', '7.jpg']
[300, 317, 167, 201]
...

**** Detection finished

Total time: 0.948... s
Total energy: 6.513... J

```





You are ready to go, good luck!






---

# GPU

## Platform
Jetson Tx2, Jetpack 4.2

## Install
```
$ sudo bash install.sh
```
## Test on given dataset
```
$ python3 run.py
```
The dataset is supposed to be organized as [required](https://d1b10bmlvqabco.cloudfront.net/attach/jrckw1628ejd9/jux80pibriz3qy/jvlmoykue8qf/Submission_requirement.txt).
## Run the demo (webcam)
```
$ python3 demo.py
```
## Run the demo (images)
```
$ python3 demo.py --input=samples/0.jpg
```


---

# References
If you find SkyNet useful, please cite the [SkyNet paper](https://arxiv.org/abs/1909.09709):
```
@inproceedings{zhang2020skynet,
  title={{SkyNet}: a hardware-efficient method for object detection and tracking on embedded systems},
  author={Zhang, Xiaofan and Lu, Haoming and Hao, Cong and Li, Jiachen and Cheng, Bowen and Li, Yuhong and Rupnow, Kyle and Xiong, Jinjun and Huang, Thomas and Shi, Honghui and Hwu, Wen-mei and Chen, Deming},
  booktitle={Conference on Machine Learning and Systems (MLSys)},
  year={2020}
}
```
More details regarding the SkyNet design motivations and SkyNet FPGA accelerator design can be found in our [ICML'19 workshop paper](https://arxiv.org/abs/1905.08369) (which won the **Best Poster Award**) and the [DAC'19 paper](https://arxiv.org/abs/1904.04421), respectively.
```
@article{zhang2019bi,
  title={A Bi-Directional Co-Design Approach to Enable Deep Learning on {IoT} Devices},
  author={Zhang, Xiaofan and Hao, Cong and Li, Yuhong and Chen, Yao and Xiong, Jinjun and Hwu, Wen-mei and Chen, Deming},
  journal={arXiv preprint arXiv:1905.08369},
  year={2019}
}
```
```
@inproceedings{hao2019fpga,
  title={{FPGA/DNN} Co-Design: An Efficient Design Methodology for {IoT} Intelligence on the Edge},
  author={Hao, Cong and Zhang, Xiaofan and Li, Yuhong and Huang, Sitao and Xiong, Jinjun and Rupnow, Kyle and Hwu, Wen-mei and Chen, Deming},
  booktitle={Proceedings of the 56th ACM/IEEE Design Automation Conference (DAC)},
  year={2019}
}
```
