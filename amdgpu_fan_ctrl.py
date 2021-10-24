#! /usr/bin/env python3
""" Control fan speed of AMD GPU

This tool manipulates the ROCK (Radeon Open Compute Kernel)
via sysfs files.
"""

__version__ = "0.0.1"
__author__ = "Luís Gomes <luismsgomes@gmail.com>"


import datetime
import itertools
import logging
import os.path
import re
import time


UPDATE_INTERVAL = 2.0  # seconds
MIN_FAN_SPEED = 18.0  # percent

# don't start the fan until temperature is greater than COLD_TEMP
COLD = 50.0

# as soon as temperature reaches HOT_TEMP, fan will run at 100%
HOT = 75.0

# how much percent of fan speed do we change at a time
FAN_DELTA = 1.0

DRMPREFIX = "/sys/class/drm"
HWMONPREFIX = "/sys/class/hwmon"
DEBUGPREFIX = "/sys/kernel/debug/dri"
MODULEPREFIX = "/sys/module"

VALUEPATHS = {
    "id": {"prefix": DRMPREFIX, "filepath": "device", "needsparse": True},
    "sub_id": {
        "prefix": DRMPREFIX,
        "filepath": "subsystem_device",
        "needsparse": False,
    },
    "vbios": {"prefix": DRMPREFIX, "filepath": "vbios_version", "needsparse": False},
    "perf": {
        "prefix": DRMPREFIX,
        "filepath": "power_dpm_force_performance_level",
        "needsparse": False,
    },
    "sclk_od": {"prefix": DRMPREFIX, "filepath": "pp_sclk_od", "needsparse": False},
    "mclk_od": {"prefix": DRMPREFIX, "filepath": "pp_mclk_od", "needsparse": False},
    "dcefclk": {"prefix": DRMPREFIX, "filepath": "pp_dpm_dcefclk", "needsparse": False},
    "fclk": {"prefix": DRMPREFIX, "filepath": "pp_dpm_fclk", "needsparse": False},
    "mclk": {"prefix": DRMPREFIX, "filepath": "pp_dpm_mclk", "needsparse": False},
    "pcie": {"prefix": DRMPREFIX, "filepath": "pp_dpm_pcie", "needsparse": False},
    "sclk": {"prefix": DRMPREFIX, "filepath": "pp_dpm_sclk", "needsparse": False},
    "socclk": {"prefix": DRMPREFIX, "filepath": "pp_dpm_socclk", "needsparse": False},
    "clk_voltage": {
        "prefix": DRMPREFIX,
        "filepath": "pp_od_clk_voltage",
        "needsparse": False,
    },
    "voltage": {"prefix": HWMONPREFIX, "filepath": "in0_input", "needsparse": False},
    "profile": {
        "prefix": DRMPREFIX,
        "filepath": "pp_power_profile_mode",
        "needsparse": False,
    },
    "use": {"prefix": DRMPREFIX, "filepath": "gpu_busy_percent", "needsparse": False},
    "use_mem": {
        "prefix": DRMPREFIX,
        "filepath": "mem_busy_percent",
        "needsparse": False,
    },
    "pcie_bw": {"prefix": DRMPREFIX, "filepath": "pcie_bw", "needsparse": False},
    "replay_count": {
        "prefix": DRMPREFIX,
        "filepath": "pcie_replay_count",
        "needsparse": False,
    },
    "unique_id": {"prefix": DRMPREFIX, "filepath": "unique_id", "needsparse": False},
    "serial": {"prefix": DRMPREFIX, "filepath": "serial_number", "needsparse": False},
    "vendor": {"prefix": DRMPREFIX, "filepath": "vendor", "needsparse": False},
    "sub_vendor": {
        "prefix": DRMPREFIX,
        "filepath": "subsystem_vendor",
        "needsparse": False,
    },
    "fan": {"prefix": HWMONPREFIX, "filepath": "pwm1", "needsparse": False},
    "fanmax": {"prefix": HWMONPREFIX, "filepath": "pwm1_max", "needsparse": False},
    "fanmode": {"prefix": HWMONPREFIX, "filepath": "pwm1_enable", "needsparse": False},
    "temp1": {"prefix": HWMONPREFIX, "filepath": "temp1_input", "needsparse": True},
    "temp1_label": {
        "prefix": HWMONPREFIX,
        "filepath": "temp1_label",
        "needsparse": False,
    },
    "temp2": {"prefix": HWMONPREFIX, "filepath": "temp2_input", "needsparse": True},
    "temp2_label": {
        "prefix": HWMONPREFIX,
        "filepath": "temp2_label",
        "needsparse": False,
    },
    "temp3": {"prefix": HWMONPREFIX, "filepath": "temp3_input", "needsparse": True},
    "temp3_label": {
        "prefix": HWMONPREFIX,
        "filepath": "temp3_label",
        "needsparse": False,
    },
    "power": {"prefix": HWMONPREFIX, "filepath": "power1_average", "needsparse": True},
    "power_cap": {"prefix": HWMONPREFIX, "filepath": "power1_cap", "needsparse": False},
    "power_cap_max": {
        "prefix": HWMONPREFIX,
        "filepath": "power1_cap_max",
        "needsparse": False,
    },
    "power_cap_min": {
        "prefix": HWMONPREFIX,
        "filepath": "power1_cap_min",
        "needsparse": False,
    },
    "dpm_state": {
        "prefix": DRMPREFIX,
        "filepath": "power_dpm_state",
        "needsparse": False,
    },
    "vram_used": {
        "prefix": DRMPREFIX,
        "filepath": "mem_info_vram_used",
        "needsparse": False,
    },
    "vram_total": {
        "prefix": DRMPREFIX,
        "filepath": "mem_info_vram_total",
        "needsparse": False,
    },
    "vis_vram_used": {
        "prefix": DRMPREFIX,
        "filepath": "mem_info_vis_vram_used",
        "needsparse": False,
    },
    "vis_vram_total": {
        "prefix": DRMPREFIX,
        "filepath": "mem_info_vis_vram_total",
        "needsparse": False,
    },
    "vram_vendor": {
        "prefix": DRMPREFIX,
        "filepath": "mem_info_vram_vendor",
        "needsparse": False,
    },
    "gtt_used": {
        "prefix": DRMPREFIX,
        "filepath": "mem_info_gtt_used",
        "needsparse": False,
    },
    "gtt_total": {
        "prefix": DRMPREFIX,
        "filepath": "mem_info_gtt_total",
        "needsparse": False,
    },
    "ras_gfx": {
        "prefix": DRMPREFIX,
        "filepath": "ras/gfx_err_count",
        "needsparse": False,
    },
    "ras_sdma": {
        "prefix": DRMPREFIX,
        "filepath": "ras/sdma_err_count",
        "needsparse": False,
    },
    "ras_umc": {
        "prefix": DRMPREFIX,
        "filepath": "ras/umc_err_count",
        "needsparse": False,
    },
    "ras_mmhub": {
        "prefix": DRMPREFIX,
        "filepath": "ras/mmhub_err_count",
        "needsparse": False,
    },
    "ras_athub": {
        "prefix": DRMPREFIX,
        "filepath": "ras/athub_err_count",
        "needsparse": False,
    },
    "ras_sdma": {
        "prefix": DRMPREFIX,
        "filepath": "ras/sdma_err_count",
        "needsparse": False,
    },
    "ras_pcie_bif": {
        "prefix": DRMPREFIX,
        "filepath": "ras/pcie_bif_err_count",
        "needsparse": False,
    },
    "ras_hdp": {
        "prefix": DRMPREFIX,
        "filepath": "ras/hdp_err_count",
        "needsparse": False,
    },
    "ras_xgmi_wafl": {
        "prefix": DRMPREFIX,
        "filepath": "ras/xgmi_wafl_err_count",
        "needsparse": False,
    },
    "ras_df": {
        "prefix": DRMPREFIX,
        "filepath": "ras/df_err_count",
        "needsparse": False,
    },
    "ras_smn": {
        "prefix": DRMPREFIX,
        "filepath": "ras/smn_err_count",
        "needsparse": False,
    },
    "ras_sem": {
        "prefix": DRMPREFIX,
        "filepath": "ras/sem_err_count",
        "needsparse": False,
    },
    "ras_mp0": {
        "prefix": DRMPREFIX,
        "filepath": "ras/mp0_err_count",
        "needsparse": False,
    },
    "ras_mp1": {
        "prefix": DRMPREFIX,
        "filepath": "ras/mp1_err_count",
        "needsparse": False,
    },
    "ras_fuse": {
        "prefix": DRMPREFIX,
        "filepath": "ras/fuse_err_count",
        "needsparse": False,
    },
    "xgmi_err": {"prefix": DRMPREFIX, "filepath": "xgmi_error", "needsparse": False},
    "ras_features": {
        "prefix": DRMPREFIX,
        "filepath": "ras/features",
        "needsparse": True,
    },
    "bad_pages": {
        "prefix": DRMPREFIX,
        "filepath": "ras/gpu_vram_bad_pages",
        "needsparse": False,
    },
    "ras_ctrl": {
        "prefix": DEBUGPREFIX,
        "filepath": "ras/ras_ctrl",
        "needsparse": False,
    },
    "gpu_reset": {
        "prefix": DEBUGPREFIX,
        "filepath": "amdgpu_gpu_recover",
        "needsparse": False,
    },
    "driver": {
        "prefix": MODULEPREFIX,
        "filepath": "amdgpu/version",
        "needsparse": False,
    },
}

