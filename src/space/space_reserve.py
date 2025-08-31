import time
import requests
import re
from urllib.parse import parse_qs, urlparse, unquote


def gen_timestamp() -> str:
    """
    Generate a timestamp that looks like a real user visit
    Args:
        None
    Returns:
        str: A timestamp string in milliseconds
    """
    return str(int(time.time() * 1000))


def parse_space_info(space_name: str, html_content: str):
    """
    Parse space information from HTML content
    Args:
        space_name: Name of the space to find (e.g., "iLibrary小研修间")
        html_content: HTML content to parse
    Returns:
        tuple: (url, payload_dict) or (None, None) if not found
    """
    # Find the li element with the matching span text
    pattern = rf'<li[^>]*url="([^"]*)"[^>]*>.*?<span>{re.escape(space_name)}</span>'
    match = re.search(pattern, html_content, re.DOTALL)

    if not match:
        return None, None

    url = match.group(1)
    # Parse URL to extract parameters
    parsed_url = urlparse(url)
    params = parse_qs(parsed_url.query)

    # Convert params to payload dict (flatten single-item lists)
    payload = {}
    for key, values in params.items():
        if values:
            # URL decode the value
            payload[key] = unquote(values[0])

    # Build the full URL path
    full_url = f"http://space.lib.xjtu.edu.cn/ClientWeb/xcus{url}"

    return full_url, payload


def find_room_by_title(title: str, rooms_data: list):
    """
    Find room information by title from the rooms data
    Args:
        title: Room title to search for (e.g., "东南一研修间")
        rooms_data: List of room data from the API response
    Returns:
        dict: Room information dict or None if not found
    """
    for room in rooms_data:
        if room.get("title") == title:
            return room
    return None


def check_available(title: str, rooms_data: list, start_time: str, end_time: str) -> bool:
    """
    Check if a room is available for reservation
    Args:
        title: Room title to check (e.g., "东南一研修间")
        rooms_data: List of room data from the API response
        start_time: Reservation start time
        end_time: Reservation end time
    Returns:
        bool: True if the room is available, False otherwise
    """
    room = find_room_by_title(title, rooms_data)
    if not room:
        return False

    # Check the room's availability
    for reservation in room.get("ts", []):
        """
        ts": [
                {
                    "id": null,
                    "start": "2025-08-31 18:30",
                    "end": "2025-08-31 20:30",
                    "state": "undo",
                    "date": null,
                    "name": null,
                    "title": "张益嘉,小组讨论",
                    "owner": "张益嘉",
                    "accno": "101788453",
                    "member": "",
                    "limit": null,
                    "occupy": false
                }
            ],
        """
        this_start_time = reservation.get("start", "")
        this_end_time = reservation.get("end", "")
        
        # Extract time part safely and convert to HHMM format for comparison
        if len(this_start_time) >= 16:  # "2025-08-31 18:30" format
            this_start_time = this_start_time[11:16].replace(":", "")  # "18:30" -> "1830"
        else:
            continue  # Skip invalid time format
            
        if len(this_end_time) >= 16:  # "2025-08-31 20:30" format
            this_end_time = this_end_time[11:16].replace(":", "")    # "20:30" -> "2030"
        else:
            continue  # Skip invalid time format
        
        # Check for time overlap: if our time overlaps with existing reservation, room is not available
        # Two time periods overlap if: start1 < end2 AND start2 < end1
        if start_time < this_end_time and this_start_time < end_time:
            return False

    return True

