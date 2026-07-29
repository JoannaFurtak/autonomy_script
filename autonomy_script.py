#github repo
# add
# commit -m
# push

#encoders

import curses
import subprocess
import rospy
from sensor_msgs.msg import NavSatFix

actual_covariance = [999.0]
actual_position = [0.0, 0.0, 0.0]

def create_window(stdscr):
    stdscr.clear()
    stdscr.box()

def gps_callback(msg):
    if len(msg.position_covariance) > 0:
        actual_covariance[0] = msg.position_covariance[0]

        actual_position[0] = msg.latitude
        actual_position[1] = msg.longitude
        actual_position[2] = msg.altitude

def gps(stdscr):
    create_window(stdscr)
    stdscr.addstr(2, 2, "Krok 1 - uruchamianie gps, q to quit")
    subprocess.Popen(["roslaunch", "sirius_navigation", "gnss.launch"],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL
    )
                                #topic,   typ danych,  funkcja do zrobienia po odczytaniu wiadomosci
    gps_sub = rospy.Subscriber('gps/fix', NavSatFix, gps_callback)

    stdscr.timeout(100) 
    ready = False

    while True:

        if actual_covariance[0] <= 0.002 and not ready:
            ready = True
            gps_sub.unregister()

        if ready:
            stdscr.addstr(6, 2, 'covariance is ok. press -s- to proceed to slam')
            return False
        else:
            stdscr.addstr(6, 2, f'acctual covariance: {actual_covariance[0]}')

        try:
            key = stdscr.getkey().lower()
            if ready and key == 's':
                return "slam"
            elif key == 'q':
                return
        except curses.error:
            pass


#tutaj musze:
#miec nowy slam, zeby pkt referencyjny byl parametrem
#odsluchy z odometry aby wiedziec jak daleko jest lazik
# warunek ze dopoki nie przejedzie sie 40m to 
# nie moge kliknac l
def slam(stdscr):
    stdscr.timeout(100)
    create_window(stdscr)
    stdscr.addstr(2, 2, "Krok 2 - uruchamianie slama, q to quit")
    slam_launched = False

    while True:
        create_window(stdscr)

        if not slam_launched:
            stdscr.addstr(4, 2, "Wybierz punkt referencyjny:")
            stdscr.addstr(5, 4, "[1] Uzyj aktualnej pozycji GPS")
            stdscr.addstr(6, 4, "[2] Uzyj domyslnej pozycji")
            stdscr.addstr(8, 2, "[q] Wyjscie")

        try:
            key = stdscr.getkey().lower()

            if key == 'q':
                return #wyjscie
            
            if not slam_launched:
                # pkt referencyjny == gps
                if key == '1':
                    rospy.set_param('NAZWA_PARAMETRU_PKT', actual_position)
                    stdscr.addstr(10, 2, "idz bujaj lazikiem, nastepnie przejedz nim 40m ")
                    stdscr.addstr(12, 2, "a potem wcisnij l -> localization")
                    subprocess.Popen(["roslaunch", "sirius_spectacularai", "slam.launch"],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL
                        )
                    slam_launched = True

                # pkt referencyjny == wybierasz
                elif key == '2':
                    stdscr.timeout(-1)
                    curses.echo()
                    default = stdscr.addstr(10, 2, "wpisz nazwe pkt referencyjnego: ")
                    rospy.set_param('NAZWA_PARAMETRU_PKT', default)
                    curses.noecho()
                    stdscr.timeout(100)
                    stdscr.addstr(12, 2, "idz bujaj lazikiem, nastepnie przejedz nim 40m")
                    stdscr.addstr(14, 2, "a potem wcisnij l -> localization")
                    subprocess.Popen(["roslaunch", "sirius_spectacularai", "slam.launch"],
                                                            stdout=subprocess.DEVNULL,
                                                            stderr=subprocess.DEVNULL
                                    )
                    slam_launched = True

            else:
                if key == 'l': #and 40m przejechane
                    localization(stdscr)
                    return

        except curses.error:
            pass

def localization(stdscr):
    create_window(stdscr)
    stdscr.timeout(100)
    stdscr.addstr(2, 2, "Krok 3 - uruchamianie localization, q to quit")
    subprocess.Popen(["roslaunch", "sirius_navigation", "localization.launch"],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL
                    )
    while True:
        try:
            key = curses.getkey().lower()

            if key == 'q':
                return
            elif key == 'm':
                mapping(stdscr)
                return

        except curses.error:
            pass

#odrive?
def mapping(stdscr):
    create_window(stdscr)
    stdscr.timeout(100)
    stdscr.addstr(2, 2, "Krok 4 - uruchamianie mapping, q to quit")
    subprocess.Popen(["roslaunch", "sirius_mapping", "sirius_mapping.launch"],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL
                    )
    while True:
        try:
            key = curses.getkey().lower()

            if key == 'q':
                return
            elif key == 'n':
                navigation(stdscr)
                return

        except curses.error:
            pass


def navigation(stdscr):
    create_window(stdscr)
    stdscr.timeout(100)
    stdscr.addstr(2, 2, "Krok 5 - uruchamianie naviagtion, q to quit")
    subprocess.Popen(["roslaunch", "sirius_navigation", "navigation.launch"],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL
                    )
    while True:
        try:
            key = curses.getkey().lower()

            if key == 'q':
                return

        except curses.error:
            pass


    # def main(stdscr):
    #     create_window(stdscr)
    #     stdscr.addstr(1, 2, "autonomy startup, press g")
    #     key = curses.getkey().lower()
    #     # match key:
    #     #     case 'g':
    #     #         return gps(stdscr)
    #     if key == 'g':
    #         gps(stdscr)
    #     if key == 's':
    #         slam(stdscr)
    #     if key == 'l':
    #       localization(stdscr)
    #     if key == 'm':
    #       mapping(stdscr)
    #     if key == 'n':
    #       navigation(stdscr)
    #     if key == 'q':
    #         return


    # if __name__ == '__main__':
    #     pass