# Supported firmware blocks
VALIDFWBLOCKS = {
    "vce",
    "uvd",
    "mc",
    "me",
    "pfp",
    "ce",
    "rlc",
    "rlc_srlc",
    "rlc_srlg",
    "rlc_srls",
    "mec",
    "mec2",
    "sos",
    "asd",
    "ta_ras",
    "ta_xgmi",
    "smc",
    "sdma",
    "sdma2",
    "vcn",
    "dmcu",
}

for block in VALIDFWBLOCKS:
    VALUEPATHS["%s_fw_version" % block] = {
        "prefix": DRMPREFIX,
        "filepath": "fw_version/%s_fw_version" % block,
        "needsparse": False,
    }
# SMC has different formatting for its version
VALUEPATHS["smc_fw_version"]["needsparse"] = True
VALUEPATHS["ta_ras_fw_version"]["needsparse"] = True
VALUEPATHS["ta_xgmi_fw_version"]["needsparse"] = True


def parse_device_name(device_name):
    """Parse the device name, which is of the format card#.

    Parameters:
    device_name -- DRM device name to parse
    """
    return device_name[4:]


def parse_sysfs_value(key: str, value: str):
    """Parse the sysfs value string

    Parameters:
    key -- [$VALUEPATHS.keys()] Key referencing desired SysFS file
    value -- SysFS value to parse

    Some SysFS files aren't a single line/string, so we need to parse it
    to get the desired value
    """
    if key == "id":
        # Strip the 0x prefix
        return value[2:]
    if re.match(r"temp[0-9]+", key):
        # Convert from millidegrees
        return int(value) / 1000
    if key == "power":
        # power1_average returns the value in microwatts. However, if power is not
        # available, it will return "Invalid Argument"
        if value.isdigit():
            return float(value) / 1000 / 1000
    # ras_reatures has "feature mask: 0x%x" as the first line, so get the bitfield out
    if key == "ras_features":
        return int((value.split("\n")[0]).split(" ")[-1], 16)
    # The smc_fw_version sysfs file stores the version as a hex value like 0x12345678
    # but is parsed as int(0x12).int(0x34).int(0x56).int(0x78)
    if (
        key == "smc_fw_version"
        or key == "ta_xgmi_fw_version"
        or key == "ta_ras_fw_version"
    ):
        return (
            str("%02d" % int((value[2:4]), 16))
            + "."
            + str("%02d" % int((value[4:6]), 16))
            + "."
            + str("%02d" % int((value[6:8]), 16))
            + "."
            + str("%02d" % int((value[8:10]), 16))
        )

    return ""


