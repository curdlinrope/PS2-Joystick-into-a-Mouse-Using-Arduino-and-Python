import time
import uinput
from serial.tools import list_ports
import serial

# --- Auto-detect Arduino port ---
def auto_port():
    for p in list_ports.comports():
        if "ttyUSB" in p.device or "ttyACM" in p.device:
            return p.device
    raise RuntimeError("Arduino not found")

SERIAL_PORT = auto_port()
BAUD_RATE    = 9600

# --- Create virtual mouse ---
device = uinput.Device([
    uinput.REL_X, uinput.REL_Y,
    uinput.BTN_LEFT, uinput.BTN_RIGHT,
])

# --- Click helpers ---
def left_click():
    device.emit(uinput.BTN_LEFT, 1)
    device.emit(uinput.BTN_LEFT, 0)

def right_click():
    device.emit(uinput.BTN_RIGHT, 1)
    device.emit(uinput.BTN_RIGHT, 0)

# --- Open serial ---
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)

last_click = 0
DOUBLE_INT = 0.3

# Movement configuration
DEADZONE = 30          # Reduced deadzone for more sensitivity
BASE_SCALE = 15        # Increased base scaling factor
MAX_SCALE = 25         # Maximum scaling for fast movements
ACCELERATION = 1.5     # Acceleration multiplier for sustained movement

# For acceleration tracking
last_movement_time = 0
movement_count = 0

while True:
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if not line:
        continue
    
    # Expecting either "PRESS" on its own, or "x,y" from Arduino
    if "PRESS" in line:
        now = time.time()
        if now - last_click < DOUBLE_INT:
            left_click()
        else:
            right_click()
        last_click = now
        continue
    
    # Handle proportional movement if comma-separated:
    if "," in line:
        try:
            x_raw, y_raw = map(int, line.split(","))
        except ValueError:
            continue
        
        # Apply deadzone
        if abs(x_raw) < DEADZONE: x_raw = 0
        if abs(y_raw) < DEADZONE: y_raw = 0
        
        if x_raw == 0 and y_raw == 0:
            # Reset acceleration when not moving
            movement_count = 0
            continue
        
        # Calculate acceleration based on sustained movement
        current_time = time.time()
        if current_time - last_movement_time < 0.1:  # Within 100ms
            movement_count = min(movement_count + 1, 10)  # Cap at 10
        else:
            movement_count = 0
        last_movement_time = current_time
        
        # Apply acceleration
        accel_factor = 1 + (movement_count * 0.2)  # Up to 3x speed
        
        # Calculate movement with non-linear scaling for better control
        # Use square root of absolute value to get more gradual acceleration
        x_factor = (abs(x_raw) / 512) ** 0.7  # Non-linear scaling
        y_factor = (abs(y_raw) / 512) ** 0.7
        
        # Apply direction
        dx = int(x_factor * BASE_SCALE * accel_factor * (1 if x_raw > 0 else -1))
        dy = int(y_factor * BASE_SCALE * accel_factor * (1 if y_raw > 0 else -1))
        
        # Cap maximum movement per frame
        dx = max(-MAX_SCALE, min(MAX_SCALE, dx))
        dy = max(-MAX_SCALE, min(MAX_SCALE, dy))
        
        if dx or dy:
            device.emit(uinput.REL_X, dx)
            device.emit(uinput.REL_Y, dy)
    
    # Or fallback to simple direction keywords with faster movement:
    else:
        dx = dy = 0
        if "LEFT"  in line: dx = -8   # Increased from -2
        if "RIGHT" in line: dx =  8   # Increased from 2
        if "UP"    in line: dy = -8   # Increased from -2
        if "DOWN"  in line: dy =  8   # Increased from 2
        
        if dx or dy:
            device.emit(uinput.REL_X, dx)
            device.emit(uinput.REL_Y, dy)