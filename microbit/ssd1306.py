# MicroPython SSD1306 OLED driver, I2C and SPI interfaces

from micropython import const
import framebuf

# register definitions
SET_CONTRAST        = const(0x81)
SET_ENTIRE_ON       = const(0xa4)
SET_NORM_INV        = const(0xa6)
SET_DISP            = const(0xae)
SET_MEM_ADDR        = const(0x20)
SET_COL_ADDR        = const(0x21)
SET_PAGE_ADDR       = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP       = const(0xa0)
SET_MUX_RATIO       = const(0xa8)
SET_COM_OUT_DIR     = const(0xc0)
SET_DISP_OFFSET     = const(0xd3)
SET_COM_PIN_CFG     = const(0xda)
SET_DISP_CLK_DIV    = const(0xd5)
SET_PRECHARGE       = const(0xd9)
SET_VCOM_DESEL      = const(0xdb)
SET_CHARGE_PUMP     = const(0x8d)

# Subclassing FrameBuffer provides support for graphics primitives
# http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
class SSD1306:
    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        self.framebuffer = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00, # off
            # address setting
            SET_MEM_ADDR, 0x00, # horizontal
            # resolution and layout
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01, # column addr 127 mapped to SEG0
            SET_MUX_RATIO, self.height - 1,
            SET_COM_OUT_DIR | 0x08, # scan from COM[N] to COM0
            SET_DISP_OFFSET, 0x00,
            SET_COM_PIN_CFG, 0x02 if self.height == 32 else 0x12,
            # timing and driving scheme
            SET_DISP_CLK_DIV, 0x80,
            SET_PRECHARGE, 0x22 if self.external_vcc else 0xf1,
            SET_VCOM_DESEL, 0x30, # 0.83*Vcc
            # display
            SET_CONTRAST, 0xff, # maximum
            SET_ENTIRE_ON, # output follows RAM contents
            SET_NORM_INV, # not inverted
            # charge pump
            SET_CHARGE_PUMP, 0x10 if self.external_vcc else 0x14,
            SET_DISP | 0x01): # on
            self.write_cmd(cmd)
        self.framebuffer.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)

    def poweron(self):
        self.write_cmd(SET_DISP | 0x01)

    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            # displays with width of 64 pixels are shifted by 32
            x0 += 32
            x1 += 32
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)

class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3c, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.temp[0] = 0x80 # Co=1, D/C#=0
        self.temp[1] = cmd
        self.i2c.write(self.addr, self.temp)

    def write_data(self, buf):
        # This will create a temporary copy of the buffer, but without memoryview or a direct write with i2c
        #  I don't see how it can be avoided
        self.i2c.write(self.addr, b'\x40' + buf)

import microbit

oled = SSD1306_I2C(
    128, 
    64, 
    microbit.i2c
)

ncss = framebuf.FrameBuffer(bytearray(b'\xff\xff\xff\xff\xff\xff\xff\xff\xf0\xfc\x00\x00\x00\x00\xff\xff\xff\xf0\xf0\x00\x00\x00\x00\x7f\xff\xff\xf0\xe0\x00\x00\x00\x00\x1f\xff\xff\xf0\xc0\x00\x00\x00\x00\x1f\xff\xff\xf0\x80\x00\x00\x00\x00\x0f\xff\xff\xf0\x80\x00\x00\x00\x00\x07\xff\xff\xf0\x80@\x00\x00\x00\x07\xff\xff\xf0\x01\xff\xff\xff\xfe\x07\xff\xff\xf0\x01\xff\xff\xff\xfe\x07\xff\xff\xf0\x01\xff\xff\xff\xfe\x07\xff\xfd\xf0\x01\xff\x80\x01\xfe\x07\xe3\xf8p\x01\xff\x00\x00\xfe\x07\xc1\xf00\x01\xfc\x00\x00~\x07\xc1\xf00\x01\xf8\x00\x00>\x07\xc1\xf00\x01\xf8\x00\x00\x1e\x07\xc1\xf00\x01\xf0\x1f\xf8\x1e\x07\xc1\xf00\x01\xf0?\xfc\x0e\x07\xc1\xf00\x01\xf0\x7f\xfe\x0e\x07\xc1\xf00\x01\xf0\x7f\xfe\x0e\x07\xc1\xf00\x01\xf0\x7f\xfe\x0e\x07\xc1\xf00\x01\xf0\x7f\xfe\x0e\x07\xc1\xf00\x01\xf0\x7f\xfe\x0e\x07\xc1\xf00\x01\xf0|>\x0e\x07\xc1\xf00\x01\xf0x\x1e\x0e\x07\xc1\xf00\x01\xf0x\x1e\x0e\x07\xc1\xf00\x01\xf0x\x1e\x0f\x0f\xc1\xf00\x01\xf0x\x1e\x0f\xff\xc1\xf00\x01\xf0x\x1e\x0f\xff\xc1\xf00\x01\xf0x\x1e\x0f\xff\xc1\xf00\x01\xf0x\x1e\x0f\xff\xc1\xf00\x01\xf0x\x1e\x0f\xff\xc1\xf00\x01\xf0x\x1e\x07\xff\x81\xf00\x01\xf0x\x1e\x03\xff\x81\xf00\x01\xf0x\x1f\x00\x00\x03\xf00\x01\xf0x\x1f\x00\x00\x07\xf00\x03\xf0x\x1f\x80\x00\x07\xf00\x03\xf0x\x1f\xc0\x00\x1f\xf00\x87\xf8\xf8\x1f\xf0\x00?\xf00\xff\xff\xf8\x1f\xff\xff\xff\xf00\xff\xff\xf8\x0f\xff\xff\xff\xe00\xff\xff\xf8\x0f\xff\xff\xff\xe00\xff\xff\xf8\x00\x00\x00\x00\x000\xff\xff\xfc\x00\x00\x00\x00\x00p\xff\xff\xfc\x00\x00\x00\x00\x00p\xff\xff\xfe\x00\x00\x00\x00\x00\xf0\xff\xff\xff\x00\x00\x00\x00\x01\xf0\xff\xff\xff\x80\x00\x00\x00\x03\xf0\xff\xff\xff\xe0\x00\x00\x00\x0f\xf0\xff\xff\xff\xff\xff\xff\xff\xff\xf0'), 68, 50, framebuf.MONO_HLSB)

oled.framebuffer.fill_rect(0, 0, 128, 64, 1)
oled.framebuffer.blit(ncss, 30, 8)
oled.show()

from microbit import sleep

c = False

while True:
    sleep(500)
    oled.invert(c)
    c = not c