def get_sysfs_value(device: str, key: str):
    """Return the desired SysFS value for a specified device

    Parameters:
    device -- DRM device identifier
    key -- [$VALUEPATHS.keys()] Key referencing desired SysFS file
    """
    file_path = get_key_file_path(device, key)
    path_dict = VALUEPATHS[key]

    if not file_path:
        return None
    # Use try since some sysfs files like power1_average will throw -EINVAL
    # instead of giving something useful.
    try:
        with open(file_path, "r") as f:
            value = f.read().rstrip("\n")
    except:
        logging.warning(
            "GPU[%s]\t: Unable to read %s", parse_device_name(device), file_path
        )
        return None

    # Some sysfs files aren't a single line of text
    if path_dict["needsparse"]:
        value = parse_sysfs_value(key, value)

    if value == "":
        logging.debug(
            "GPU[%s]\t: Empty SysFS value: %s", parse_device_name(device), key
        )

    return value


class FailedToSetSysfsValue(Exception):
    def __init__(self, device, key, value, file_path, message):
        super().__init__()
        self.device = device
        self.key = key
        self.value = value
        self.file_path = file_path
        self.message = message

    def __str__(self):
        return (
            f"{self.__class__.__name__}("
            f"device={self.device!r}, "
            f"key={self.key!r}, "
            f"value={self.value!r}, "
            f"file_path={self.file_path!r}, "
            f"message={self.message!r})"
        )


