<a id="top"></a>

<div align="center">

<h1 align="center">Smart Waste Sorter</h1>

<p align="center">
<strong>A computer vision-powered IoT system that automatically classifies and sorts waste using AI and robotics.</strong>
<br /><br />
<a href="#installation">Installation Guide</a> ·
<a href="#contact">Contact</a>
</p>

</div>

---

## Table of Contents

1. [About The Project](#about-the-project)
2. [Built With](#built-with)
3. [Getting Started](#getting-started)
   - [Prerequisites](#prerequisites)
   - [Installation](#installation)
4. [Usage](#usage)
5. [Hardware Setup](#hardware-setup)
6. [Roadmap](#roadmap)
7. [License](#license)
8. [Contact](#contact)

---

## About The Project

The Smart Waste Sorter is a full-stack IoT solution designed to automate waste management. By bridging high-level Artificial Intelligence with low-level hardware control, this project eliminates human error in waste segregation.

### Key Capabilities

**Real-Time AI Classification**  
Uses YOLOv8 to distinguish between 'Wet' (organic) and 'Dry' (recyclable) waste instantly.

**Robotic Sorting**  
Controls dual servo motors to physically route waste into the correct bin based on the AI's decision.

**Overflow Protection**  
An integrated ultrasonic sensor monitors bin levels and automatically halts the system if the bin is full to prevent overflow.

**Web-Based Dashboard**  
Replaces clunky terminal windows with a modern, responsive Web GUI for real-time monitoring and manual control.

<p align="right">(<a href="#top">back to top</a>)</p>

---

## Built With

- Python 3.8+: The core logic and server.
- Flask: Web server framework for the GUI.
- OpenCV: Image processing and video stream handling.
- YOLOv8: Advanced object detection model.
- Arduino (C++): Firmware for hardware control.
- Tailwind CSS: Styling for the frontend dashboard.

<p align="right">(<a href="#top">back to top</a>)</p>

---

## Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.8+** — Required to run the computer vision server.
2. **Arduino IDE** — Required to upload the firmware to your Arduino board.

### Installation

1. **Clone the Repository**

```bash
git clone https://github.com/shlokbshetty/classificationwaste.git
```

2. **Install Python Packages**

```bash
pip install -r requirements.txt
```

3. **Download the Model**  
Ensure the `yolov8m-cls.pt` model file is placed in the root directory of the project.

4. **Setup Hardware**  
"Make sure you have the right hardware components for the project (Hardware components will be specified soon)
Connect your Arduino via USB. Identify its COM port (e.g., `COM3` or `/dev/ttyUSB0`).

5. **Configure Port**  
Update `server.py`:

```python
ARDUINO_PORT = 'COM7'  # Change 'COM7' to your actual port
```

<p align="right">(<a href="#top">back to top</a>)</p>

---

## Usage

1. **Upload Firmware**  
Upload `dustbin_controller.ino` using the Arduino IDE.

2. **Start the Server**

```bash
python server.py
```

3. **Access the Dashboard**

```
http://127.0.0.1:5000
```

4. **System Operation**

- **Auto Mode:** Continuous scanning and sorting.
- **Manual Mode:** Place an item and click **Scan Once**.

<p align="right">(<a href="#top">back to top</a>)</p>

---

## Hardware Setup

| Component          | Arduino Pin | Function                                      |
|-------------------|-------------|-----------------------------------------------|
| Wet Bin Servo     | Pin 8       | Opens the wet waste compartment.              |
| Dry Bin Servo     | Pin 9       | Opens the dry waste compartment.              |
| Ultrasonic Trig   | Pin 11      | Sends sound pulse for distance measurement.   |
| Ultrasonic Echo   | Pin 12      | Receives sound pulse echo.                    |

**Note:** Mount the ultrasonic sensor on the underside of the lid, facing downward.

<p align="right">(<a href="#top">back to top</a>)</p>

---

## Roadmap

- [x] Integrate YOLOv8 Classification  
- [x] Develop Web GUI with Flask  
- [x] Add Ultrasonic Bin Level Detection  
- [ ] Add Database for waste statistics tracking  
- [ ] Mobile App integration  
- [ ] Support for 'Hazardous' waste category  

<p align="right">(<a href="#top">back to top</a>)</p>

---

## Architecture Diagram

<img width="1600" height="1283" alt="arch diagram" src="https://github.com/user-attachments/assets/b92fa957-87fb-4e06-8aba-8084669dce6c" />

---

## FlowChart 

<img width="754" height="1600" alt="flow chart" src="https://github.com/user-attachments/assets/42fce35e-8c1d-4620-b3a6-ac422ee698ef" />

---

## Circuit Diagram

<img width="1600" height="753" alt="circuit diagram" src="https://github.com/user-attachments/assets/a0659c91-30a5-485f-b4ee-7cc69fb2d1ed" />

---

## Working Project's Images

<img width="1280" height="960" alt="1" src="https://github.com/user-attachments/assets/be53ceaa-42f7-4e20-9d11-262a4f23a2be" />
<img width="720" height="1280" alt="2" src="https://github.com/user-attachments/assets/76ee9424-5cd5-4aac-bd97-b81f9a303517" />
<img width="1280" height="720" alt="3" src="https://github.com/user-attachments/assets/38c01880-f836-4966-94e7-2549c4ddb016" />

---

## License

Distributed under the **MIT License**. See `LICENSE.txt` for more information.

<p align="right">(<a href="#top">back to top</a>)</p>

---

## Contact

**Shlok Shetty**  
GitHub: `@shlokbshetty`  
Email: `shettyshlok87@gmail.com`  

**Shree Yadav**
GitHub: `@shreeyadav06`  
Email: `shreeyadav0123456789@gmail.com`  
Project Link: https://github.com/shlokbshetty/classificationwaste

<p align="right">(<a href="#top">back to top</a>)</p>
