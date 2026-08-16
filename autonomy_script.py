import curses
import subprocess
import rospy
from pick import Option, pick
from sensor_msgs.msg import NavSatFix
from nav_msgs.msg import Odometry
import math

actual_covariance = [999.0]
actual_position = [0.0, 0.0, 0.0]
covariance_status = "none"
gps_ready = False

def gps_callback(msg):
    if len(msg.position_covariance) > 0:
        actual_covariance[0] = msg.position_covariance[0]

        actual_position[0] = msg.latitude
        actual_position[1] = msg.longitude
        actual_position[2] = msg.altitude

def gps():
    subprocess.Popen(["roslaunch", "sirius_navigation", "gnss.launch"],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL
    )
    gps_sub = rospy.Subscriber('gps/fix', NavSatFix, gps_callback)

    global covariance_status, gps_ready
    covariance_status = "waiting for data"
    gps_ready = False




last_pos = [None, None]
driven_distance = [0.0]

def odometry_callback(msg, stdscr):
    current_x = msg.pose.pose.position.x
    current_y = msg.pose.pose.position.y

    if last_pos[0] == None:
        last_pos[0] = current_x
        last_pos[1] = current_y
    else:
        dx = current_x - last_pos[0]
        dy = current_y - last_pos[1]

        vector = math.sqrt(dx**2 + dy**2)
        driven_distance[0] += vector

        last_pos[0] = current_x
        last_pos[1] = current_y


def slam(stdscr):
    stdscr.timeout(100)
    create_window(stdscr)
    stdscr.addstr(2, 2, "Step 2 - slam startup, q to quit")
    slam_launched = False

    while True:

        if not slam_launched:
            create_window(stdscr)
            stdscr.addstr(4, 2, "choose a reference point:")
            stdscr.addstr(5, 4, " 1 - current position")
            stdscr.addstr(6, 4, "2 - saved position")

        elif slam_launched:
            if driven_distance[0] >= 40.0:
                stdscr.addstr(14, 2, "drived 40m, press l")
                stdscr.refresh()


        try:
            key = stdscr.getkey().lower()

            if key == 'q':
                return #wyjscie
            
            if not slam_launched:
                # pkt referencyjny == gps
                if key == '1':
                    create_window(stdscr)
                    rospy.set_param('NAZWA_PARAMETRU_PKT', actual_position)
                    stdscr.addstr(10, 2, "go shake the rover, then drive for 40m")
                    stdscr.addstr(12, 2, "next press l -> localization")
                    subprocess.Popen(["roslaunch", "sirius_spectacularai", "slam.launch"],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL
                        )
                    odom_sub = rospy.Subscriber('slam/global_odometry', Odometry, odometry_callback, callback_args=stdscr)
                    slam_launched = True

                # pkt referencyjny == wybierasz
                elif key == '2':
                    create_window(stdscr)
                    points = ["p1", "p2"]
                    title = "pick a referenece point"
                    stdscr.timeout(-1)
                    curses.endwin() #???
                    chosen_point, index = pick(points, title)
                    stdscr.clear()
                    stdscr.refresh()
                    try:
                        coordinates = rospy.get_param(chosen_point)
                        rospy.set_param("nazsa paramwetu pkt", coordinates)
                        stdscr.timeout(100)
                        stdscr.addstr(12, 2, "go shake the rover, then drive for 40m")
                        stdscr.addstr(14, 2, "next press l -> localization")
                        subprocess.Popen(["roslaunch", "sirius_spectacularai", "slam.launch"],
                                                                stdout=subprocess.DEVNULL,
                                                                stderr=subprocess.DEVNULL
                                        )
                        odom_sub = rospy.Subscriber('slam/global_odometry', Odometry, odometry_callback, callback_args=stdscr)
                        slam_launched = True
                    except KeyError:
                        stdscr.addstr(14, 2, "chosen point doesn't exist" )

            else:
                if key == 'l' and driven_distance[0] >= 40.0:
                    odom_sub.unregister()
                    return 'l'

        except curses.error:
            pass

