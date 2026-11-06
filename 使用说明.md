# 桌面宠物猫 🐱

参考你附图的那只嫌弃脸虎斑猫做的桌面宠物。

## 效果

- 无边框透明窗口，一直置顶浮在桌面
- 半眯眼的嫌弃表情 + M 字额纹 + 白胸毛
- 尾巴左右摇摆，会随机眨眼、偶尔说话
- **左键拖动** 换位置，**双击** 撸一下，**右键** 出菜单
- **右键 → 跟着鼠标走**：猫会慢慢跟在光标旁边（再点一次关闭）
- **闲置 60 秒自动睡觉**（闭眼 + Zzz），点它一下或（跟随模式下）动鼠标就会醒
- **整点报时**：每到整点冒泡"X点整啦~"
- **右键 → 开始番茄钟**：25 分钟倒计时显示在猫脚下，结束时提醒休息

## 一、直接跑（推荐先试）

需要 Windows + Python 3.8+：

```bat
pip install PyQt5
python desktop_cat.py
```

跑起来没问题再打包。

## 二、打包成 .exe

**在 Windows 上**执行（Mac/Linux 打不出 Windows 的 exe）：

```bat
pip install pyinstaller PyQt5
pyinstaller --onefile --windowed --name 桌面猫 desktop_cat.py
```

打包完成后，`.exe` 在 `dist\桌面猫.exe`，双击就能跑，可以拷到任何 Windows 电脑上。

参数解释：
- `--onefile`：打成单个 exe（体积大约 40-60 MB，PyQt 自带）
- `--windowed`：不弹黑色命令行窗口
- `--name 桌面猫`：exe 文件名

想加图标：先准备一个 `cat.ico`，然后加参数 `--icon=cat.ico`。

## 三、常见问题

**跑起来窗口是白色方块？**
显卡驱动老可能不支持窗口透明。更新驱动，或把开头的 `Qt.WA_TranslucentBackground` 那行注释掉（会有个白色背景但功能正常）。

**打包后 exe 打不开？**
先在命令行里 `python desktop_cat.py` 能跑，再去掉 `--windowed` 重新打包看报错。

**想改猫的外观？**
所有绘制在 `paintEvent` 里，颜色变量在开头（`tabby_dark`、`white_fur` 之类），改 RGB 值就能换配色。

## 四、想加更多功能？

代码里预留的位置：
- `idle_action` 里加更多台词
- `show_menu` 里加菜单项
- 想让它跟着鼠标走、掉到桌面底部之类的，`animate` 里加逻辑就行

有需要我可以继续加，比如让它跟着鼠标跑、每小时报时、连接 API 说天气之类的。