def set_sysfs_value(device: str, key: str, value: str):
    """ Write to a sysfs file."""
    file_path = get_key_file_path(device, key)

    if not os.path.isfile(file_path):
        raise FailedToSetSysfsValue(
            device, key, value, file_path, "File does not exist"
        )
    try:
        logging.debug(f"Writing value {value!r} to file {file_path!r}")
        with open(file_path, "w") as f:
            f.write(value + "\n")  # Certain sysfs files require \n at the end
    except (IOError, OSError):
        raise FailedToSetSysfsValue(device, key, value, file_path, "IO Error")


def is_amd_device(device: str):
    """Return whether the specified device is an AMD device or not

    Parameters:
    device -- DRM device identifier
    """
    vid = get_sysfs_value(device, "vendor")
    if vid == "0x1002":
        return True
    return False


def get_all_devices():
    """ Return a list of GPU devices."""

    if not os.path.isdir(DRMPREFIX) or not os.listdir(DRMPREFIX):
        logging.error("Unable to get devices, /sys/class/drm is empty or missing")
        return None

    devices = [
        device
        for device in os.listdir(DRMPREFIX)
        if re.match(r"^card\d+$", device) and is_amd_device(device)
    ]
    return sorted(devices, key=lambda x: int(x.partition("card")[2]))


def list_amd_hw_monitors():
    """Return a list of AMD HW Monitors."""
    hwmons = []

    for mon in os.listdir(HWMONPREFIX):
        tempname = os.path.join(HWMONPREFIX, mon, "name")
        if os.path.isfile(tempname):
            with open(tempname, "r") as tempmon:
                drivername = tempmon.read().rstrip("\n")
                if drivername in ["radeon", "amdgpu"]:
                    hwmons.append(os.path.join(HWMONPREFIX, mon))
    return hwmons


