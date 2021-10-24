# AMD GPU fan control for Linux

This software has been developed and tested on Debian 10 Buster with the 4.19.0-6-amd64 Linux kernel and a Radeon™ RX 590 GPU.
It requires the `amdgpu` kernel module to be loaded.


## Why this package?

1. automatic fan control provided by the GPU hardware keeps the fans of my RX 590 running all the time (albeit at a very low speed)
1. after some years of continued use, even at low speeds, fans develop irritanting noises
1. most of the time I use my computer in a way that requires minimal GPU usage (writing code, browsing the web, etc)
1. without fans, the temperature of my RX 590 rarely raises above 50°C when doing non-GPU intensive activities, even during the hottest summer days

# Disclaimer

USE OF THIS SOFTWARE IS ENTIRELY OF YOUR RESPONSABILITY.  HARDWARE DAMAGE MAY RESULT FROM HIGH TEMPERATURES AS A RESULT OF USING THIS SOFTWARE.


# Warning

This software puts your GPU into manual fan control (manual means not controlled directly by hardware).
**If you stop this software you should reboot your computer or manually reset your GPU fan control to automatic mode.**

# Installing this software

If you want to run the software manually or develop your own software making use of functions from the `amdgpu_fan_ctrl` Python module, you may install it with pip3 or simply copy the file into some directory of your choice.

The most common use case will be to run this software as a `systemd` service, started at boot.  To install this service, run the script `./install-systemd-service.sh` as root.

# License

This software is licensed under the MIT license.


