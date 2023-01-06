


from collections import defaultdict
s = """0	PA8	RX0	3	6
1	PA9	TX0	15	9
2	PB25	Digital Pin 2	3	6
3	PC28	Digital Pin 3	15	9
4	connected to both PA29 and PC26	Digital Pin 4	15	9
5	PC25	Digital Pin 5	15	9
6	PC24	Digital Pin 6	15	9
7	PC23	Digital Pin 7	15	9
8	PC22	Digital Pin 8	15	9
9	PC21	Digital Pin 9	15	9
10	connected to both PA28 and PC29	Digital Pin 10	15	9
11	PD7	Digital Pin 11	15	9
12	PD8	Digital Pin 12	15	9
13	PB27	Digital Pin 13 / Amber LED "L"	3	6
14	PD4	TX3	15	9
15	PD5	RX3	15	9
16	PA13	TX2	3	6
17	PA12	RX2	3	6
18	PA11	TX1	3	6
19	PA10	RX1	3	6
20	PB12	SDA	3	6
21	PB13	SCL	3	6
22	PB26	Digital Pin 22	3	6
23	PA14	Digital Pin 23	15	9
24	PA15	Digital Pin 24	15	9
25	PD0	Digital Pin 25	15	9
26	PD1	Digital pin 26	15	9
27	PD2	Digital Pin 27	15	9
28	PD3	Digital Pin 28	15	9
29	PD6	Digital Pin 29	15	9
30	PD9	Digital Pin 30	15	9
31	PA7	Digital Pin 31	15	9
32	PD10	Digital Pin 32	15	9
33	PC1	Digital Pin 33	15	9
34	PC2	Digital Pin 34	15	9
35	PC3	Digital Pin 35	15	9
36	PC4	Digital Pin 36	15	9
37	PC5	Digital Pin 37	15	9
38	PC6	Digital Pin 38	15	9
39	PC7	Digital Pin 39	15	9
40	PC8	Digital Pin 40	15	9
41	PC9	Digital Pin 41	15	9
42	PA19	Digital Pin 42	15	9
43	PA20	Digital Pin 43	3	6
44	PC19	Digital Pin 44	15	9
45	PC18	Digital Pin 45	15	9
46	PC17	Digital Pin 46	15	9
47	PC16	Digital Pin 47	15	9
48	PC15	Digital Pin 48	15	9
49	PC14	Digital Pin 49	15	9
50	PC13	Digital Pin 50	15	9
51	PC12	Digital Pin 51	15	9
52	PB21	Digital Pin 52	3	6
53	PB14	Digital Pin 53	15	9
54	PA16	Analog In 0	3	6
55	PA24	Analog In 1	3	6
56	PA23	Analog In 2	3	6
57	PA22	Analog In 3	3	6
58	PA6	Analog In 4	3	6
59	PA4	Analog In 5	3	6
60	PA3	Analog In 6	3	6
61	PA2	Analog In 7	3	6
62	PB17	Analog In 8	3	6
63	PB18	Analog In 9	3	6
64	PB19	Analog In 10	3	6
65	PB20	Analog In 11	3	6
66	PB15	DAC0	3	6
67	PB16	DAC1	3	6
68	PA1	CANRX	3	6
69	PA0	CANTX	15	9
70	PA17	SDA1	3	6
71	PA18	SCL2	15	9
72	PC30	LED "RX"	15	9
73	PA21	LED "TX"	3	6
74	PA25	(MISO)	15	9
75	PA26	(MOSI)	15	9
76	PA27	(SCLK)	15	9
77	PA28	(NPCS0)	15	9
78	PB23	(unconnected)	15	9
USB	PB11	ID	15	9
USB	PB10	VBOF	15	9"""

n = s.splitlines()
n = [l.split() for l in n]
d = {v[0]:v[1] for v in n}
d = defaultdict(lambda :"-1",d)
# print(d)

pins="""#define UI_DISPLAY_RS_PIN 8
#define ORIG_X_MIN_PIN 11
#define ORIG_Y_DIR_PIN 12
#define TEMP_0_PIN 13
#define TEMP_1_PIN 14
#define ORIG_X_DIR_PIN 14
#define ORIG_X_STEP_PIN 15
#define HEATER_0_PIN 16
#define LIGHT_PIN 17
#define FIL_SENSOR1_PIN 24
#define ORIG_FAN_PIN 25
#define ORIG_X_ENABLE_PIN 29
#define ORIG_Y_STEP_PIN 30
#define UI_DISPLAY_D0_PIN 34
#define UI_DISPLAY_D1_PIN 35
#define UI_DISPLAY_D2_PIN 36
#define UI_DISPLAY_D3_PIN 37
#define UI_DISPLAY_D4_PIN 38
#define UI_DISPLAY_D5_PIN 39
#define UI_DISPLAY_D6_PIN 40
#define UI_DISPLAY_D7_PIN 41
#define SCK_PIN 42
#define MOSI_PIN 43
#define UI_DISPLAY_RW_PIN_NOT_USED 45
#define TOP_SENSOR_PIN 64
#define BEEPER_PIN 66
#define HEATER_1_PIN 67
#define ORIG_Y_MIN_PIN 68
#define ORIG_Y_ENABLE_PIN 69
#define MISO_PIN 73
#define UI_BACKLIGHT_PIN 78
#define ORIG_FAN2_PIN 85
#define ORIG_Z_MIN_PIN 92
#define Z_PROBE_PIN 117
#define ORIG_Z_DIR_PIN 118
#define ORIG_Z_STEP_PIN 119
#define ORIG_Z_ENABLE_PIN 120
#define ORIG_E0_DIR_PIN 121
#define ORIG_E0_STEP_PIN 122
#define ORIG_E0_ENABLE_PIN 123
#define UI_DISPLAY_ENABLE_PIN 125"""

n = pins.splitlines()
n = [l.split() for l in n]
n = map(lambda (x,y,z):[x,y,z,"//",d[z]],n)

n = [" ".join(i)  for i in n]

print("\n".join(n))

print(d)
