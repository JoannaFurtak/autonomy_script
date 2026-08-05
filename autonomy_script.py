import curses
import subprocess
import rospy
from sensor_msgs.msg import NavSatFix
from nav_msgs.msg import Odometry
import math

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
                return 's'
            elif key == 'q':
                return
        except curses.error:
            pass

#tutaj musze:
#miec nowy slam, zeby pkt referencyjny byl parametrem
#odsluchy z odometry aby wiedziec jak daleko jest lazik
# warunek ze dopoki nie przejedzie sie 40m to 
# zebym nie mogla kliknac l

last_pos = [None, None]
driven_distance = [0.0]

def odometry_callback(msg, stdscr):
    current_x = msg.pose.pose.position.x
    current_y = msg.pose.pose.position.y

    if last_pos == None:
        last_pos[0] = current_x
        last_pos[1] = current_y
    else:
        dx = current_x - last_pos[0]
        dy = current_y - last_pos[1]

        vector = math.sqrt(dx**2 + dy**2)
        driven_distance[0] += vector

        last_pos[0] = current_x
        last_pos[1] = current_y

        if driven_distance[0] >= 40.0:
            stdscr.addstr(14, 2, "kliklin l")


def slam(stdscr):
    stdscr.timeout(100)
    create_window(stdscr)
    stdscr.addstr(2, 2, "Krok 2 - uruchamianie slama, q to quit")
    slam_launched = False

    while True:

        if not slam_launched:
            create_window(stdscr)
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
                    create_window(stdscr)
                    rospy.set_param('NAZWA_PARAMETRU_PKT', actual_position)
                    stdscr.addstr(10, 2, "idz bujaj lazikiem, nastepnie przejedz nim 40m ")
                    stdscr.addstr(12, 2, "a potem wcisnij l -> localization")
                    subprocess.Popen(["roslaunch", "sirius_spectacularai", "slam.launch"],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL
                        )
                    odom_sub = rospy.Subscriber('slam/global_odometry', Odometry, odometry_callback)
                    slam_launched = True

                # pkt referencyjny == wybierasz
                elif key == '2':
                    create_window(stdscr)
                    stdscr.timeout(-1)
                    curses.echo()
                    stdscr.addstr(10, 2, "wpisz nazwe pkt referencyjnego: ")
                    default = stdscr.getstr(10, 35).decode('utf-8')
                    rospy.set_param('NAZWA_PARAMETRU_PKT', default)
                    curses.noecho()
                    stdscr.timeout(100)
                    stdscr.addstr(12, 2, "idz bujaj lazikiem, nastepnie przejedz nim 40m")
                    stdscr.addstr(14, 2, "a potem wcisnij l -> localization")
                    subprocess.Popen(["roslaunch", "sirius_spectacularai", "slam.launch"],
                                                            stdout=subprocess.DEVNULL,
                                                            stderr=subprocess.DEVNULL
                                    )
                    odom_sub = rospy.Subscriber('slam/global_odometry', Odometry, odometry_callback)
                    slam_launched = True

            else:
                if key == 'l':
                    odom_sub.unregister()
                    return 'l'

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
                return 'm'

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
                return 'n'

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

def main(stdscr):
    create_window(stdscr)
    stdscr.timeout(100)
    state = None

    while True:
        if state == None:
            try:
                state = stdscr.getkey().lower()
            except curses.error:
                continue
        try:
            match state:
                case 'g':
                    state = gps(stdscr)
                case 's':
                    state = slam(stdscr)
                case 'l':
                    state = localization(stdscr)
                case 'm':
                    state = mapping(stdscr)
                case 'n':
                    state = navigation(stdscr)
                case 'q':
                    return
                case _:
                    state = None
        except curses.error:
            pass
                

if __name__ == '__main__':
    curses.wrapper(main)