def get_hw_monitor_from_device(device: str):
    """Return the corresponding HW Monitor for a specified GPU device.

    Parameters:
    device -- DRM device identifier
    """
    drmdev = os.path.realpath(os.path.join(DRMPREFIX, device, "device"))
    for hwmon in list_amd_hw_monitors():
        if os.path.realpath(os.path.join(hwmon, "device")) == drmdev:
            return hwmon
    return None


def get_key_file_path(device: str, key: str):
    """Return the filepath for a specific device and key

    Parameters:
    device -- Device whose filepath will be returned
    key -- [$VALUEPATHS.keys()] The sysfs path to return
    """
    if key not in VALUEPATHS.keys():
        logging.warning("Key %s not present in VALUEPATHS map" % key)
        return None
    path_dict = VALUEPATHS[key]

    if path_dict["prefix"] == HWMONPREFIX:
        # HW Monitor values have a different path structure
        if not get_hw_monitor_from_device(device):
            logging.warning(
                "GPU[%s]\t: No corresponding HW Monitor found",
                parse_device_name(device),
            )
            return None
        file_path = os.path.join(
            get_hw_monitor_from_device(device), path_dict["filepath"]
        )
    elif path_dict["prefix"] == DEBUGPREFIX:
        # Kernel DebugFS values have a different path structure
        file_path = os.path.join(
            path_dict["prefix"], parse_device_name(device), path_dict["filepath"]
        )
    elif path_dict["prefix"] == DRMPREFIX:
        file_path = os.path.join(
            path_dict["prefix"], device, "device", path_dict["filepath"]
        )
    else:
        # Otherwise, just join the 2 fields without any parsing
        file_path = os.path.join(path_dict["prefix"], path_dict["filepath"])

    if not os.path.isfile(file_path):
        return None
    return file_path


def device_exists(device):
    """Check whether the specified device exists in sysfs.

    Parameters:
    device -- DRM device identifier
    """
    if os.path.exists(os.path.join(DRMPREFIX, device)) == 0:
        return False
    return True


def is_dpm_available(device):
    """Check if DPM is available for a specified device.

    Parameters:
    device -- DRM device identifier
    """
    if not device_exists(device) or not os.path.isfile(
        get_key_file_path(device, "dpm_state")
    ):
        logging.warning("GPU[%s]\t: DPM is not available", parse_device_name(device))
        return False
    return True


def get_temps(device: str):
    """Return the current temperatures for a given device.

    Parameters:
    device -- DRM device
    """
    temps = dict()
    # We currently have temp1/2/3, so use range(1,4)
    for i in range(1, 4):
        temp = get_sysfs_value(device, f"temp{i}")
        if temp:
            label = get_sysfs_value(device, f"temp{i}_label") or i
            temps[label] = temp
    return temps


def get_temp(device: str):
    return max(0.0, *get_temps(device).values())


def get_fan_speed(device: str):
    """Return the fan speed % for a specified device or None if either current
       fan speed or max fan speed cannot be obtained.

    Parameters:
    device -- DRM device identifier
    """

    fan_level = get_sysfs_value(device, "fan")
    fan_max = get_sysfs_value(device, "fanmax")
    if not fan_level or not fan_max:
        return None
    fan_speed_percent = 100 * float(fan_level) / float(fan_max)
    logging.debug(f"device {device} fan speed: {fan_speed_percent}%")
    return fan_speed_percent


class UnableToSetFanSpeedException(Exception):
    pass


