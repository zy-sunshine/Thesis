# -*- coding=utf-8 -*-
import mmseg

mmseg.dict_load_defaults()
subject = "linux兼容硬件列表及笔记本usb摄头配置推荐"
algor = mmseg.Algorithm(subject)
for tk in algor:
    print tk.text
