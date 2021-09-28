import yaml

# Polaris driver
from polaris_vega_api import PolarisDriver

##############################################################################
#              NODE MAIN ROUTINE
##############################################################################

def main():
    # Initialize EMGSensor object
    polaris_driver = PolarisDriverMine()

    # Loop
    polaris_driver.loop()


class PolarisDriverMine:

    #################################
    #  CONSTRUCTORS AND DESTRUCTORS
    #################################

    def __init__(self):

        # Get package configuration file
        yaml_file = open("config.yml")
        parsed_yaml_file = yaml.load(yaml_file, Loader=yaml.FullLoader)

        # Initialize polaris driver
        self.polaris_driver = PolarisDriver()
        self.polaris_driver.debug = parsed_yaml_file['polaris_vega']['debug']
        self.polaris_driver.initialize_ip_communication(parsed_yaml_file['polaris_vega']['ip'],
                                                        parsed_yaml_file['polaris_vega']['port'], )
        self.polaris_driver.open()
        self.polaris_driver.init()

        passive_file_list = []
        if 'passive_tools' in parsed_yaml_file and len(parsed_yaml_file['passive_tools']) > 0:
            for tool in parsed_yaml_file['passive_tools']:
                passive_file_list.append(tool['path'])
        else:
            raise Exception('Fatal error: Configuration file has no passive tool definitions.')

        self.polaris_driver.init_passive_marker_tracker(passive_file_list)

        # self.polaris_driver.set_fps(parsed_yaml_file['polaris_vega']['fps'])

        self.polaris_driver.start_tracking()


    def close(self):
        self.polaris_driver.stop_tracking()
        self.polaris_driver.close()

    #################################
    # CLASS MAIN LOOP
    #################################

    def loop(self):
        while True:
            try:
                self.polaris_driver.update_tool_transformations()
                # self.polaris_driver.set_fps()
                print(self.polaris_driver._get("Param.Tracking.Frame Frequency"))
                for tool in self.polaris_driver.get_tools():
                    print(tool.rot.q1, tool.rot.q2, tool.rot.q3, tool.rot.q0, tool.trans.x, tool.trans.y, tool.trans.z, int(tool.get_frame_number()), int(tool.get_parent_port_handle_id()), int(tool.get_status()))
            except KeyboardInterrupt:
                print('Keyboard interrupt detected, shutting down node...')

                # Send stop tracking signal to Polaris and close serial port
                self.close()

    def update_data(self):
        self.polaris_driver.update_tool_transformations()


##############################################################################
#              RUNNING THE MAIN ROUTINE
##############################################################################

if __name__ == '__main__':
    try:
        main()
    except:
        pass