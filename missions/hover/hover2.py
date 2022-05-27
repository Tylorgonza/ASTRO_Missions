import argparse
import time

from skyengine.drone import DroneController
from skyengine.exceptions import FlightAbortedException
from skylog.logger import DirectLogger
from skylog.message import BaseMessage
from skymission.concurrency import tick
from skymission.mission import Mission
from skymission.mission import callback
from skymission.mission import panic


class LocationMessage(BaseMessage):
    """
    Message for the drone's current location.
    """

    def __init__(self, timestamp, lat, lon, alt):
        self.timestamp = timestamp
        self.lat = lat
        self.lon = lon
        self.alt = alt

    def serialize(self):
        return {
            'timestamp': self.timestamp,
            'lat': self.lat,
            'lon': self.lon,
            'alt': self.alt,
        }

    @staticmethod
    def deserialize(json):
        return LocationMessage(
            timestamp=json['timestamp'],
            lat=json['lat'],
            lon=json['lon'],
            alt=json['alt'],
        )


class HoverMission(Mission):
    """
    A mission to take off, hover, and land.
    """

    port = 4000
    mission_id = 'hover'

    """
	CREATING INSTANCE OF TXT SHEET TO WRITE TO WHILE GRABBING DATA DURING THIS MISSION
    """
    f = open("log_"+today(),'w')
    def __init__(self, fc_addr, log_file):
        """
        Create a HoverMission, which is started as soon as the class is instantiated.

        :param fc_addr: MAVProxy address of the flight controller.
        :param log_file: Name of log file for location data.
        """
        self.enable_disk_event_logging()

        self.dc = DroneController(fc_addr)
        self.location_logger = DirectLogger(path=log_file)
        self.log.debug('Drone controller and logger initialized successfully')

        self.cancel_tick = self.start_location_log()
        self.log.info('Hover mission initialization complete')

        self.start_server()

    @tick(interval=0.5)
    def start_location_log(self):
        """
        Start periodically logging the drone GPS location to disk.
        """
        location = self.dc.vehicle.location.global_frame
        message = LocationMessage(
            timestamp=time.time(),
            lat=location.lat,
            lon=location.lon,
            alt=location.alt,
        )

        # self.log.debug('Recording current location: ({lat}, {lon})'.format(
        #     lat=location.lat,
        #     lon=location.lon,
        # ))

        self.location_logger.log(message)

    @callback(
        endpoint='/start-mission',
        description='Gives the drone an altitude and hover time.',
        required_params=('alt', 'hover_time'),
        public=True,
    )
    def start_mission(self, data, *args, **kwargs):
        """
        Client-invoked endpoint to begin the hover mission.

        :param data: Required to be of the form:
                     {
                         'alt': ...,  # Target altitude (m)
                         'hover_time': ..., # Hover time (s)
                     }
        """
        alt = data['alt']
        hover_time = data['hover_time']

        try:
            self.log.debug('Taking off to altitude: {alt}'.format(alt=alt))
            self.dc.take_off(alt)
            self.log.debug('Take off complete')

            time.sleep(3)

            location = self.dc.read_gps()
            self.log.debug('Current location: ({lat}, {lon})'.format(lat=location.lat,lon=location.lon,))

	    # Moving to location 1: center of the field
	    """
	    logging first location
	    """
            nextlat, nextlon = 29.71758978560598, -95.4055873521442

            self.log.debug('Navigating to waypoint: ({lat}, {lon})'.format(lat=nextlat,lon=nextlon,))
            self.dc.goto(coords=(nextlat, nextlon), altitude=alt, airspeed=2)
            self.log.debug('Navigation to waypoint complete')

            location = self.dc.read_gps()
            self.log.debug('Arrived! Current location: ({lat}, {lon})'.format(lat=location.lat,lon=location.lon,))

            time.sleep(3)
	    	f.write("first location (lat,lon): {lat},{lon} Alt: {alt}  \t")
	    	f.write()

            # Moving to location 2
            """
            logging second location
            """


            nextlat, nextlon = 29.717660833596735, -95.40562356196683

            self.log.debug('Navigating to waypoint: ({lat}, {lon})'.format(lat=nextlat,lon=nextlon,))
            self.dc.goto(coords=(nextlat, nextlon), altitude=alt, airspeed=2)
            self.log.debug('Navigation to waypoint complete')

            location = self.dc.read_gps()
            self.log.debug('Arrived! Current location: ({lat}, {lon})'.format(lat=location.lat,lon=location.lon,))

            time.sleep(3)
            f.write("second location (lat,lon): {lat},{lon} Alt: {alt} \t")



            # Moving to location 3

            nextlat, nextlon = 29.71772838737737, -95.40566513620766

            self.log.debug('Navigating to waypoint: ({lat}, {lon})'.format(lat=nextlat,lon=nextlon,))
            self.dc.goto(coords=(nextlat, nextlon), altitude=alt, airspeed=2)
            self.log.debug('Navigation to waypoint complete')

            location = self.dc.read_gps()
            self.log.debug('Arrived! Current location: ({lat}, {lon})'.format(lat=location.lat,lon=location.lon,))

            time.sleep(3)

            self.log.debug('Hovering for: {hover_time} seconds'.format(hover_time=hover_time))
            time.sleep(hover_time)
            #third location being logged
            f.write("third location (lat,lon): {lat},{lon} Alt: {alt} Hovertime: {hover_time} \t")


            self.log.info('Hovering complete; begin landing')
            self.dc.land()
            self.log.info('Landed!')
            f.close()
        except FlightAbortedException:
            self.log.warn('Flight aborted due to emergency panic!')

    @panic
    def panic(self, *args, **kwargs):
        self.log.warn('Panic request received')
        self.dc.panic()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--fc-addr',
        dest='fc_addr',
        help='Address of the flight controller mavproxy messages',
        default=None,
    )
    parser.add_argument(
        '--log-file',
        dest='log_file',
        help='Path to the log file to create',
        default='travel-path',
    )
    args = parser.parse_args()

    HoverMission(
        fc_addr=args.fc_addr,
        log_file=args.log_file,
    )