def localization(stdscr):
    create_window(stdscr)
    stdscr.timeout(100)
    stdscr.addstr(2, 2, "Step 3 - localization startup, q to quit")
    subprocess.Popen(["roslaunch", "sirius_navigation", "localization.launch"],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL
                    )
    while True:
        try:
            key = stdscr.getkey().lower()

            if key == 'q':
                return
            elif key == 'm':
                return 'm'

        except curses.error:
            pass

def mapping(stdscr):
    create_window(stdscr)
    stdscr.timeout(100)
    stdscr.addstr(2, 2, "Step 4 - mapping startup, q to quit")
    subprocess.Popen(["roslaunch", "sirius_mapping", "sirius_mapping.launch"],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL
                    )
    while True:
        try:
            key = stdscr.getkey().lower()

            if key == 'q':
                return
            elif key == 'n':
                return 'n'

        except curses.error:
            pass

def navigation(stdscr):
    create_window(stdscr)
    stdscr.timeout(100)
    stdscr.addstr(2, 2, "Krok 5 - naviagtion startup, q to quit")
    subprocess.Popen(["roslaunch", "sirius_navigation", "navigation.launch"],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL
                    )
    while True:
        try:
            key = stdscr.getkey().lower()

            if key == 'q':
                return

        except curses.error:
            pass

def main(stdscr):

    #wsteone ustawienie
    global covariance_status, actual_covariance, gps_ready, gps_sub
    curses.curs_set(0) #niema myszkiiii
    stdscr.timeout(100) #10razy na sek petla

    #kroki
    options = [
        "1. GPS startup",
        "2. SLAM",
        "3. localization",
        "4. mapping",
        "5. navigation",
        "4. quit programm"
    ]
    aktualny_wiersz = 0

    #statusy odpalenia
    status_gps = "[ none ]"
    status_slam = "[ none ]"

    #petla dzialania funkcji i rysowania ekranu
    while True:
        stdscr.clear()

        #1 GPS 
        if gps_sub is not None and not gps_ready:
            if actual_covariance[0] != 999.0: 
                if actual_covariance[0] <= 0.002:
                    gps_ready = True
                    gps_sub.unregister()
                    covariance_status = "ready"
                else:
                    covariance_status = f"{round(actual_covariance[0], 4)}"

        #RYSOWANIE CHECKLISTY
        stdscr.addstr(1, 2, "AUTONOMY STARTUP", curses.A_BOLD)
        stdscr.addstr(3, 2, f"status gps = [{covariance_status}]")
        stdscr.addstr(4, 2, "status slam = []")
        stdscr.addstr(5, 2, "status localization = []")
        stdscr.addstr(6, 2, "status mapping = []")
        stdscr.addstr(7, 2, "status navigation = []")
        stdscr.addstr(8, 2, "-" * 40)
        
        #menu do odpalania funkcji
        stdscr.addstr(10, 2, "functions:", curses.A_BOLD)
        for index, option_txt in enumerate(options):
            x = 4
            y = 12 + index
            
            if index == aktualny_wiersz:
                #podswietlenie
                stdscr.addstr(y, x, f"> {option_txt} <", curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, f"  {option_txt}  ")

        stdscr.refresh()

        #obsluga klawiszy
        klawisz = stdscr.getch()

        if klawisz == curses.KEY_UP and aktualny_wiersz > 0:
            aktualny_wiersz -= 1
        elif klawisz == curses.KEY_DOWN and aktualny_wiersz < len(options) - 1:
            aktualny_wiersz += 1
        elif klawisz in [curses.KEY_ENTER, 10, 13]: # Enter
            
            #logiki dla wierszy
            if aktualny_wiersz == 0:
                gps()
            elif aktualny_wiersz == 1:
                slam()
            elif aktualny_wiersz == 2:
                localization(stdscr)
                status_slam = "[ active ]"
            elif aktualny_wiersz == 3:
                mapping(stdscr)
                status_slam = "[ active ]"
            elif aktualny_wiersz == 4:
                status_nav = "[active]"
                navigation(stdscr)
            elif aktualny_wiersz == 5:
                break

if __name__ == '__main__':
    curses.wrapper(main)
