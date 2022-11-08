import pyautogui
import time
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01


def natural_like_type(message, interval, pause_interval=None):
    pause_interval = pause_interval or interval * 6
    for c in message:
        if len(c) > 1:
            c = c.lower()
        pyautogui.press(c, _pause=False)

        if c in ['\n', ' ', '.', '=']:
            t = pause_interval
        else:
            t = interval

        time.sleep(t)
        pyautogui.failSafeCheck()



case = 10
time.sleep(4)

if case == 1:
    natural_like_type(
        "xy = [125, 125]\n"
        "x, y = xy\n"
        "plt.plot(x, y, marker='+')\n"
        "plt.title(xy)\n",
        interval=0.02)

if case == 2:
    natural_like_type(
    "\n"
    "# Plot a circle around the xy-point\n"
    "radius = 50\n"
    "phi = np.linspace(0, 2 * np.pi, 30)\n"
    "x_circle = radius * np.cos(phi)\n"
    "y_circle = radius * np.sin(phi)\n"
    "plt.plot(x_circle + x, y_circle + y, linewidth=3)\n",
    interval = 0.02)

if case == 3:
    natural_like_type(
        "\n"
        "# Create a TextBox for the radius:\n"
        "TextBox(ax=plt.axes([0.65, 0.05, 0.2, 0.05]),\n"
        "label='radius: ', initial=radius)\n",
        interval=0.02)

if case == 4:
    natural_like_type(
        "\n"
        "# Load and plot source image\n"
        "filename = iquib('bacteria_droplets.tif')\n"
        "img = plt.imread(filename)\n"
        "plt.imshow(img)\n",
        interval=0.02)

if case == 5:
    natural_like_type(
        "\n"
        "# Create a new figure\n"
        "plt.figure()\n"
        "ax = plt.subplot(2, 2, 1)\n"
        "ax.set_title('Bacteria in a droplet')\n",
        interval=0.02)

if case == 6:
    natural_like_type(
        "\n"
        "# Slice and plot selected region of image:\n"
        "sub_img = img[y-radius : y+radius+1, x-radius : x+radius+1, :]\n"
        "ax.imshow(sub_img)\n",
        interval=0.02)

if case == 7:
    natural_like_type(
        "\n"
        "# Threshold the sub-image in each color\n"
        "thresholds = [200, 200, 200]\n"
        "sub_img_binary = sub_img > np.expand_dims(thresholds, axis=(0, 1))\n"
        "ax = plt.subplot(2, 2, 3)\n"
        "ax.imshow(sub_img_binary * 1.0)\n",
        interval=0.02)


if case == 8:
    natural_like_type(
        "\n"
        "# Plot RGB intensity histograms\n"
        "rgb = np.eye(3)\n"
        "bins = np.arange(2, 8, 0.25)\n"
        "for i, color in enumerate(rgb):\n"
        "ax = plt.subplot(3, 2, (i + 1) * 2)\n"
        "log_intensity = np.log2(sub_img[:, :, i])\n"
        "log_threshold = np.log2(thresholds[i])\n"
        "ax.hist(np.ravel(log_intensity), bins,\n"
        "color=color*0.5, log=True)\n"
        "ax.hist(log_intensity[log_intensity>log_threshold], bins,\n"
        "color=color)\n"
        "ax.plot(log_threshold + np.array([0, 0]), ax.get_ylim(),\n"
        "'--kd', linewidth=2)\n",
        interval=0.02)

if case == 9:
    natural_like_type(
        " Total area above threshold in each color\n"
        "fraction_above_threshold = np.average(sub_img_binary, (0, 1))\n"
        "plt.figure()\n"
        "plt.bar(['R', 'G', 'B'], fraction_above_threshold*100, color=rgb)\n"
        "plt.ylabel('area above threshold, %')\n",
        interval=0.02)

if case == 10:
    natural_like_type(
        "\n"
        "from pyquibbler.quib_network import dependency_graph\n"
        "dependency_graph(fraction_above_threshold)",
        interval=0.02)
