#!/usr/bin/env python3
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests

# Constants
BASE_URL = "http://202.117.24.3:8088"
AREAS = ["xingqing2floor", "xingqing3floor", "xingqing4floor"]

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s][%(asctime)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def fetch_api(endpoint: str, params: Dict) -> Optional[Dict]:
    try:
        response = requests.get(
            BASE_URL + endpoint,
            params=params,
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"API request failed {endpoint}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return None

class LibraryDataManager:

    def __init__(self, base_url: str, areas: List[str], cache_live_days: int = 15, cache_file_path: str = 'cache.json'):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.base_url = base_url
        self.areas = areas
        self.cache_file = cache_file_path
        self.cache_live_days = cache_live_days

        self.area_space_map: Dict[str, List[str]] = {}
        self.space_seat_map: Dict[str, List[str]] = {}

        self.load_cache()

    def load_cache(self) -> None:
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                cache_date = datetime.fromisoformat(data.get('date')).date()
                current_date = datetime.now().date()
                days_diff = (current_date - cache_date).days

                if days_diff < self.cache_live_days:
                    self.area_space_map = data['area_space']
                    self.space_seat_map = data['space_seat']
                    self.logger.info(f"Loaded valid cache data (age: {days_diff} days)")
                    return
                else:
                    self.logger.info(f"Cache is {days_diff} days old, refreshing...")
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Cache load failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected cache error: {str(e)}")
        self.refresh_data()

    def refresh_data(self) -> None:
        self.logger.info("Refreshing mapping data from server")
        self._fetch_areas_spaces()
        self._fetch_spaces_seats()
        self._save_cache()

    def _fetch_areas_spaces(self) -> None:
        self.area_space_map.clear()
        for area in self.areas:
            if spaces := self._get_spaces(area):
                self.area_space_map[area] = spaces
                self.logger.debug(f"Fetched {len(spaces)} spaces for area {area}")

    def _fetch_spaces_seats(self) -> None:
        self.space_seat_map.clear()
        for space in sum(self.area_space_map.values(), []):
            if seats := self._get_seats(space):
                self.space_seat_map[space] = seats
                self.logger.debug(f"Fetched {len(seats)} seats for space {space}")

    def _save_cache(self) -> None:
        data = {
            'date': datetime.now().date().isoformat(),
            'area_space': self.area_space_map,
            'space_seat': self.space_seat_map
        }
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(data, f)
            self.logger.info("Cache saved successfully")
        except IOError as e:
            self.logger.error(f"Failed to save cache: {str(e)}")

    def _get_spaces(self, area: str) -> List[str]:
        data = fetch_api("/qseatui", {"sp": area})
        return [k for k in (data or {}) if k not in ("", "spacecancel")]

    def _get_seats(self, space: str) -> List[str]:
        data = fetch_api("/qseatuist", {"sp": space})
        return [k for k in (data or {}) if k not in ("", "cancel")]

    def get_area_for_space(self, space: str) -> Optional[str]:
        for area, spaces in self.area_space_map.items():
            if space in spaces:
                return area
        self.logger.warning(f"Space {space} not found in any area")
        return None

    def get_space_for_seat(self, seat: str) -> Optional[str]:
        for space, seats in self.space_seat_map.items():
            if seat in seats:
                return space
        self.logger.warning(f"Seat {seat} not found in any space")
        return None


class SeatBookingSystem:

    # A map of user status codes to their descriptions
    USER_STATUS_MAP = {
        -2: "Cannot successfully read the card",
        1: "Already ",
        2: "No reservation",
    }

    # A map of seat status codes to their descriptions
    SEAT_STATUS_MAP = {
        0: "This seat is reserved",         # 预约座位
        1: "This seat is in use",           # 在用座位
        2: "This seat is available",        # 可用座位
        3: "This seat is temporarily away"  # 中途离馆
    }

    AVALID_SEAT_STATUS = 2


    def __init__(self, base_url: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.base_url = base_url
        if self.initialize() is False:
            self.logger.error("Failed to initialize SeatBookingSystem")
            sys.exit(1)


    def initialize(self) -> bool:
        try:
            response = requests.get(self.base_url + "/seatuieast/#", timeout=5)
            response.raise_for_status()
            if "西安交通大学图书馆图书预约系统" in response.text:
                self.logger.info("System initialized successfully")
                return True
            self.logger.error("Unexpected landing page content")
            return False
        except requests.RequestException as e:
            self.logger.error("Initialization request failed: %s", str(e))
        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            return False

    def get_user_status(self, cardno: str) -> Tuple[Optional[int], Optional[str]]:
        data = fetch_api("/quserinfo", {"cardno": cardno})
        if data:
            status = int(data.get('status'))
            message = data.get('message')
            return status, message
        else:
            self.logger.error(f"Failed to fetch user status for cardno {cardno}")
            return None, None

    def get_space_status(self, space: str) -> Optional[List[Dict[str, int]]]:
        data = fetch_api("/qseatuist", {"sp": space})
        if data:
            seat_list = []
            for key, value in data.items():
                if key == "" or key == "cancel":
                    continue
                seat_list.append({key: int(value[4])})
            self.logger.info(f"Fetched {len(seat_list)} seats for space {space}")
            return seat_list
        else:
            self.logger.error(f"Failed to fetch space status for space {space}")
            return None

    def get_seat_status(self, seat_id: str, space: str) -> Tuple[Optional[int], Optional[str]]:
        SEAT_STATUS_INDEX = 4
        data = fetch_api("/qseatuist", {"sp": space})
        if data:
            seat_data = data.get(seat_id)
            if seat_data:
                seat_status = int(seat_data[SEAT_STATUS_INDEX])
                seat_message = self.SEAT_STATUS_MAP.get(seat_status, ["", ""])
                return seat_status, seat_message
            else:
                self.logger.warning(f"Seat {seat_id} not found in space {space}")
                return None, None
        else:
            self.logger.error(f"Failed to fetch seat status for seat {seat_id} in space {space}")
            return None, None


    def book_seat(self, cardno: str, seat_id: str, space: str) -> int:
        # return 0: reservation failed
        # return 1: reservation success
        # return 2: already reserved
        # return -1: runtime error
        """Reserve a seat for a user.

        Args:
            cardno:lib user card number
            seat_id: Seat ID
            space: Space name

        Returns:
            0: reservation failed
            1: reservation success
            2: already reserved
           -1: runtime error
        """

        # check if the cardno is already reserved the seat
        user_status, user_message = self.get_user_status(cardno)
        if user_status == 1 and seat_id in user_message:
            self.logger.warning(f"User already has reservation for seat {seat_id}")
            return 2
        
        seat_status, seat_message = self.get_seat_status(seat_id, space)
        if seat_status is None:
            return -1
        if seat_status != self.AVALID_SEAT_STATUS:
            self.logger.warning(f"Seat {seat_id} is not available for booking because {seat_message}")
            return 0
        
        # Proceed to book the seat
        try:
            response = requests.post(
                self.base_url + "/seatuieast/#",
                data={"No": cardno, "kid": seat_id, "sp": space},
                timeout=5
            )
            response.raise_for_status()
            
            if "成功" in response.text:
                self.logger.info(f"Seat {seat_id} booked successfully")
                return 1
            # # Following status should already be handled in check_seat_status
            #
            # if "已被预约" in response.text:
            #     self.logger.warning(f"Seat {seat_id} already occupied")
            #     return 0
            self.logger.error(f"Unexpected booking response: {response.text}")
            return 0
        except requests.RequestException as e:
            self.logger.error(f"Booking request failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"Booking unexpected failed: {str(e)}")
        return -1


def reserve_seat(cardno: str, seat_id: str) -> bool:

    data_manager = LibraryDataManager(BASE_URL, AREAS)
    booking_system = SeatBookingSystem(BASE_URL)

    if not (space := data_manager.get_space_for_seat(seat_id)):
        return -1

    result = booking_system.book_seat(cardno, seat_id, space)
    if result == 1:
        print(f"Seat {seat_id} booked successfully for cardno {cardno}")
    elif result == 2:
        print(f"User already has reservation for seat {seat_id}")
    elif result == 0:
        print(f"Failed to book seat {seat_id} for cardno {cardno}")
    else:
        print(f"Unexpected error occurred while booking seat {seat_id} for cardno {cardno}")
    if result != 1:
        sys.exit(1)

def only_check_user_status(cardno: str):
    booking_system = SeatBookingSystem(BASE_URL)
    status, message = booking_system.get_user_status(cardno)
    if status is not None:
        print(f"User status for cardno {cardno}: {SeatBookingSystem.USER_STATUS_MAP.get(status, 'Unknown')}")
        if message:
            print(f"Message: {message}")
    else:
        print(f"Failed to fetch user status for cardno {cardno}")
        sys.exit(1)

def only_check_seat_status(seat_id: str):
    data_manager = LibraryDataManager(BASE_URL, AREAS)
    booking_system = SeatBookingSystem(BASE_URL)

    if not (space := data_manager.get_space_for_seat(seat_id)):
        print(f"Seat {seat_id} not found in any space")
        return

    seat_status, seat_message = booking_system.get_seat_status(seat_id, space)
    if seat_status is not None:
        print(f"Seat status for {seat_id}: {SeatBookingSystem.SEAT_STATUS_MAP.get(seat_status, 'Unknown')}")
        if seat_message:
            print(f"Message: {seat_message}")
    else:
        print(f"Failed to fetch seat status for seat {seat_id}")
        sys.exit(1)

def find_all_available_seats(space: str):
    data_manager = LibraryDataManager(BASE_URL, AREAS)
    booking_system = SeatBookingSystem(BASE_URL)

    if not (area := data_manager.get_area_for_space(space)):
        print(f"Space {space} not found in any area")
        return
    seat_list = booking_system.get_space_status(space)
    available_seat_list = []
    if seat_list:
        print(f"Available seats in {space}:")
        for seat in seat_list:
            for seat_id, status in seat.items():
                if status == SeatBookingSystem.AVALID_SEAT_STATUS:
                    available_seat_list.append(seat_id)
    else:
        print(f"No available seats found in space {space}")
        sys.exit(1)

    # The seat number is a string in the format "[A-Z]?\d+"
    # First sort by letter, then by number, if no letter exists, consider it less than A
    available_seat_list.sort(key=lambda x: (x[0], int(x[1:])) if x else (None, 0))

    for i in range(0, len(available_seat_list), 10):
        print(" ".join(available_seat_list[i:i + 10]))
    print(f"Total available seats in {space}: {len(available_seat_list)}")


def list_space(area: str):
    data_manager = LibraryDataManager(BASE_URL, AREAS)
    if area not in data_manager.area_space_map:
        print(f"Area {area} not found")
        return
    spaces = data_manager.area_space_map[area]
    print(f"Spaces in {area}:")
    for space in spaces:
        print(" - " + space)

def list_all_spaces():
    # data_manager = LibraryDataManager(BASE_URL, AREAS)
    # all_spaces = sum(data_manager.area_space_map.values(), [])
    # print("All spaces:")
    # for space in all_spaces:
    #     print(" - " + space)
    for area in AREAS:
        list_space(area)

def refresh_cache():
    data_manager = LibraryDataManager(BASE_URL, AREAS)
    data_manager.refresh_data()
    print("Cache refreshed successfully")


if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser(description="Library Seat Booking System")
    parser.add_argument('--log', default='INFO', help='Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)', type=str)

    subparsers = parser.add_subparsers(dest="command")
    
    # "book" Command
    book_parser = subparsers.add_parser('book', help='Reserve a seat')
    book_parser.add_argument('cardno', help='User card number')
    book_parser.add_argument('seat_id', help='Seat ID to book')
    
    # "seat" Command
    seat_parser = subparsers.add_parser('seat', help='Check seat status')
    seat_parser.add_argument('seat_id', help='Seat ID to check')
    
    # "user" Command
    user_parser = subparsers.add_parser('user', help='Check user status')
    user_parser.add_argument('cardno', help='User card number')
    
    # "space" Command
    space_parser = subparsers.add_parser('space', help='Find available seats in a space')
    space_parser.add_argument('space', help='Space identifier')

    # "list" Command
    list_parser = subparsers.add_parser('list', help='List spaces in an area')
    list_parser.add_argument('area', help='Area identifier')

    # "listall" Command
    subparsers.add_parser('listall', help='List all spaces')
    
    # "refresh" Command
    subparsers.add_parser('refresh', help='Refresh cache')
    
    # "help" Command already handled by argparse

    # Parse arguments

    args = parser.parse_args()

    # Set logging level
    log_level = getattr(logging, args.log.upper(), logging.INFO)
    if not isinstance(log_level, int):
        parser.error(f"Invalid log level: {args.log}")
        sys.exit(1)
    logging.getLogger().setLevel(log_level)
    
    if args.command == 'book':
        reserve_seat(args.cardno, args.seat_id)
    elif args.command == 'seat':
        only_check_seat_status(args.seat_id)
    elif args.command == 'user':
        only_check_user_status(args.cardno)
    elif args.command == 'space':
        find_all_available_seats(args.space)
    elif args.command == 'refresh':
        refresh_cache()
    elif args.command == 'list':
        list_space(args.area)
    elif args.command == 'listall':
        list_all_spaces()
    elif args.command == 'help':
        parser.print_help()
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)        
