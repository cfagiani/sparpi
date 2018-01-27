"""
__author__ = 'Christopher Fagiani'
"""

GRAVITY = 9.80665  # m/s^2
SCALE = 0.004

DATA_FORMAT_REG = 0x31
BW_RATE_REG = 0x2C
POWER_CTL_REG = 0x2D
FIRST_DATA_REG = 0x32
NUM_DATA_REG = 6

BW_RATE = 0x0F  # x0B = 100 Hz,  x0C = 200 Hz, x0D = 400 Hz, x0E = 800 Hz, x0F = 1600 Hz

MEASURE_MODE = 0x08
RANGE = 0x03  # 16 g (max)

try:
    import smbus
except ImportError:
    raise ImportError("smbus is not installed. Please install (sudo apt-get install python-smbus i2c-tools)")

bus = smbus.SMBus(1)


class Accelerometer(object):
    """
    This class is for use with an ADXL345 accelerometer (for full set of possible options, see the component data sheet
    at https://www.sparkfun.com/datasheets/Sensors/Accelerometer/ADXL345.pdf). This abstraction assumes that you have
    python-smbus installed and that the Raspberry Pi has been configured to use the i2c bus. After initialization,
    the x,y,z values of the accelerometer can be read via the get_sample() method.
    """

    def __init__(self, address=0x53):
        self.address = address
        self.__write_register(BW_RATE_REG, BW_RATE)
        self.__set_range()
        self.__write_register(POWER_CTL_REG, MEASURE_MODE)

    def __write_register(self, reg, data):
        bus.write_byte_data(self.address, reg, data)

    def __read_register(self, reg):
        return bus.read_byte_data(self.address, reg)

    def __set_range(self, range_val=RANGE):
        # range is specified using the DATA_FORMAT_REG
        # the range is only in the lowest 2 bits.
        # need to preserve other bits
        existing = self.__read_register(DATA_FORMAT_REG)

        # unset the lower nibble
        existing &= ~0x0F
        # apply the desired range
        existing |= range_val
        # set the justify bit
        existing |= 0x08
        self.__write_register(DATA_FORMAT_REG, existing)

    def get_sample(self):
        sensor_data = bus.read_i2c_block_data(self.address, FIRST_DATA_REG, NUM_DATA_REG)

        axes = []
        for i in range(0, len(sensor_data), 2):
            # NOTE: if you want g-force, don't multiply by GRAVITY
            axes.append(
                round(get_value(sensor_data[i], sensor_data[i + 1])
                      * SCALE * GRAVITY, 4))

        return (axes[0], axes[1], axes[2])


def get_value(byte1, byte2):
    val = byte1 | (byte2 << 8)
    if val & (1 << 16 - 1):
        val = val - (1 << 16)
    return val
