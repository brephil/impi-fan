import unittest
from unittest.mock import patch, mock_open, MagicMock
from io import StringIO

# Assuming the script is named ipmi-fan-superserver.py
from ipmi_fan_superserver import (
    get_high_temp,
    check_and_set_duty_cycle,
    set_zone_duty_cycle,
    set_fan_mode,
)

class TestIPMIFanSupervisor(unittest.TestCase):

    def setUp(self):
        # Mock global variables for testing
        self.high_component_temp = 80
        self.med_high_component_temp = 70
        self.med_component_temp = 60
        self.med_low_component_temp = 50
        self.low_component_temp = 40

    def test_get_high_temp(self):
        devices = ["CPU", "GPU"]
        temps = [
            ("CPU Temp", "75"),
            ("GPU Temp", "85"),
            ("Other Device", "90")
        ]
        high_temp = get_high_temp(devices, temps)
        self.assertEqual(high_temp, 85)

    @patch('ipmi_fan_superserver.set_zone_duty_cycle')
    def test_check_and_set_duty_cycle(self, mock_set_zone_duty_cycle):
        zone = 0
        temps = {
            "CPU": 75,
            "GPU": 85
        }
        check_and_set_duty_cycle(zone, temps, self.high_component_temp, self.med_high_component_temp, 
                                self.med_component_temp, self.med_low_component_temp, self.low_component_temp)
        mock_set_zone_duty_cycle.assert_called_with(zone, 100)  # Assuming z0_high is set to 100

    @patch('os.popen')
    def test_set_fan_mode(self, mock_popen):
        mode = "full"
        expected_command = 'ipmitool raw 0x30 0x45 0x01 1'
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        set_fan_mode(mode)
        mock_popen.assert_called_with(expected_command)

if __name__ == '__main__':
    unittest.main()