def set_fan_speed(device: str, fan_speed: float):
    """Set fan speed for a device."""
    if not is_dpm_available(device):
        logging.warning(f"GPU[{device}]: DPM is not available for this device")
        raise UnableToSetFanSpeedException

    logging.debug(f"setting device {device} fan speed: {fan_speed}%")

    fanpath = get_key_file_path(device, "fan")
    maxfan = get_sysfs_value(device, "fanmax")
    fanmode = get_sysfs_value(device, "fanmode")

    if maxfan is None:
        logging.warning(
            f"GPU[{device}]: Unable to get maxfan value (file {fanpath!r} is empty)"
        )
        raise UnableToSetFanSpeedException

    if fanmode != "1":
        set_sysfs_value(device, "fanmode", "1")
        logging.debug(f"GPU[{device}]: Successfully set fan control to 'manual'")

    maxfan = int(maxfan)
    fan_speed_abs = int((fan_speed * maxfan) / 100.0)
    if fan_speed_abs > maxfan:
        fan_speed_abs = maxfan
    set_sysfs_value(device, "fan", str(fan_speed_abs))


def get_decrease_fan_speed_delta(fan_speed: float, delta: float, turn_off: bool):
    # if the fan is already running slower than minimum speed
    if fan_speed < MIN_FAN_SPEED:
        # we ignore the turn_off argument and always set the fan off
        return -fan_speed
    # if fan would be running slower than minimum speed after decreasing it by delta:
    if (fan_speed - delta) < MIN_FAN_SPEED:
        if turn_off:
            return -fan_speed  # turn the fan off
        else:
            return -fan_speed + MIN_FAN_SPEED  # make it run at minimum speed
    return -delta


def get_increase_fan_speed_delta(fan_speed, delta):
    new_fan_speed = fan_speed + delta
    # if fan would be running faster than maximum speed
    if new_fan_speed > 100:
        return 100 - fan_speed  # cap it at 100%
    elif new_fan_speed < MIN_FAN_SPEED:
        return MIN_FAN_SPEED - fan_speed  # jump to minimum fan speed
    return delta


def compute_fan_speed_delta(temp: float, temp_delta: float, fan_speed: float):
    if temp >= HOT:
        return get_increase_fan_speed_delta(fan_speed, 100.0)

    if temp <= COLD:
        # if temperature is decreasing, we slowly decrease the fan speed
        if temp_delta < 0.0:
            return get_decrease_fan_speed_delta(fan_speed, FAN_DELTA, turn_off=True)
        # if temperature is constant or increasing we don't change fan speed
        # until it rises above COLD
        return 0.0

    # if temperature is decreasing we decrease fan speed slowly
    if temp_delta < 0.0:
        return get_decrease_fan_speed_delta(fan_speed, FAN_DELTA, turn_off=False)

    # if temperature is increasing we increase fan speed slowly
    if temp_delta > 0.0:
        return get_increase_fan_speed_delta(fan_speed, FAN_DELTA)

    # if temperature is not changing, don't change the fan speed
    return 0.0


def sign(value):
    return "+" if value >= 0 else "-"


def monitor_and_control():
    devices = get_all_devices()
    device_temp = dict()
    for device in devices:
        device_temp[device] = get_temp(device)

    for i in itertools.count():
        time.sleep(UPDATE_INTERVAL)
        for device in devices:
            old_temp, device_temp[device] = device_temp[device], get_temp(device)
            temp_delta = (device_temp[device] - old_temp) / UPDATE_INTERVAL
            fan_speed = get_fan_speed(device)
            fan_speed_delta = compute_fan_speed_delta(
                device_temp[device], temp_delta, fan_speed
            )
            logging.debug(
                f"device={device}, temp={device_temp[device]}, temp_delta={temp_delta}, "
                f"fan_speed={fan_speed}%, delta={fan_speed_delta}"
            )

            if i % 5 == 0:
                now = datetime.datetime.now()
                print(
                    f"{now} || device {device} || "
                    f"temperature: {device_temp[device]}°C || "
                    f"fan speed: {fan_speed:.1f}%  "
                )
            if fan_speed_delta:
                set_fan_speed(device, fan_speed + fan_speed_delta)


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.DEBUG
        if "-vv" in sys.argv[1:]
        else logging.INFO
        if "-v" in sys.argv[1:]
        else logging.WARNING
    )
    monitor_and_control()