def space_reserve(
    my_session: requests.Session,
    userId: str,
    password: str,
    spacename: str,
    date: str,
    startTime: str,
    endTime: str,
):
    entry_url = "http://space.lib.xjtu.edu.cn/"

    # step 1
    entry_page = my_session.get(entry_url, allow_redirects=True)

    # step 2 (maybe useless)
    get_language_url = "http://space.lib.xjtu.edu.cn/ClientWeb/pro/ajax/util.aspx"
    _ = my_session.get(
        get_language_url,
        params={"act": "get_language", "_": gen_timestamp()},
        allow_redirects=True,
    )

    # step 3
    main_url = "http://space.lib.xjtu.edu.cn/ClientWeb/xcus/ic2/index.aspx"
    _ = my_session.get(
        main_url, params={"_": gen_timestamp()}, allow_redirects=True,
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    # Parse space information dynamically
    # TODO
    # space_url, space_payload = parse_space_info("iLibrary小研修间", entry_page.text)
    # print(space_payload)

    space_url = "http://space.lib.xjtu.edu.cn/ClientWeb/xcus/a/dftdetail.aspx"
    space_payload = {
        "mode": "2",
        "classKind": "1",
        "id": "100462940",
        "name": "iLibrary小研修间"
    }
    _ = my_session.post(
        space_url,
        data=space_payload,
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    # step 4
    # params = dev_order=&kind_order=&classkind=1&display=cld&md=d&kind_id=100462940&purpose=&cld_name=default&date=20250819&act=get_rsv_sta&_=1755534572408
    get_reverse_time_url = "http://space.lib.xjtu.edu.cn/ClientWeb/pro/ajax/device.aspx"
    get_reverse_time_page = my_session.get(
        get_reverse_time_url,
        params={
            "dev_order": "",
            "kind_order": "",
            "classkind": "1",
            "display": "cld",
            "md": "d",
            "kind_id": space_payload["id"],
            "purpose": "",
            "cld_name": "default",
            "date": date,
            "act": "get_rsv_sta",
            "_": gen_timestamp(),
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    # Parse room information from response
    rooms_data = get_reverse_time_page.json().get("data", [])

    # Find the specific room
    target_room = find_room_by_title(spacename, rooms_data)
    if not target_room:
        print("未找到指定房间")
        return 1

    avaliable_flag = check_available(spacename, rooms_data, startTime, endTime)
    if not avaliable_flag:
        print("房间在指定时间内不可用")
        return 1

    # step 5
    login_url = "http://space.lib.xjtu.edu.cn/ClientWeb/pro/ajax/login.aspx"
    _ = my_session.post(
        login_url,
        data={
            "id": userId,
            "pwd": password,
            "act": "login"
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    # step 6
    search_account_url = "http://space.lib.xjtu.edu.cn/ClientWeb/pro/ajax/data/searchAccount.aspx"
    _ = my_session.get(
        search_account_url,
        params={
            "type": "",
            "term": userId,
            "_": gen_timestamp()
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    # step 7
    reverse_url = "http://space.lib.xjtu.edu.cn/ClientWeb/pro/ajax/reserve.aspx"
    _start = date[0:4] + "-" + date[4:6] + "-" + date[6:8] + " " + startTime[0:2] + ":" + startTime[2:4]
    _end = date[0:4] + "-" + date[4:6] + "-" + date[6:8] + " " + endTime[0:2] + ":" + endTime[2:4]
    reverse_page = my_session.get(
        reverse_url,
        params={
            "dev_id": target_room["devId"],
            "lab_id": target_room["labId"],
            "kind_id": target_room["kindId"],
            "room_id": "",
            "type": "dev",
            "prop": "",
            "test_id": "",
            "term": "",
            "test_name": "参与线上组会",
            "min_user": str(target_room["minUser"]),
            "max_user": str(target_room["maxUser"]),
            "mb_list": userId,
            "start": _start,
            "end": _end,
            "start_time": startTime,
            "end_time": endTime,
            "up_file": "",
            "memo": "需要参与线上的组会，组会过程中需要发言",
            "act": "set_resv",
            "_": gen_timestamp()
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    # step 8
    # check if reverse_page is {ret: 1, act: "set_resv", msg: "操作成功！", data: null, ext: null}
    if reverse_page.json() == {"ret": 1, "act": "set_resv", "msg": "操作成功！", "data": None, "ext": None}:
        return 0
    else:
        return 1


if __name__ == "__main__":
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    })

    # Example usage
    date = input("Enter the date (YYYYMMDD): ")
    startTime = input("Enter the start time (HHMM): ")
    endTime = input("Enter the end time (HHMM): ")
    userId = input("Enter your user ID: ")
    password = input("Enter your password: ")
    space = input("Enter the space name: ")

    # space = (1 .. 4) --> spacename
    # 1 -- > "东南一研修间"
    # 2 -- > "东南二研修间"
    # 3 -- > "西南一研修间"
    # 4 -- > "西南二研修间"
    space_name_map = {
        "1": "东南一研修间",
        "2": "东南二研修间",
        "3": "西南一研修间",
        "4": "西南二研修间"
    }

    ret = space_reserve(
        my_session=session,
        spacename=space_name_map[space],
        date=date,
        startTime=startTime,
        endTime=endTime,
        userId=userId,
        password=password
    )

    if ret == 0:
        exit(0)
    else:
        exit(1)